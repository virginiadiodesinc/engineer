from datetime import datetime
from sqlalchemy import case, or_, and_
from sqlalchemy.orm import with_polymorphic
import re
import os
import io
import csv
import shutil
import filecmp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from difflib import SequenceMatcher

import pickle

import altair as alt
alt.data_transformers.enable('default',max_rows=None)

from sql import SSP_DB_DATA_DIR
from util.functions import makeif, removeParen, png2url, readFile, removeFile, replaceFile, get_hex_color, getSystemFrequencies, getWorkOrderLinks, calcNoiseMarker, mergeDFs, locFloatIndex, DFs2longDF, getLastParen
from util.data.specs import SPEC_DICT, BAND_SETTINGS
from util.data.taper_scaling import TAPER_DB_SCALING
from util.data.spec_traces import spec_trace_df_dict
from util.data.plot_format import plot_format_df_dict
from util.data.spec_color_span import SPEC_COLOR_THRESHOLDS
from .database import Base
from .models import System, Testset, Test, test_type_dict
from . import BANDS, SYSTEMS, ORDERS

#Used to replace compact terms (IM_CL) into descriptive terms (Intrinsic Mixer Conversion Loss)
replacements = {'None':'','_spec':'', '_freq':' Frequency (GHz)', '_':' ', 'HD':'High Drive', 'LD':'Low Drive',
				'IM':'Intrinsic Mixer', 'EXT':'Extended', 'MAG':'Magnitude', 'PHA':'Phase',
				'CL':'Conversion Loss (dB)', 'TPP':'Test Port Power (dBm)', 'WQ':'Wave Quantities (dB)',
				'DR': 'Dynamic Range (dB)', 'SB':'Stability', 'IS':'Input Saturation', 'PL':'Power Levelability', 'GS':'Gold Standards',
				'UCA': 'User Controlled Attenuation', 'DANL': 'Displayed Average Noise Level', 'PXA': 'PXA Sweep', 'IF_BW': 'IF Bandwidth',
				'PLHRM':'Powerleveling Harmonics', 'PLH':'Powerleveling Harmonics', 'HRM':'Harmonics (dBc)', 'Enh12':'Enhanced Response 1>2', 'Enh21':'Enhanced Response 2>1',
				'CS': 'Current Sweep', 'YFAC': 'Y-Factor', 'PS': 'Power Sweep', 'CRT': 'Current Reliability', 'PRT': 'Power Reliability',
				'DCO': 'DC Oscillations', 'SBO': 'Sideband Oscillations', 'NTEMP': 'Noise Temperature', 'GAIN': 'Gain'}

gs_replacements = {'xth':'Thru','xqs':'Quarter shim Thru','st-st':'Shorts','qm-ro':'Quarter-milled Short - Radiating Open',
					'ro-qm':'Radiating Open - Quarter milled Short','pl-pl':'Precision Loads','ro-ro':'Radiating Opens',
					'xswg1':'1" SWG Thru','xj10':'J10 Thru','swg1-ro':'1" SWG Short - Radiating Open','ro-swg1':'Radiating Open - 1" SWG Short','xcut1':'1" Cutoff Waveguide'}

spec_colors = {'minimum':'green', 'min_typ':'#FCD12A', 'typical':'#FCD12A', 'max_typ':'#FCD12A', 'maximum':'red'}
spec_shorts = {'minimum':'min', 'min_typ':'typ', 'max_typ':'typ', 'maximum':'max'}

# letter and other designations for ACL file bands
acl_band_designations = {"WR0.65": {"Letter": None, "Multiplier": 0, "USER": True},
						"WR1.0": {"Letter": None, "Multiplier": 0, "USER": True},
						"WR1.5": {"Letter": None, "Multiplier": 54, "USER": True},
						"WR2.2": {"Letter": None, "Multiplier": 36, "USER": True},
						"WR3.4": {"Letter": "J", "Multiplier": 24, "USER": True},
						"WR4.3": {"Letter": "Y", "Multiplier": 18, "USER": False},
						"WR5.1": {"Letter": "G", "Multiplier": 18, "USER": True},
						"WR6.5": {"Letter": "D", "Multiplier": 12, "USER": False},
						"WR8.0": {"Letter": "F", "Multiplier": 9, "USER": True},
						"WR10": {"Letter": "W", "Multiplier": 9, "USER": True},
						"WR12": {"Letter": "E", "Multiplier": 6, "USER": False},
						"WR15": {"Letter": "V", "Multiplier": 6, "USER": False},
						"WR19": {"Letter": "U", "Multiplier": 4, "USER": False},
						"WR22": {"Letter": None, "Multiplier": 0, "USER": True},
						"WR28": {"Letter": None, "Multiplier": 0, "USER": True}}

# Lookup for special multipliers for SpaceX SAX systems
spacex_acl_bands = {'WR19':4,'WR8.0': 8}

# Lookup table for "Gold" Gold Standards data
GS_SNs = {"WR0.65": ('VNAX 2301','VNAX 2302'),
			"WR1.0": ('VNAX 2483','VNAX 2484'),
			"WR1.5": ('VNAX 2745','VNAX 2746'),
			"WR2.2": ('VNAX 2686','VNAX 2687'),
			"WR3.4": ('VNAX 2815','VNAX 2816'),
			"WR4.3": ('VNAX 2669','VNAX 2670'),
			"WR5.1": ('VNAX 2809','VNAX 2810'),
			"WR6.5": ('VNAX 2786','VNAX 2787'),
			"WR8.0": ('VNAX 2831','VNAX 2832'),
			"WR10": ('VNAX 2794','VNAX 2795'),
			"WR12": ('VNAX 2829','VNAX 2830'),
			"WR15": ('VNAX 2796','VNAX 2797'),
			"WR19": ('VNAX 2514','VNAX 2515'),
			"WR22": (None,None),
			"WR28": ('VNAX 2709','VNAX 2710')}

# Dict of GS short names to descriptive names
GS_NAMES = {'xth': 'through', 'st': 'short', 'xqs': 'quarter shim', 'pl': 'precision load', 'ro': 'radiating open', 'swg1': '1" SWG', 'xcut1': '1" cutoff SWG', 'xj10': 'J10 load'}
#qm quarter wave milled
#Default constant for color gradient generation used in spec checking
COLOR_SPAN = 0.5#dB

"""============================   Generic Table Functions    ============================"""
#Returns the next available ID in the table
def newID(table):
	IDs = [row.ID for row in table.all()]
	return min(set(range(0,len(IDs)+1))-set(IDs))

#Adds a system to the DB
def addSystem(db, SN, Band=None, Type=None, Subtype=None, Arch=None, overwrite=False):
	sys = db.get(System, SN)
	if sys == None:
		system = System(SN=SN,Band=Band,Type=Type,Subtype=Subtype,Arch=Arch)
		db.add(system)
		db.commit()
		print(f"System table entry added: {system}")
		return True
	else:
		if overwrite == True:
			sys = db.query(System).filter(System.SN == SN)
			update_dict = {key: val for key, val in {'Band':Band,'Type':Type,'Subtype':Subtype,'Arch':Arch}.items() if val is not None}
			sys.update(update_dict)
			db.commit()
			print('System updated: ',SN)
		elif overwrite == None:
			print(f'Update Ignored: {SN}')
		else:
			
			if sys.getDict() == {'SN':SN,'Band':Band,'Type':Type,'Subtype':Subtype,'Arch':Arch}:	return print('System found: ', sys)
			print('Old:',sys.getDict())
			print('New:',{'SN':SN,'Band':Band,'Type':Type,'Subtype':Subtype,'Arch':Arch})
			raise Warning(f"{sys} already exists. \nWould you like to update details of the system?")

#Changes the sytem type, moving all testset data to its new location
def changeSystemType(db, SN, Type):
	
	# Update the type of the system entry
	system = db.query(System).filter(System.SN == SN)
	if system.count() < 1: return print(f"No such system {SN}")
	
	old_type = system.first().Type
	print(old_type)
	if old_type == Type:	return
	system.update({'Type': Type})
	db.commit()
	
	table = db.query(Testset)
	rows = table.filter_by(SN1 = SN)
	
	# Now update the test file locations in the db and move the files, deleting empty folders behind
	for testset in rows:
		tests = db.query(Test).filter_by(testsetID = testset.ID)
		for test in tests:
			src = test.file
			if old_type in src:
				dest = src.replace(f'/{old_type}/', f'/{Type}/')
				try:
					os.makedirs(os.path.dirname(dest), exist_ok=True)
					shutil.copy2(src, dest)
					os.remove(src)
					src_folder = src[:src.index(f'/{old_type}/')]
					print(src_folder)
					
					test = db.query(Test).filter(Test.testsetID == testset.ID, Test.test_name == test.test_name)
					test.update({'file': dest})
					db.commit()
					print(f"Moved: {src} -> {dest}")
				except Exception as err:
					print(f"Could not move test to new location: {src} -> {dest}", err)

#Testset functions
def addTestset(db, SN1, SN2=None, rev='next', Order=None, Customer=None, Engineer=None, Last_Edit=None, Comments="", Approval=False, overwrite=False, table=None):
	if rev == '':	raise Exception("Blank revision label:")
	
	if table == None:	table = db.query(Testset)
	rows = table.filter_by(SN1 = SN1, SN2 = SN2)
	revs = [row.rev for row in rows]	#List of every revision that exists for this pair of SNs
	revs.sort()
	
	#Set rev to be the next available revision if requested
	if rev == 'next':
		if len(revs) == 0:	rev = 'a'
		else:				rev = chr(ord(revs[-1]) + 1)
	
	#If the requested revision already exists, check for overwrite or approval
	if rev in revs:
		row = rows.filter_by(rev = rev).first()
		if row.Approval:
			raise Exception(f"Attempting to overwrite an Approved testset!\n\nRevision {rev} for {SN1}-{SN2} IS ALREADY APPROVED!\n\nPlease unapprove the testset before overwriting data or submit to the next available revision: {'a' if len(revs) == 0 else chr(ord(revs[-1]) + 1)}".replace('-None',''))
		if overwrite == True or row.Deleted == True:
			ID = row.ID
			testset = rows.filter(Testset.rev == rev)
			testset.update({'Order':Order,'Customer':Customer,'Engineer':Engineer,'Last_Edit':Last_Edit,'Approval':Approval,'Comments':Comments,'Deleted':False})
			db.commit()
			print(f'Testset updated: {SN1}-{SN2} {rev}'.replace('-None',''))
		elif overwrite == None:
			ID = rows[0].ID
			print(f'Update Ignored: {SN1}-{SN2} {rev}'.replace('-None',''))
		else:
			raise Warning(f"Attempting to overwrite!\nAre you sure you want to submit revision {rev}?\nThe next available revision is {'a' if len(revs) == 0 else chr(ord(revs[-1]) + 1)}")
	#Otherwise, add it
	else:
		ID=newID(table)
		testset = Testset(ID=ID,SN1=SN1,SN2=SN2,rev=rev,Order=Order,Customer=Customer,Engineer=Engineer,Last_Edit=Last_Edit,Comments=Comments,Approval=Approval)
		db.add(testset)
		db.commit()
		print('Testset added: ',testset)
	return ID

def changeRev(db, SN1, SN2=None, rev=None):
	return False

def toggleApproval(db, sn1, sn2, rev):
	# Correct none strings
	if sn2.lower() == 'none':	sn2 = None
	table = db.query(Testset)
	rows = table.filter_by(SN1 = sn1, SN2 = sn2)
	if rows.count() == 0: return
	new = not rows.filter_by(rev = rev)[0].Approval
	testset = rows.filter(Testset.rev == rev)

	# Make datetime out of Last_Edit string
	# Add one sec and turn back into string
	last_edit = datetime.strptime(testset.first().Last_Edit, "%m/%d/%Y %X")
	new_last = last_edit + timedelta(0,1)
	new_last_str = new_last.strftime("%m/%d/%Y %X")

	testset.update({'Approval':new, 'Last_Edit': new_last_str})
	db.commit()
	return new

#Adds a test to a testset. This also has the job of checking the file location and copying the file
def addTest(db, testsetID, test_name, original_file, new_file, minimum_spec=None, min_typ_spec=None, max_typ_spec=None, maximum_spec=None, test_type='None', overwrite=False):#, start_freq, stop_freq, points, header_rows, data_columns):
	#If the original file doesnt exist, raise an Exception
	if not os.path.isfile(original_file):	raise FileNotFoundError(f"File not found: {original_file}")
	
	#Query the DB for this exact test
	test = db.get(test_type_dict[test_type], {'testsetID': testsetID, 'test_name': test_name})
	
	#If the test exists and we are not overwriting it, raise a Warning
	if test != None and overwrite == False:	raise Warning(f"Attempting to overwrite a test!\nAre you sure you want to overwrite '{test_name}'?")
	
	#If there is already a file there, and we arent overwriting, and its not an exact copy, raise an Exception
	if os.path.isfile(new_file) and not overwrite and not filecmp.cmp(original_file,new_file):	raise FileExistsError(f"File already exists: {new_file}")
	
	#Copy the file to its new location
	makeif(os.path.dirname(new_file))
	#If a permission error is reached, replace the file to regain permissions
	try:
		shutil.copy(original_file, new_file)
	except PermissionError:
		replaceFile(new_file)
		shutil.copy(original_file, new_file)
	
	# Correct bad spec values
	if type(minimum_spec) is str:
		try:	minimum_spec = float(minimum_spec)
		except:	minimum_spec = None
	if type(min_typ_spec) is str:
		try:	min_typ_spec = float(min_typ_spec)
		except:	min_typ_spec = None
	if type(max_typ_spec) is str:
		try:	max_typ_spec = float(max_typ_spec)
		except:	max_typ_spec = None
	if type(maximum_spec) is str:
		try:	maximum_spec = float(maximum_spec)
		except:	maximum_spec = None
	
	#If it is a new test, add it like normal
	if test == None:
		test = test_type_dict[test_type](testsetID=testsetID, test_name=test_name, file=new_file, minimum_spec=minimum_spec, min_typ_spec=min_typ_spec, max_typ_spec=max_typ_spec, maximum_spec=maximum_spec, test_type=test_type)#, header_rows=header_rows, data_columns=data_columns, start_freq=start_freq, stop_freq=stop_freq, points=points)
		db.add(test)
		db.commit()
		print(f"Test added: {test_name}")
	#For an existing test, overwrite the entry
	else:
		test = db.query(Test).filter(Test.testsetID == testsetID, Test.test_name == test_name)
		test.update({'file':new_file, 'minimum_spec':minimum_spec, 'min_typ_spec':min_typ_spec, 'max_typ_spec':max_typ_spec, 'maximum_spec':maximum_spec, 'test_type':test_type})#'header_rows':header_rows, 'data_columns':data_columns, 'start_freq':start_freq, 'stop_freq':stop_freq, 'points':points,
		db.commit()
		print(f"Test updated: {test_name} - {new_file}")

'''#Deletes a test. This will also delete the file and remove its directory if it was the last file there
def delTest(db, testsetID, test_name):
	#Query the DB for this exact test
	test = db.get(Test, {'testsetID': testsetID, 'test_name': test_name})
	#If the test doesnt exist, raise a Warning
	if test == None:	raise Warning(f"Attempting to remove a test that doesnt exist: '{test_name}'")
	
	#Get the file path
	path = test.file
	
	#Delete it
	test = db.query(Test).filter(Test.testsetID == testsetID, Test.test_name == test_name)
	test.delete()
	db.commit()
	
	#Now, remove the file and empty directories
	removeFile(path)
'''

#Returns the list of testsets in the database for a given system type description
def getIndex(db, arch = False, sort_list = [], **kwargs):
	#If Type is in kwargs and is None, remove it
	if 'Type' in kwargs:
		# If the type includes VNAX or is None, then include Architecture
		if kwargs['Type'] == None or kwargs['Type'] == 'All' or kwargs['Type'] == 'Any' or 'VNAX' in kwargs['Type']:	arch = True
		if kwargs['Type'] == None or kwargs['Type'] == 'All' or kwargs['Type'] == 'Any':	del kwargs['Type']
	
	(set_rows, sys_dict) = getTestsets(db, **kwargs)
	
	index = {}
	for set_row in set_rows:
		SN = set_row.SN1
		sys = sys_dict[SN]
		set_arch = str(getattr(sys, 'Arch', None))
		if set_row.SN2 != None:
			SN = SN + '-' + set_row.SN2
			sys2 = db.get(System, set_row.SN2)
			set_arch = set_arch + '-' + str(getattr(sys2, 'Arch', None))
		
		if SN in index.keys():
			last_edit = max(datetime.strptime(set_row.Last_Edit,"%m/%d/%Y %H:%M:%S"), datetime.strptime(index[SN][-4],"%m/%d/%Y %H:%M:%S")).strftime("%m/%d/%Y %H:%M:%S")
			index[SN] = [sorted(index[SN][0] + [set_row.rev]), sys.Band, sys.Type, sys.Subtype, set_arch, set_row.Order, set_row.Customer, set_row.Engineer, last_edit, set_row.Approval, set_row.SN2, set_row.SN1]
		else:
			index[SN] = [[set_row.rev], sys.Band, sys.Type, sys.Subtype, set_arch, set_row.Order, set_row.Customer, set_row.Engineer, set_row.Last_Edit, set_row.Approval, set_row.SN2, set_row.SN1]
	
	#Sort the list
	return sortIndexOn(index, cols = ['SN','revs','Band','Type','Subtype','Arch','Order','Customer','Engineer','Last Edit','Approval'], sort = sort_list, arch = arch)

def getPairIndex(db, **kwargs):
	#set_rows = set_rows.filter(or_(Testset.SN1.in_([sys.SN for sys in sys_rows]), Testset.SN2.in_([sys.SN for sys in sys_rows])))
	
	index = [['SN','revs','Band','Subtypes','Arch','Order','Customer','Engineer','Last Edit','Approval']]
	
	return index


def sortIndexOn(index, cols, sort, arch=False):
	if sort == []: sort = ['SN']
	
	#Loop through columns to sort by
	for col in sort:
		#Remove the negative sign if it is there and save the invert tag
		invert = False
		reverse = True
		if col[0] == '-' and len(col) > 1:
			col = col[1:]
			invert=True
		
		#If the column is not in the table columns, then skip it
		if col not in cols:	continue
		
		#Now sort the table by the column
		if col == 'SN':
			index = dict(sorted(index.items(), key=lambda x: int(re.sub('[^0-9]', '', x[0])) if re.sub('[^0-9]', '', x[0]) else 0, reverse=reverse^invert))
		elif col == "Last Edit":
			index = dict(sorted(index.items(), key=lambda x: datetime.strptime(x[1][cols.index(col)-1],"%m/%d/%Y %H:%M:%S"), reverse=reverse^invert))
		elif col == 'Band':
			index = dict(sorted(index.items(), key=lambda x: BANDS.index(x[1][cols.index(col)-1]) if x[1][cols.index(col)-1] in BANDS else -1, reverse=reverse^invert))
		else:
			reverse = False
			index = dict(sorted(index.items(), key=lambda x: str(x[1][cols.index(col)-1]), reverse=reverse^invert))
	
	index = [cols] + [[(ind, max(val[0]))] + val for ind, val in index.items()]
	
	# Remove architectures
	if arch == False:	index = [row[:5]+row[6:] for row in index]
	
	return index

def getCurrentOptions(db, col):
	"""Get distinct values for a given column

    @param db Sqlalchemy session
    @param col desired column such as Testset.Customer

	@return distinct values
    """
	distinct = []

	# Sqlalchemy will return a list of tuples with an empty second value.
	# We can discard the empty values by using `for i, in ...` instead of `for i in ...`
	for i, in db.query(col).distinct():
		distinct.append(i)

	return distinct

def getOptionsByBand(db):
	"""Get a dictionary of possible search options based on any given band

	@param db Sqlalchemy session

	@return dictionary of possible options for given band
	"""
	bands = getCurrentOptions(db, System.Band)
	opts = {}

	for i in bands:
		d = []
		for j, in db.query(System.Type).filter(System.Band == i).distinct():
			d.append(j)

		opts[i] = { "Type" : d }

	for i in bands:
		d = []
		for j, in db.query(System.Subtype).filter(System.Band == i).distinct():
			d.append(j)

		opts[i] = opts[i] |  { "Subtype" : d }

	# opts.update({i { "Type" : d })
	return opts

def getOptionsByType(db):
	"""Get a dictionary of possible search options based on any given band

	@param db Sqlalchemy session

	@return dictionary of possible options for given band
	"""
	types = getCurrentOptions(db, System.Type)
	opts = {}

	for i in types:
		d = []
		for j, in db.query(System.Band).filter(System.Type == i).distinct():
			d.append(j)

		opts[i] = { "Band" : d }

	for i in types:
		d = []
		for j, in db.query(System.Subtype).filter(System.Type == i).distinct():
			d.append(j)

		opts[i] = opts[i] |  { "Subtype" : d }

	# opts.update({i { "Type" : d })
	return opts

def getOptionsBySubtype(db):
	"""Get a dictionary of possible search options based on any given band

	@param db Sqlalchemy session

	@return dictionary of possible options for given band
	"""
	subtypes = getCurrentOptions(db, System.Subtype)
	opts = {}

	for i in subtypes:
		d = []
		for j, in db.query(System.Band).filter(System.Subtype == i).distinct():
			d.append(j)

		opts[i] = { "Band" : d }

	for i in subtypes:
		d = []
		for j, in db.query(System.Type).filter(System.Subtype == i).distinct():
			d.append(j)

		opts[i] = opts[i] |  { "Type" : d }

	# opts.update({i { "Type" : d })
	return opts

# Turns a query object into a list of results, maintaining all public attributes
def query2objects(query):
	class O:	pass
	return_list = []
	for item in query:
		obj = O()
		for attribute in [attr for attr in dir(item) if not attr.startswith('_')]:
			setattr(obj, attribute, getattr(item, attribute, None))
		return_list.append(obj)
	return return_list

"""=============================    General DB functions    ============================="""

#Function that returns all table data in a way that Jinja can take advantage of
def getTableDict(db, sort={'system': ['SN']}):
	metaobj = Base.metadata
	
	tables = {}
	for table in [metaobj.tables[name] for name in metaobj.tables.keys()]:
		rows = db.query(table)
		#Sort the rows based on given priorities
		if table.name in sort.keys():
			for col in sort[table.name]:
				if col not in ORDERS.keys():
					rows = rows.order_by(table.columns[col])
				else:
					rows = rows.order_by(case(ORDERS[col], value=table.columns[col], else_=-1))
		tables[table.name] = [list(table.columns.keys())] + [[str(s).replace('None','-') for s in row] for row in rows]
	
	return {' '.join(e.capitalize() for e in key.split('_')): val for key, val in tables.items()}


"""============================= HTML asset generators and defs ========================="""

# Formats operational specs (mult and input power) for display
def getOpSpecWebInfo(op_spec_dict, op_spec = 'multiplier', unit='x_'):
	strs = []
	for name, val in op_spec_dict.items():
		if op_spec.lower() in name.lower():
			spec_str = f"{name}: {unit.replace('_',str(val).replace(':','-'))}"
			# Remove the spec name to avoid duplications
			idx = name.lower().find(op_spec.lower())
			#print(spec_str,spec_str[:idx].strip(), spec_str[idx+len(op_spec):].strip())
			spec_str = ' '.join([spec_str[:idx].strip(), spec_str[idx+len(op_spec):].strip()])
			# Add the spec value to the string
			strs.append(spec_str.replace(' :',':').strip())
	if len(strs) == 0:
		return 'Not found'
	
	out_str = ', '.join(strs)
	return out_str

# Function that creates a unique key to use for caching testset pages
def getCacheKey(url, SN1, SN2, rev):
	return '-'.join(filter(None, [url, SN1, SN2, rev]))

#Class that contains testset information ready to be used in the html template
class HTML_Testset():
	def __init__(self, sys1=None, sys2=None, ts=None, tests=[]):
		self.SN_name = 'NONE'
		self.sn1=None
		self.sn2=None
		
		self.details = {'Band':None,'Type':None,'Subtype':None}
		self.tests = {}#{'Conversion Loss': {Low-IF Conversion Loss: []}}
		self.files = {'Work Orders': {}, 'Original Files': {}, 'Generated Files': {}}
		self.passing = {}
		self.Comments = ""
		self.Approval = False

		self.Last_Edit = ts.Last_Edit

		self.Deleted = ts.Deleted

		if sys1 != None:
			try:
				self.sn1 = self.SN_name = sys1.SN
				for attr in ['Band', 'Type', 'Subtype']:
					self.details[attr] = getattr(sys1, attr)
				if str(sys1.Arch) != 'None':
					self.details['Architecture'] = str(sys1.Arch)
			except Exception as err:
				print(str(err))
		
		if sys2 != None:
			try:
				self.sn2 = sys2.SN
				self.SN_name += ('-'+sys2.SN)
				self.details['Band'] += ('-'+sys2.Band)
				#self.details['Type'] += ('-'+sys2.Type)
				self.details['Subtype'] += (','+sys2.Subtype).rstrip(',')
				self.details['Architecture'] = str(sys1.Arch) + '-' + str(sys2.Arch)
			except Exception as err:
				print(repr(err))
		
		# Add operational specs to details for QC to confirm
		if sys1:
			try:
				op_spec_dict = SPEC_DICT['Operational'][sys1.Type][sys1.Subtype][sys1.Band]
				mult1_str = getOpSpecWebInfo(op_spec_dict, 'multiplier', 'x_')
				pow1_str = getOpSpecWebInfo(op_spec_dict, 'input power', '_')#'_dBm')
			except Exception as err:
				print(repr(err))
				mult1_str = 'Not found'
				pow1_str = 'Not found'
			
			self.details['Mult Factors'] = mult1_str
			self.details['Input Powers'] = pow1_str
		if sys2:
			try:
				op_spec_dict = SPEC_DICT['Operational'][sys2.Type][sys2.Subtype][sys2.Band]
				mult2_str = getOpSpecWebInfo(op_spec_dict, 'multiplier', 'x_')
				pow2_str = getOpSpecWebInfo(op_spec_dict, 'input power', '_')
			except Exception as err:
				print(repr(err))
				mult2_str = 'Not found'
				pow2_str = 'Not found'
			
			self.details['Mult Factors'] += ' - ' + mult2_str
			self.details['Input Powers'] += ' - ' + pow2_str
		
		if ts != None:
			for attr in ['rev', 'Order', 'Customer', 'Engineer', 'Last_Edit', 'Comments', 'Approval']:
				try:
					setattr(self, attr, getattr(ts, attr, None))
					if attr != 'rev' and attr != 'Comments':	self.details[attr.replace('_',' ')] = getattr(self, attr)
				except Exception as err:
					print(str(err))
		
		if self.Comments == None:	self.Comments = ""
		
		# Grab the work order link by searching backwards from the last edit date for the order number
		#order_num = self.details.get('Order',None)
		#if type(order_num) is str:
		#	wo_files = getWorkOrderLinks(order_num, self.Last_Edit)
		#	for file in wo_files:
		#		self.files['Work Orders'][file.name] = file.path.replace('\\','/')
		
		# Remove WO links for now
		del self.files['Work Orders']

		self.addTests(tests)
	
	#Iterate through test objects, adding first unique test types, then unique test names
	#Each subplot added to the unique test name entry will be added as an image or attempted to merge with any plots
	#{'Conversion Loss':
	#	{'Low-IF Conversion Loss':
	#		[{'format':'image', 'title':'Low Drive Low-IF Conversion Loss', 'file':png2url(test.file), 'file_name':os.path.basename(test.file)}, {'format':'plot', 'file':test.file}]}
	#'Displayed Average Noise Level':
	#	{'DANL':
	#		[{'format':'image', 'title':'', 'file':png2url(test.file), 'file_name':os.path.basename(test.file)}]}}
	def addTests(self, tests):
		if tests == None:	return
		#print([test.test_name for test in tests])
		# breakpoint()
		# Get testset info used to get frequency range info
		sys_type=self.details['Type']
		sys_subtype=self.details['Subtype'].split(',')[0]
		sys_band=self.details['Band'].split('-')[0]
		sys_arch=self.details.get('Architecture','None')
		
		# Get in-band and extended-band frequency range information to be passed into the plotter for spec lines and calculation
		freq_range = getSystemFrequencies(sys_band, sys_type, sys_subtype)
		
		# Set to floats if not None
		for k,v in freq_range.items():
			try:	freq_range[k] = float(str(v))
			except:	freq_range[k] = None
		
		# Unique tag generators for HTML files
		html_tag = 0
		vis_tags = []
		
		# Keep track of all file paths and names for use later
		self.file_paths = []
		
		for test in tests:
			test_type = test.test_type
			
			# Fix harmonics type
			if test_type == 'None' and 'harmonics' in test.test_name.lower():
				test_type = 'HRM'
			
			#Get the full name of the test type if there is one
			if test_type in replacements:	test_type = replacements[test_type]
			# Otherwise, place the filler name
			else:	test_type = 'Other tests'
			
			#Add test type to the dict if its not already there
			if test_type not in self.tests:	self.tests[test_type] = {}
			
			#Now, format the test name removing text in parenthesis and adding it to the test dict for this test type
			test_name, test_subname = removeParen(test.test_name), ' '.join(removeParen(test.test_name, return_paren=True))
			if test_name in replacements: test_name = replacements[test_name]
			test_subname = (test_subname + ' ' + test_name).strip()
			
			# If its a coef "test" then dont add it normally
			if 'coefs' in test_name.lower():
				#Add the file to the dict of original files (even though its a csv now)
				self.files['Original Files'][os.path.basename(test.file)] = test.file
				continue
			
			#Add test name to test type dict if not already there
			if test_name not in self.tests[test_type]:	self.tests[test_type][test_name] = []
			
			#If the file is an image, process it accordingly
			if test.file.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
				#Only add a title if it is needed to distinguish the plot from the test name (ex. LOW DRIVE Low-IF CL)
				title = test_subname if test_subname != test_name else ''
				self.tests[test_type][test_name].append({'format': 'image', 'title': title, 'file': png2url(test.file), 'file_name': os.path.basename(test.file)})
			else:
				file_path = test.file
				self.file_paths.append(file_path)
				
				#Add the file to the dict of original files
				self.files['Original Files'][os.path.basename(test.file)] = file_path
				
				# Variable used to save a loaded xlsx file to save time
				reference_xlsx = None
				
				# If the file is an xlsx, then it will need to be split into sheets and a test will need to be added for each
				sheets_to_plot = ['']
				if '.xlsx' in file_path:
					sheets_to_plot = list(pd.read_excel(test.file, sheet_name=None, index_col=0).keys())
				
				# Loop through sheets (only one for csvs)
				for sheet_to_plot in sheets_to_plot:
					
					#Iterate through all plots for this test and try to add to them
					added = False
					for tst in [tst for tst in self.tests[test_type][test_name] if tst['format'] == 'plot']:
						#Dont stack harmonics
						if 'harmonics' in test_name.lower(): continue
						#Dont stack dual head plots
						if 'sweeps' in test_name.lower(): continue
						if tst['plot'].addTest(test, sheet=sheet_to_plot):
							self.passing.update(tst['plot'].passing)
							added = True
							break
					
					#If there are no plots already or it couldnt be added to any, then make one
					if not added:
						# Skip raw GS data
						if '(raw)' in sheet_to_plot:	continue
						
						# Check if this test needs a J10 comparison
						reference_data = None
						if 'VNAX' in sys_type and 'normalized j10' in test_name.lower():
							ref_dir_path = f'W:/Python Testing Resources/Reference Gold Standards/Normalized J10/{sys_band}'
							if os.path.isdir(ref_dir_path):
								file_obj = [obj for obj in list(os.scandir(ref_dir_path)) if obj.is_file()][0]
								reference_data = {'ref': file_obj.path}#{file_obj.name.replace('.csv',''): file_obj.path}
						
						plot = AltairPlot(test, sheet=sheet_to_plot, sys_type=sys_type, freq_range=freq_range, arch=sys_arch, sys_subtype=sys_subtype, sys_band=sys_band, reference_data=reference_data)
						self.passing.update(plot.passing)
						
						# Replace gs short terms for readability
						if test_type == 'Gold Standards':
							for key, val in gs_replacements.items():
								sheet_to_plot = sheet_to_plot.replace(key, val)
						
						test_plot_name = (test_subname + ' ' + sheet_to_plot).rstrip()
						
						# Clean power sweep test name
						if test.test_type == 'PS':	test_plot_name = test_plot_name.replace('Post SI','').replace('Post RT','').replace('Pre RT','')
						
						if plot.chart == None:
							if '.html' not in file_path.lower():
								self.tests[test_type][test_name].append({'format': 'text', 'title': test_plot_name, 'text': file_path + ' could not be opened.'})
							else:
								with open(file_path,'r') as open_file:
									content = open_file.read()
								
								#Trim off extra, replace vis tag with "unique" tag, and increment the tag number
								tag = f'vis{html_tag}'
								content = content[content.index('<body>')+6:content.index('</body>')].replace("\"vis\"",f"\"{tag}\"").replace("'vis'",f"'{tag}'").replace("\"#vis\"",f"\"#{tag}\"")
								html_tag += 1
								
								self.tests[test_type][test_name].append({'format': 'html', 'title': test_plot_name, 'content': content})
						else:
							vis_tag = 'vt_'+re.sub(r'[^a-zA-Z0-9_:.-]', '_', test_plot_name).replace('.','_').replace('-','_')
							while vis_tag in vis_tags:
								vis_tag = vis_tag+'_'
							vis_tags.append(vis_tag)
							self.tests[test_type][test_name].append({'format': 'plot', 'title': test_plot_name, 'plot': plot, 'vis_tag': vis_tag})
		
		# Sort tests alphabetically
		self.tests = dict(sorted(self.tests.items()))
		
		self.generateFiles()
	
	#Takes the type, subtype, and tests present into account and produces appropriate files for download
	def generateFiles(self):
		sys_type = self.details['Type']
		
		# Generate CL file for NTX testsets
		if sys_type == 'NTX':
			try:
				tests = self.tests[replacements['CL']]
				#print(list(tests.keys()))
				s = 'Low-IF Conversion Loss'
				res = [val for key, val in tests.items() if s in key][0]
				#new_res = [item['plot'].df for item in res if 'chain 1' in item['title'].lower()][0]
				#chain1_lowIF_df = new_res
				#new_res = [item['plot'].df for item in res if 'chain 2' in item['title'].lower()][0]
				#chain2_lowIF_df = new_res
				
				new_res = [item['plot'].df for item in res][0]
				chain1_cols = [col for col in new_res.columns if 'chain 1' in col.lower()]
				chain2_cols = [col for col in new_res.columns if 'chain 2' in col.lower()]
				chain1_lowIF_df = new_res[chain1_cols[0]].to_frame()
				chain2_lowIF_df = new_res[chain2_cols[0]].to_frame()
				
				s = 'High-IF Conversion Loss'
				res = [val for key, val in tests.items() if s in key][0]
				#new_res = [item['plot'].df for item in res if 'chain 1' in item['title'].lower()][0]
				#chain1_highIF_df = new_res
				#new_res = [item['plot'].df for item in res if 'chain 2' in item['title'].lower()][0]
				#chain2_highIF_df = new_res
				
				new_res = [item['plot'].df for item in res][0]
				chain1_cols = [col for col in new_res.columns if 'chain 1' in col.lower()]
				chain2_cols = [col for col in new_res.columns if 'chain 2' in col.lower()]
				chain1_highIF_df = new_res[chain1_cols[0]].to_frame()
				chain2_highIF_df = new_res[chain2_cols[0]].to_frame()
				
				freq = chain1_lowIF_df.index
				
				final_df = pd.DataFrame({
					"Freq(GHz)": freq,
					"Low IF 1 Conversion Loss (dB)": chain1_lowIF_df.iloc[:,0],
					"High IF 1 Conversion Loss (dB)": chain1_highIF_df.iloc[:,0],
					"Low IF 2 Conversion Loss (dB)": chain2_lowIF_df.iloc[:,0],
					"High IF 2 Conversion Loss (dB)": chain2_highIF_df.iloc[:,0]
				})
				
				self.files['Generated Files'][f'{self.SN_name} Conversion Loss.csv'] = getCSVstring(final_df)
			except Exception as err:
				print(str(err))
				self.files['Generated Files'][f'Missing requirements'] = ''
		
		if sys_type == 'SGX' and replacements['TPP'] in self.tests and 'Test Port Power' in self.tests[replacements['TPP']]:
			df = self.tests[replacements['TPP']]['Test Port Power'][0]['plot'].df.add_suffix(' Test Port Power (dBm)')
			
			#For modular files, add each relavent componant
			if self.details['Subtype'] != '' and self.details['Subtype'][0] == 'M':
				for test_name in ['WR5.1 Test Port Power','WR4.3 Test Port Power','WR3.4 Test Port Power','WR2.8 Test Port Power','WR2.2 Test Port Power','WR1.5 Test Port Power','WR1.2 Test Port Power','WR1.0 Test Port Power']:
					if test_name in self.tests[replacements['TPP']]:
						temp_df = self.tests[replacements['TPP']][test_name][0]['plot'].df
						if temp_df.index.size == df.index.size:
							df[test_name.replace('Test Port Power','Frequency (GHz)')] = temp_df.index
							# Grab the column for tpp ('Source' if only one drive was measured or 'Low Drive'/'High Drive' prioritizing Low Drive
							for source_col in ['Source (dBm)','Low Drive','High Drive']:
								if source_col in temp_df.columns:
									df[test_name + ' (dBm)'] = temp_df[source_col].values
									break
			
			self.files['Generated Files'][f'{self.SN_name} Test Port Power.csv'] = getCSVstring(df.reset_index())
			
		elif sys_type == 'SAX' and replacements['CL'] in self.tests:
			subtype = self.details['Subtype']
			band = self.details['Band']
			
			# Grab formatted test names to look for (including if offset)
			loif_test_name, hiif_test_name = self.getIFTestNames(subtype, band)
			
			#If Low-IF or High-IF are not included, none of these correction files are possible
			if loif_test_name not in self.tests[replacements['CL']] or hiif_test_name not in self.tests[replacements['CL']]:
				loif_test_name, hiif_test_name = self.getIFTestNames('-F', band)
				if loif_test_name not in self.tests[replacements['CL']] or hiif_test_name not in self.tests[replacements['CL']]:
					return
			
			#Configuration "B" and "C", plus using High-IF files to calculate configuration "A"
			df = self.tests[replacements['CL']][hiif_test_name][0]['plot'].df
			# Remove duplicated indicies for weird old data
			df = df[~df.index.duplicated(keep='first')]
			hd_col_names = [col for col in df.columns if 'high drive' in col.lower()]
			ld_col_names = [col for col in df.columns if 'low drive' in col.lower()]
			if len(hd_col_names) == 0 or len(ld_col_names) == 0:	return
			hd_col_name = hd_col_names[0]
			ld_col_name = ld_col_names[0]
			df = df[[hd_col_name,ld_col_name]]
			cl_df = df.rename(columns={hd_col_name:'"C" High Freq. Input', ld_col_name:'"B" Standard Input'})
			
			#Configuration "A" (Low Drive High IF + High Drive Low IF - High Drive High IF)
			df = self.tests[replacements['CL']][loif_test_name][0]['plot'].df
			df = df[~df.index.duplicated(keep='first')]
			hd_col_names = [col for col in df.columns if 'high drive' in col.lower()]
			if len(hd_col_names) == 0:	return
			hd_col_name = hd_col_names[0]
			
			# Check if LD low IF already exists
			ld_col_names = [col for col in df.columns if 'low drive' in col.lower()]
			has_LD_low_IF = (len(ld_col_names) != 0)
			
			if has_LD_low_IF:
				config_A_col = df[ld_col_names[0]]
			else:
				config_A_col = cl_df['"B" Standard Input'] + df[hd_col_name] - cl_df['"C" High Freq. Input']
			
			#Add config "A" column to the CL file and use it to create the PXA correction dataframe
			cl_df.insert(loc=0, column='"A" LO/IF Input/Output', value=config_A_col)
			pxa_df = cl_df['"A" LO/IF Input/Output']
			
			# Check if this is a SAX-Z and generate side-band files if so
			if '-Z' in subtype:
				pos_offset_data = pxa_df.copy()
				try:
					#print(loif_test_name, loif_test_name.replace('+','-'))
					loif_data_df = self.tests[replacements['CL']][loif_test_name.replace('+','-')][0]['plot'].df
					#print(loif_data_df)
					loif_ld_col_names = [col for col in loif_data_df.columns if 'low drive' in col.lower()]
					neg_offset_data = loif_data_df[[loif_ld_col_names[0]]]
					anritsu_file = getAnritsuClFile(pos_offset_data, neg_offset_data, self.SN_name, f'{band}SAX-Z-M')
					self.files['Generated Files']['ExternalMixerConversionLossTable.csv'] = anritsu_file
				except Exception as err:
					print(f'Could not find negative offset data: {err}')
			
			#Try to create the .acl file
			if 'SAX' in SPEC_DICT['Operational'].keys() and subtype in SPEC_DICT['Operational']['SAX'].keys():
				try:
					# Extract specs from files. If not able to, then grab from the spec sheet. If both fail, return an error statement
					hd_mult = '0'
					ld_mult = '0'
					
					# Check all high and low drive files for both mults
					hd_file_paths = [file_path for file_path in self.file_paths if '(HD)' in file_path or '(High Drive)' in file_path]
					ld_file_paths = [file_path for file_path in self.file_paths if '(LD)' in file_path or '(Low Drive)' in file_path]
					for file_path in hd_file_paths:
						with open(file_path) as f:
							line = next((l for l in f if 'LO mult:' in l), None)
						if line:
							hd_mult = line.split(',')[-1]
							#print(line, hd_mult)
							break
					for file_path in ld_file_paths:
						with open(file_path) as f:
							line = next((l for l in f if 'LO mult:' in l), None)
						if line:
							ld_mult = line.split(',')[-1]
							#print(line, ld_mult)
							break
					
					# Check spec sheets if not found. Will raise an error if spec does not exist
					if hd_mult == '0':	hd_mult = str(int(SPEC_DICT['Operational']['SAX'][subtype][band]['High Drive Multiplier']))
					if ld_mult == '0':	ld_mult = str(int(SPEC_DICT['Operational']['SAX'][subtype][band]['Low Drive Multiplier']))
					
					# New special check. WR12 SAX-F systems to SpaceX only need 3-port acl file
					special_case = (band == 'WR12' and 'spacex' in str(self.details.get('Customer','')).lower())
					if '-F' in subtype and not special_case:
						#Normal 2-port acl file using Low Drive Low-IF
						mult = ld_mult
						data = pxa_df
						ports = 2
					else:
						#Special 3-port acl file using High Drive Low-IF
						mult = hd_mult
						data = df[hd_col_name]
						# Grab 1.3GHz if offset data if this is a SAX-C
						if '-C' in subtype:
							try:
								new_loif_test_name, new_hiif_test_name = self.getIFTestNames(subtype, band, 1300)
								df = self.tests[replacements['CL']][new_loif_test_name][0]['plot'].df
								hd_col_names = [col for col in df.columns if 'high drive' in col.lower()]
								data = df[hd_col_names[0]]
							except Exception as e:
								print(f'Error generating -C file: {e}')
						ports = 3
						# Create the special acl file for spacex systems
						spec_acl_tests = [test for test in self.tests[replacements['CL']] if 'low-if' in test.lower() and ('1.3ghz if' in test.lower() or '1300mhz if' in test.lower())]
						if 'spacex' in str(self.details.get('Customer','')).lower() and band in spacex_acl_bands and len(spec_acl_tests) > 0:
							df = self.tests[replacements['CL']][spec_acl_tests[0]][0]['plot'].df
							hd_acl_cols = [col for col in df if 'high drive' in col.lower()]
							if len(df.columns) == 1 or (hd_acl_cols) == 0:	data = df[df.columns[0]]
							else:	data = df[hd_acl_cols[0]]
							mult = str(spacex_acl_bands[band])
					acl_file = getACLfile(data, self.SN_name, band, ports, mult)
				except Exception as err:
					acl_file = {'ErrorCreatingACLfile',''}
					print(f'Exception occured when creating acl file: {repr(err)}')
			else:	acl_file = None
			
			#Add config "D" to the file if it exists
			if 'IF-in Conversion Loss' in self.tests[replacements['CL']]:
				df = self.tests[replacements['CL']]['IF-in Conversion Loss'][0]['plot'].df
				df = df[~df.index.duplicated(keep='first')]
				hd_col_names = [col for col in df.columns if 'high drive' in col.lower()]
				if len(hd_col_names) == 0:	return
				cl_df['"D" Block Up-Conversion Loss'] = df[hd_col_names[0]]
			
			#And then add them as csv strings to the data structure
			self.files['Generated Files'][f'{self.SN_name} PXA Table.csv'] = formatPXAfile(pxa_df.copy(), band)
			self.files['Generated Files'][f'{self.SN_name} Conversion Loss.csv'] = getCSVstring(cl_df.reset_index())
			if acl_file is not None:	self.files['Generated Files'][list(acl_file.keys())[0]] = list(acl_file.values())[0]
			
			# Add the config A plot to the Low IF dataframe to plot on the website if it isnt already part of the testset
			if not has_LD_low_IF:
				self.tests[replacements['CL']][loif_test_name][0]['plot'].df.insert(loc=1, column='Low Drive (Calculated)', value=config_A_col)
				self.tests[replacements['CL']][loif_test_name][0]['plot'].df2chart('(Low Drive) ' + loif_test_name)
			
			# Add it to passing spec comparison
			try:	spec = self.passing['(High Drive) ' + loif_test_name][-1]['spec']
			except:	spec = 10
			val = config_A_col.min()
			self.passing.update({'(Low Drive) ' + loif_test_name:[{'value':f'{val:.3f}', 'spec':spec, 'name':'min', 'color':get_hex_color(spec, val, COLOR_SPAN)}]})
			
		elif sys_type == 'CCU' and replacements['CL'] in self.tests:
			
			if 'Optimal Mixer Conversion Loss' in self.tests[replacements['CL']]:
				df = self.tests[replacements['CL']]['Optimal Mixer Conversion Loss'][0]['plot'].df.add_prefix('Optimal ')
				self.files['Generated Files'][f'{self.SN_name} Optimal Conversion Loss.csv'] = getCSVstring(df.reset_index())
			
			tests = ['+6.0GHz IF','-6.0GHz IF']
			files = []
			for offset in tests:
				if 'Optimal Mixer Conversion Loss 6001pts '+offset in self.tests[replacements['CL']]:
					df = self.tests[replacements['CL']]['Optimal Mixer Conversion Loss 6001pts '+offset][0]['plot'].df
				elif 'Optimal Mixer Conversion Loss 6001pts '+offset+' Sweeps' in self.tests[replacements['CL']]:
					df = self.tests[replacements['CL']]['Optimal Mixer Conversion Loss 6001pts '+offset+' Sweeps'][0]['plot'].df
				else:
					continue
				filename = f"{self.details['Band']}{sys_type}{self.details['Subtype']} {self.SN_name.replace(sys_type,'')} "+offset+".csv"
				model = f"{self.details['Band']}{sys_type}{self.details['Subtype']}"
				files.append(formatCCKSfile(df, self.SN_name, model, offset, self.Last_Edit))
			
			if len(files) > 0:
				header = '\n'.join(files[0].split('\n')[:4])
				filename = f"{self.details['Band']}{sys_type}{self.details['Subtype']} {self.SN_name.replace(sys_type,'')}.csv"
				self.files['Generated Files'][filename] = ''.join([header] + [file.replace(header,'') for file in files])
		
		elif sys_type == 'CCD' and replacements['CL'] in self.tests:
			
			if 'Optimal IF out Conversion Loss' in self.tests[replacements['CL']]:
				df = self.tests[replacements['CL']]['Optimal IF out Conversion Loss'][0]['plot'].df.add_prefix('Optimal ')
				self.files['Generated Files'][f'{self.SN_name} Optimal Conversion Loss.csv'] = getCSVstring(df.reset_index())
			
			tests = ['+2.55GHz IF','-2.55GHz IF','+6.20GHz IF','-6.20GHz IF','+7.5225GHz IF','-7.5225GHz IF','+7.89GHz IF','-7.89GHz IF','+8.4GHz IF','-8.4GHz IF']
			files = []
			for offset in tests:
				if 'Optimal IF out Conversion Loss 6001pts '+offset in self.tests[replacements['CL']]:
					df = self.tests[replacements['CL']]['Optimal IF out Conversion Loss 6001pts '+offset][0]['plot'].df
				elif 'Optimal IF out Conversion Loss 6001pts '+offset+' Sweeps' in self.tests[replacements['CL']]:
					df = self.tests[replacements['CL']]['Optimal IF out Conversion Loss 6001pts '+offset+' Sweeps'][0]['plot'].df
				else:
					continue
				filename = f"{self.details['Band']}{sys_type}{self.details['Subtype']} {self.SN_name.replace(sys_type,'')} "+offset+".csv"
				model = f"{self.details['Band']}{sys_type}{self.details['Subtype']}"
				files.append(formatCCKSfile(df, self.SN_name, model, offset, self.Last_Edit))
			
			if len(files) > 0:
				header = '\n'.join(files[0].split('\n')[:4])
				filename = f"{self.details['Band']}{sys_type}{self.details['Subtype']} {self.SN_name.replace(sys_type,'')}.csv"
				self.files['Generated Files'][filename] = ''.join([header] + [file.replace(header,'') for file in files])
		
		elif sys_type == 'PSAX' and replacements['CL'] in self.tests:
			df_dict = {}
			tests = ['+1.0GHz IF','-1.0GHz IF','+6.0GHz IF','-6.0GHz IF']
			for offset in tests:
				col_name = 'Mixer Conversion Loss '+offset
				if col_name in self.tests[replacements['CL']]:
					df_dict[col_name] = self.tests[replacements['CL']][col_name][0]['plot'].df
			
			if len(df_dict) > 0:
				filename = f"{self.SN_name} Conversion Loss.csv"
				self.files['Generated Files'][filename] = getPSAXfile(df_dict)
		
		elif sys_type == 'VNAX' and replacements['TPP'] in self.tests:
			
			filedict = {}
			for test_name, test_data in self.tests[replacements['TPP']].items():
				#print(test_data[0]['plot'].df)
				if test_data[0]['format'] == 'plot':
					cols = getattr(test_data[0]['plot'].df, 'columns', [])
					for col in cols:
						filedict.update(formatVNAXTPPfiles(test_data[0]['plot'].df[col], 'VNAX ' + ''.join([c for c in col if c.isdigit()])))
			
			for filename, filestring in filedict.items():
				self.files['Generated Files'][filename] = filestring
		
		elif sys_type == 'AMC-I' and 'Power Sweep' in self.tests:
			for test_name, test_data in self.tests[replacements['PS']].items():
				for data_ind in range(len(test_data)):
					if 'power' in test_data[data_ind]['title'].lower().replace('power sweep','') and test_data[data_ind]['format'] == 'plot':
						try:
							taper_correction = TAPER_DB_SCALING[self.details['Band']]
							self.files['Generated Files']['Corrected Power Sweeps.csv'] = getCSVstring(test_data[data_ind]['plot'].df.add(taper_correction), index=True)
						except Exception as err:
							print(str(err))
	
	# Returns the formatted test names including if offset
	def getIFTestNames(self, subtype, band, if_offset = None):
		loif_test_name = 'Low-IF Conversion Loss'
		hiif_test_name = 'High-IF Conversion Loss'
		try:
			if if_offset == None:	if_offset = float(SPEC_DICT['Operational']['SAX'][subtype][band]['IF Offset (MHz)'])
			print(if_offset)
			if if_offset != 322.5:
				if_offset_str = f'{if_offset/1000:+}GHzIF'
				print(if_offset_str)
				# Check to make sure at least one file has the right if offset. If not, its probably an old testset
				for test_name in self.tests[replacements['CL']]:
					if loif_test_name in test_name and if_offset_str in test_name.replace(' ',''):
						loif_test_name = test_name
					if hiif_test_name in test_name and if_offset_str in test_name.replace(' ',''):
						hiif_test_name = test_name
				print(loif_test_name)
		except Exception as e:
			print(f'Error generating test names: {e}')
		return loif_test_name, hiif_test_name

def clearCacheByTestset(rdb, SN1, SN2, rev = None):
	"""Clear cached Testsets by SN1, SN2 and rev

	"""
	if SN2 == "None":
		SN2 = None

	if rev == "None":
		rev = None

	if rev == None:
		cachekey = '-'.join(filter(None, [SN1, SN2]))
	else:
		cachekey = '-'.join(filter(None, [SN1, SN2, rev]))

	for key in rdb.keys():
		if cachekey in str(key):
			rdb.delete(key)

def editTestset(db, SN1, SN2, rev, edits):
	"""Edit a testset

	@param db Database Object (if calling from flask this should be app.db)
    @param SN1 Serial Number 1 of System to edit
	@param SN2 Serial Number 2 of System to edit
	@param rev Revision of System to edit
	@param edits Dictionary with desired Testset attributes
	"""

	ts = getTestset(db, SN1, SN2, rev)
	if ts == None:
		return

	for key, value in edits.items():
		if value == 'None':
			value = None

		setattr(ts, key, value)

	db.commit()
	# clearCacheByTestset(SN1, SN2, rev)

def editTest(db, testsetId, testName,  edits):
	"""Edit a Test

	@param db Database Object (if calling from flask this should be app.db)
    @param testsetId ID of test to edit
	@param testName Name of test to edit
	@param edits Dictionary with desired Test attributes
	"""

	q = db.query(Test)
	q = q.filter(
		and_(
			Test.testsetID == testsetId,
			Test.test_name == testName
		)
	)

	test = q.all()

	if len(test) != 1:
		print("Error: found too many or too few tests, taking no action")
		return False

	test = test[0]

	for key, value in edits.items():
		if value == 'None':
			value = None

		setattr(test, key, value)

	db.commit()

def editSystem(db, SN, edits):
	"""Edit a System

	@param db Database Object (if calling from flask this should be app.db)
    @param SN Serial Number of System to edit
	@param edits Dictionary with desired System attributes
	"""

	sys = getSystem(db, SN)
	if sys == None:
		return

	for key, value in edits.items():
		if value == 'None':
			value = None
		if value != 'no-change':
			setattr(sys, key, value)

	db.commit()

def delTest(db, testsetId, testName):
	"""Delete a test

	@param db Database Object (if calling from flask this should be app.db)
    @param testsetId ID of test to delete
	@param testName Name of test to delete
	"""

	q = db.query(Test)
	q = q.filter(
		and_(
			Test.testsetID == testsetId,
			Test.test_name == testName
		)
	)

	# test = q.all()

	if q.count() != 1:
		print("Error: found too many or too few tests, taking no action")
		return False

	q.delete()
	db.commit()

def editTestSpecs(db, testsetId, testName, minimum, maximum, mintyp, maxtyp):
	"""Edit Specs for a Test

	@param db Database Object (if calling from flask this should be app.db)
    @param testsetId ID of test to delete
	@param testName Name of test to delete

	@param minumum Min Spec for Test
	@param maximum Max Spec for Test
	@param mintyp Mintyp Spec for Test
	@param maxtyp Maxtyp Spec for Test
	"""

	q = db.query(Test)
	q = q.filter(
		and_(
			Test.testsetID == testsetId,
			Test.test_name == testName
		)
	)

	test = q.all()

	if len(test) != 1:
		print("Error: found too many or too few tests, taking no action")
		return False

	test = test[0]

	if maximum == "None": maximum = None
	if minimum == "None": minimum = None
	if maxtyp == "None": maxtyp = None
	if mintyp == "None": mintyp = None

	test.maximum_spec = maximum
	test.minimum_spec = minimum
	test.max_typ_spec = maxtyp
	test.min_typ_spec = mintyp

	db.commit()

def getTestsByTestset(db, SN1, SN2, rev):
	"""Get Tests for a given Testset

	@param db Database Object (if calling from flask this should be app.db)
	@param SN1 Serial Number 1 of System to edit
	@param SN2 Serial Number 2 of System to edit
	@param rev Revision of System to edit
	"""
	ts = getTestset(db, SN1, SN2, rev)

	q = db.query(Test)
	q = q.filter(Test.testsetID == ts.ID)

	rows = q.all()
	return rows

def getTestset(db, SN1, SN2, rev):
	"""Get Testset object by SN(s) and rev

	@param db Database Object (if calling from flask this should be app.db)
	@param SN1 Serial Number 1 of System to edit
	@param SN2 Serial Number 2 of System to edit
	@param rev Revision of System to edit
	"""

	if SN2 == 'None':
		SN2 = None

	q = db.query(Testset)
	q = q.filter(
		and_(
			Testset.SN1 == SN1,
			Testset.SN2 == SN2,
			Testset.rev == rev,
		)
	)

	ts = q.all()

	if len(ts) != 1:
		print("Error: found too many or too few testsets, taking no action")
		return None

	# print(f"flagging {SN1} {SN2} {rev} as deleted")
	return ts[0]

# Takes search parameters and returns a testset query and the system dictionary for quick lookup
def getTestsets(db, **kwargs):
	#Query the System and Testset tables and filter through kwargs for applicable search criteria
	sys_table = db.query(System)
	sys_kwargs = {kwarg: kwargs[kwarg] for kwarg in kwargs if hasattr(System, kwarg)}

	set_table = db.query(Testset)
	set_kwargs = {kwarg: kwargs[kwarg] for kwarg in kwargs if hasattr(Testset, kwarg)}
	
	#Search for specific values that can be treated as lists to allow for easier filtering
	sys_filters = {'SN':System.SN, 'Band':System.Band, 'Type':System.Type, 'Arch':System.Arch, 'Subtype':System.Subtype}
	for arg, column in sys_filters.items():
		if arg in sys_kwargs.keys() and type(sys_kwargs[arg]) == list:
			sys_table = sys_table.filter(column.in_([val for val in sys_kwargs[arg]]))
			del sys_kwargs[arg]
	#set_filters = {'Order'
	
	sys_rows = sys_table.filter_by(**sys_kwargs)
	sys_dict = {sys.SN: sys for sys in sys_rows}
	set_rows = set_table.filter_by(**set_kwargs)
	set_rows = set_rows.filter(Testset.Deleted != True)

	if "SN" in kwargs:
		set_rows = set_rows.filter(or_(
			Testset.SN1.in_([sys.SN for sys in sys_rows]),
			Testset.SN2.in_([sys.SN for sys in sys_rows])
		))
	else:
		set_rows = set_rows.filter(Testset.SN1.in_([sys.SN for sys in sys_rows]))

	# If searching by SN, and your search matches SN2, you'll end up with testset in set_rows
	# with SN1 that's not a key in `sys_dict`.
	#
	# This will cause an error on the line that runs `sys = sys_dict[SN]`
	# So we snag the appropriate System(s) and stick 'em in `sys_dict` if not already there.
	if "SN" in kwargs:
		for set_row in set_rows:
			SN = set_row.SN1
			if SN in sys_dict:
				continue

			q = db.query(System)
			sys_append_rows = q.filter(System.SN == SN)
			sys_append_dict = {sys.SN: sys for sys in sys_append_rows}
			sys_dict.update(sys_append_dict)

	# If date in kwargs, and date's aren't empty then filter set_rows accordingly
	if "date" in kwargs.keys() and kwargs['date'] != ['', '']:
		startdate = datetime.fromisoformat(kwargs['date'][0])
		enddate = datetime.fromisoformat(kwargs['date'][1])
		set_rows = set_rows.filter(Testset.datetime.between(startdate, enddate))
	
	return (set_rows, sys_dict)

# Take a testset query and keep only the latest revision for each (NOT USED)
def removeOutdatedRevisions(rows, sn_order=None):
	table = rows.all()
	
	latest_dict = {}
	for row in table:
		dict_key = f'{row.SN1}-{row.SN2}' if row.SN2 is not None else f'{row.SN1}'
		if dict_key not in latest_dict:
			latest_dict[dict_key] = row
		else:
			latest = False
			# If the current row has a more recent revision, replace the row in the dict
			last_edit_row_lead = row.datetime - latest_dict[dict_key].datetime
			if last_edit_row_lead > timedelta(hours=1):
				latest = True
			elif abs(last_edit_row_lead) <= timedelta(hours=1):
				if len(row.rev) == 1 and len(latest_dict[dict_key].rev) == 1 and ord(row.rev) > ord(latest_dict[dict_key].rev):
					latest = True
				elif len(row.rev) > len(latest_dict[dict_key].rev):
					latest = True
			
			if latest:
				#print(f'Replacing latest rev {latest_dict[dict_key]} with {row}')
				#print(f'Latest row in table {latest_dict[dict_key]}; {latest_dict[dict_key].Last_Edit}')
				#print(f'Current row {row}; {row.Last_Edit}')
				#print(f'Difference {last_edit_row_lead}')
				latest_dict[dict_key] = row
	
	# Order it if desired
	if type(sn_order) is not list:
		return list(latest_dict.values())
		
	ordered_latest_list = []
	for sn in sn_order:
		ordered_latest_list.append(latest_dict[sn])
	return ordered_latest_list

# Take a Test query and a dict of testset_ids to sns and remove tests with the same name that are from older revisions
def removeOutdatedTests(rows, tsID_SN_dict, test_filter=None, sn_order=None):
	"""
	test_filter	filters for only tests that include this string if not None
	sn_order	list of sn pairs used to order the result, so its always in order of user query
	"""
	latest_dict = {}
	for row in rows:
		tsID, test_name = row.testsetID, row.test_name
		(SN1, SN2) = tsID_SN_dict[tsID]['SNs']
		rev, datetime = tsID_SN_dict[tsID]['rev'], tsID_SN_dict[tsID]['last_edit']
		
		dict_key = f'{SN1}-{SN2}:;:{test_name}' if SN2 is not None else f'{SN1}:;:{test_name}'
		
		# Only add it to the dict if the test_name being filtered for is in the test_name, or if there is no name being filtered
		if test_filter is None or (type(test_filter) is str and test_filter in test_name):
			if dict_key not in latest_dict:
				latest_dict[dict_key] = row
			else:
				latest = False
				# If the current row has a more recent revision, replace the row in the dict
				last_edit_row_lead = datetime - tsID_SN_dict[latest_dict[dict_key].testsetID]['last_edit']
				if last_edit_row_lead > timedelta(hours=1):
					latest = True
				# If they were uploaded within an hour of each other, theres a chance that they are both old sets uploaded at the same time, so check revision
				elif abs(last_edit_row_lead) <= timedelta(hours=1):
					dict_rev = tsID_SN_dict[latest_dict[dict_key].testsetID]['rev']
					if len(rev) == 1 and len(dict_rev) == 1 and ord(rev) > ord(dict_rev):
						latest = True
					elif len(rev) > len(dict_rev):
						latest = True
				
				if latest:
					#print(f'Replacing latest rev {latest_dict[dict_key].test_name} with {row.test_name}')
					#print(f"Latest row in table {latest_dict[dict_key]}: {tsID_SN_dict[latest_dict[dict_key].testsetID]}; {tsID_SN_dict[latest_dict[dict_key].testsetID]['last_edit']}")
					#print(f"Current row {row}; {tsID_SN_dict[row.testsetID]}: {datetime}")
					#print(f'Difference {last_edit_row_lead}')
					latest_dict[dict_key] = row
	
	# Order it if desired
	if type(sn_order) is not list:	return list(latest_dict.values())
	
	ordered_latest_list = dict(sorted(latest_dict.items(), key=lambda item: sn_order.index(item[0].split(':;:')[0])))
	#print(list(ordered_latest_list.keys())[:10])
	
	return list(ordered_latest_list.values())

def getSystem(db, SN):
	"""Get System object by SN

	@param db Database Object (if calling from flask this should be app.db)
	@param SN Serial Number of System to edit
	"""

	q = db.query(System)
	q = q.filter(
		System.SN == SN
	)

	sys = q.all()

	if len(sys) != 1:
		print("Error: found too many or too few systems, taking no action")
		return None

	return sys[0]

def systemHasActiveTestsets(db, SN):
	"""Check if a given System has undeleted Testsets

	@param db Database Object (if calling from flask this should be app.db)
    @param SN Serial Number of System to check

	@return True if system has undeleted Testsets, otherwise False
    """
	q = db.query(Testset)
	q = q.filter(
		or_(
			Testset.SN1 == SN,
			Testset.SN2 == SN
		)
	)

	q = q.filter(Testset.Deleted == False)

	return q.count() > 0

def delTestset(db, SN1, SN2, rev):
	"""Mark a Testset as Deleted

	This will set the Deleted flag for a given Testset. If too many or too few Testsets are found then no action is taken.

	@param db Database Object (if calling from flask this should be app.db)
	@param SN1 Serial Number 1.
    @param SN2 Serial Number 2.
    @param rev Revision.
    """
	if SN2 == 'None':
		SN2 = None

	q = db.query(Testset)
	q = q.filter(
		and_(
			Testset.SN1 == SN1,
			Testset.SN2 == SN2,
			Testset.rev == rev,
		)
	)

	# print(q.all()[0].SN1)
	# print(q.all())
	ts = q.all()

	if len(ts) != 1:
		print("Error: found too many or too few testsets, taking no action")
		return

	# print(f"flagging {SN1} {SN2} {rev} as deleted")
	ts[0].Deleted = True
	db.commit()

def getHTMLTestset(db, rdb, url, SN1, SN2, rev):
	print(SN1,SN2)
	if SN2 == 'None': SN2 = None

	# Set `cache_string` to be used as Redis key
	cache_string = getCacheKey(url, SN1, SN2, rev)

	# Query DB for TS first to compare to cached data
	ts = db.query(Testset).filter_by(SN1=SN1, SN2=SN2, rev=rev).first()
	print(ts)
	# If Redis connection is available (not None) then attempt to grab data from Redis
	if rdb != None:
		cached_testset_data = rdb.get(cache_string)

		# If data was returned from Redis then return data, else continue to generate as per usual
		if cached_testset_data != None:
			pickle_hts = pickle.loads(cached_testset_data)
			# Compare ts.Last_Edit with cached value, return cache if equal
			if pickle_hts.Last_Edit == ts.Last_Edit:
				# print("Serving pickle")
				return pickle_hts

	sys1 = db.get(System, SN1)
	sys2 = db.get(System, SN2) if SN2 != None else None
	tests = db.query(Test).filter(Test.testsetID == ts.ID) if ts is not None else []
	
	if sys1.Type != 'VNAX':
		hts =  HTML_Testset(sys1, sys2, ts, tests)

		# Cache generated data in Redis if available
		if rdb != None:
			phts = pickle.dumps(hts)
			rdb.set(cache_string, phts, ex=604800)

		return hts
	
	# Going to do special work to pull tests from previous testsets for VNAXs
	rows = db.query(Testset).filter_by(SN1=SN1, SN2=SN2)
	
	# Sort the revs alphabetically and remove revs after this one
	revs = sorted([tset.rev for tset in rows])
	revs = revs[:revs.index(rev)]
	
	# Create dict of revisions linking to the tests required from those revs
	tests_to_pull = {}
	
	test_names = [test.test_name.replace('(','').replace(')','') for test in tests]
	
	# Take care of pulling old coef tests for no reason
	for gs_type in ['TRL','SOLT','ENH21','ENH12']:
		if f'{gs_type}_coefs' in test_names or f'{gs_type}_coefs'.lower() in test_names:
			test_names += [f'{gs_type} coefs',f'{gs_type}_coefs'.lower(),f'{gs_type} coefs'.lower()]
	
	# Loop through past revisions to determine which tests to pull, starting with the most recent
	for revision in reversed(revs):
		# Determine if we can avoid pulling TPP and PL plots from the old format
		ignore_old_tpp = False
		if f'{SN1} Test Port Power' in test_names and ((SN2 is None) or (f'{SN2} Test Port Power' in test_names)):
			ignore_old_tpp = True
		ignore_old_pl = False
		if f'{SN1} Power Levelability' in test_names and ((SN2 is None) or (f'{SN2} Power Levelability' in test_names)):
			ignore_old_pl = True
		#print(ignore_old_tpp)
		#print(test_names)
		# Grab the testset revision to be searched
		tset = db.query(Testset).filter_by(SN1=SN1, SN2=SN2, rev=revision).first()
		# Get all tests for that testset
		new_tests = db.query(Test).filter(Test.testsetID == tset.ID)
		
		# Format the test names so that they will be recognized
		new_test_dict = {}
		for new_test in new_tests:
			new_test_name = new_test.test_name
			# Sorting replacement dict by key length, to avoid replacing keys that are substrings of other keys (Ex: replacing PL in "PLH")
			for key,val in dict(reversed(sorted(replacements.items(), key=lambda item: len(item[0])))).items():
				new_test_name = new_test_name.replace(key,val)
			new_test_dict[new_test.test_name] = new_test_name.replace('(','').replace(')','')
		#print(new_test_dict)
		# Then, remove repeated test names
		new_test_names = []
		for new_test_name, corrected_test_name in new_test_dict.items():
			if corrected_test_name not in test_names:	new_test_names.append(corrected_test_name)
		#new_test_names = list(set(new_test_names) - set(test_names))
		
		if ignore_old_tpp:
			new_test_names = [name for name in new_test_names if 'test port power' not in name.lower()]
		if ignore_old_pl:
			new_test_names = [name for name in new_test_names if not ('power' in name.lower() and 'levelability' in name.lower())]
		test_names += new_test_names
		new_test_dict = {val:key for key,val in new_test_dict.items()}
		if len(new_test_names) > 0:	tests_to_pull[revision] = [tset.ID, [new_test_dict[new_test_name] for new_test_name in new_test_names]]
	
	print(tests_to_pull)
	
	# Then loop through required revs and add queries
	for revision, [tset_ID, tests_required] in tests_to_pull.items():
		new_tests = db.query(Test).filter(Test.testsetID == tset_ID, Test.test_name.in_(tests_required))
		
		# Append the donor rev to the test_name
		for new_test in new_tests:
			#test_names.append(new_test.test_name)
			new_test.test_name = new_test.test_name + ' - {' + revision + '}'
		
		tests = tests.union(new_tests)
	
	# Sort alphabetically by name then type
	tests = tests.order_by(Test.test_name)
	tests = tests.order_by(Test.test_type)
	
	hts = HTML_Testset(sys1, sys2, ts, tests)

	# Cache generated data in Redis if available
	if rdb != None:
		phts = pickle.dumps(hts)
		rdb.set(cache_string, phts, ex=604800)

	return hts

# Go through a table and get all unique test names as keys, with list af applicable testsets as values
def getTestNameTestsetIDdict(db, rows, tsID_SN_dict, test_filter=None, sn_order=None):
	# Get testset IDs to search the test table
	tsIDs = [ts.ID for ts in rows]
	
	# Grab only tests from relavent testsets
	test_rows = db.query(Test).filter(Test.testsetID.in_(tsIDs)).all()
	
	# Filter the tests to remove any with duplicate Test Names but earlier revisions
	test_rows = removeOutdatedTests(test_rows, tsID_SN_dict, test_filter=test_filter, sn_order=sn_order)
	
	# Sort in order of testset ID
	#test_rows = sorted(test_rows, key=lambda o: tsIDs.index(o.testsetID))
	
	# Dictionary of test names to testsetIDs with those testnames
	test_name_dict = {}
	for test_row in test_rows:
		test_name = test_row.test_name
		
		# Remove _coefs "tests"
		if '_coefs' in test_name or ' coefs' in test_name:	continue
		
		if test_name not in test_name_dict:	test_name_dict[test_name] = []
		test_name_dict[test_name].append((test_row.testsetID, test_row.test_name))
	
	# Sort test names alphabetically
	test_name_dict = dict(sorted(test_name_dict.items()))
	
	# Search for test names with sns in them. Add them to the list of the largest substring of its test name out of available keys
	for test_name in list(test_name_dict.keys()):
		if any(system_type in test_name for system_type in SYSTEMS):
			sub_test_name = ''
			for test_name_check in list(test_name_dict.keys()):
				# Ignore matching test names duh
				if test_name_check is test_name:	continue
				if test_name_check in test_name and len(test_name_check) > len(sub_test_name):
					sub_test_name = test_name_check
			# If there was no match, use the 'removeParen' function to create a test name and add it
			if sub_test_name == '':
				trimmed = removeParen(test_name)
				if trimmed != test_name:
					test_name_dict[trimmed] = test_name_dict[test_name]
					del test_name_dict[test_name]
			else:
				#print(f'Adding {test_name} testset IDs {test_name_dict[test_name]} to {sub_test_name} ID list')
				test_name_dict[sub_test_name] += test_name_dict[test_name]
				del test_name_dict[test_name]
	
	return test_name_dict

# Go through a table and get a dictionary of all testsetIDs to pairs of SNs
def getTestsetIDSNdict(db, table):
	return {ts.ID: {'SNs':(ts.SN1,ts.SN2), 'rev':ts.rev, 'last_edit':ts.datetime} for ts in table}

# Take the dict of test names to tsIDs and the dict of tsIDs to sn pairs and format the test name search list
def formatTestNameCompareList(test_name_ID_dict, ID_sn_dict):
	# Create return list including testset count, naming SNs and moving to the end if specific to only one testset
	return_list = []
	return_list_end = []
	for test_name, IDs in test_name_ID_dict.items():
		if len(IDs) > 1:
			return_list.append(f'{test_name} [{len(IDs)}]')
		else:
			return_list_end.append(f"{test_name} [{ID_sn_dict[IDs[0][0]]['SNs'][0]}]" if ID_sn_dict[IDs[0][0]]['SNs'][1] is None else f"{test_name} [{ID_sn_dict[IDs[0][0]]['SNs'][0]}-{ID_sn_dict[IDs[0][0]]['SNs'][1]}]")
	return_list += return_list_end
	#print(return_list)
	return return_list

class AltairPlot():
	def __init__(self, test, col_header=None, sheet=None, sys_type=None, freq_range={'start':None,'stop':None,'ext_start':None,'ext_stop':None}, arch='None', sys_subtype=None, sys_band=None, reference_data=None):
		''' Class used to plot every test displayed on the website. A bit messy
		
		@param test		Test object returned from a query
		@param col_header	Optional prefix to use for column names
		@param sheet		Optional string representing which page of a .xlsx file to read
		@param sys_type		Type of the system that this test is for. Needed for some specific formatting
		@param freq_range	Dict of frequency range start and stop points as floats in GHz
		@param arch			String representing architecture. Used for some specific formatting
		@param sys_subtype	Optional string representing system subtype. Used for specific formatting
		@param sys_band		Optional string representing system band. Used for NormJ10
		@param reference_data	Optional data to be plotted alongside as a reference
		'''
		self.df = pd.DataFrame()
		self.test_type = None
		self.chart = None
		self.json = None
		self.specs = {}
		self.passing = {}
		self.sys_type = sys_type
		self.sys_subtype = sys_subtype
		self.sys_band = sys_band
		self.arch = arch
		self.start = freq_range['start']
		try: self.start = float(self.start)
		except: print(type(self.start))
		self.stop = freq_range['stop']
		try: self.stop = float(self.stop)
		except: print(type(self.stop))
		self.ext_start = freq_range['ext_start']
		self.ext_stop = freq_range['ext_stop']
		self.test_type = test.test_type
		self.test_name = test.test_name
		self.col_header = col_header
		self.gs_id = sheet
		self.reference_data = reference_data
		
		# Open the file and read into a df. If it is an xlsx file, then read the sheet requested
		if '.xlsx' in test.file:
			if sheet == None:	self.df = pd.read_excel(test.file, index_col=0)
			else:				self.df = pd.read_excel(test.file, sheet_name=sheet, index_col=0)
		else:
			try:	self.df = readFile(test.file, UCA=self.test_type == 'UCA')
			except:	return None
		
		# Grab spec dict from test object
		self.specs = test.getSpecDict()

		self.og_df = self.df.copy()
		
		# Format the incoming dataframe
		self.df = self.formatDF(self.df, test.test_name, test.test_type, col_header)
		
		# Convert the df to a chart so it is ready to display
		self.df2chart(test.test_name)
	
	# Formats the incoming dataframe. Done on every file coming in
	def formatDF(self, df, test_name, test_type, col_header):
		# If TPP, remove extra data
		if test_type == 'TPP':
			if 'Source (dBm)' in df.columns:
				df = df.loc[:,['Source (dBm)']]
		
		# Rework PL column names to GHz if needed
		if test_type == 'PL':
			try:
				if float(df.columns[0]) > 1000000000:
					df.columns = [str(float(col)/1000000000) + ' GHz' for col in df.columns]
			except:	pass
		
		#Remove fake imaginary column
		if 'ImS11' in df.columns and (df['ImS11'] == 0).all():	del df['ImS11']
		
		# Remove phase columns for now if this is not a stability test
		if self.test_type != 'SB':
			for column in df.columns:
				if '(deg)' in str(column).lower():	del df[column]
		
		#Rename columns in the new dataframe to reflect information
		test_subnames = ' '.join(removeParen(test_name, return_paren = True))
		if col_header == None or col_header == '':
			col_header = test_subnames + ' ' if len(test_subnames) > 0 else ''
			self.col_header = col_header
		df = df.add_prefix(col_header)
		
		return df
	
	def addTest(self, test, col_header=None, chart=True, sheet=None):
		# Never stack Powerlevelability of Gold Standards
		if test.test_type in ['PL','GS']:	return False
		
		#Return False if the file cannot be read
		if '.xlsx' in test.file:
			if sheet == None:	return False
			else:
				try:	df = pd.read_excel(test.file, sheet_name=sheet, index_col=0)
				except:	return False
		else:
			UCA = True if self.test_type == 'UCA' else False
			try:	df = readFile(test.file, UCA=UCA)
			except:	return False
		
		#Return False if the test types are different or the specs dont match
		if test.test_type != self.test_type:	return False
		# If the specs dont match, just use the new specs
		if self.specs != test.getSpecDict():
			if test.getSpecDict() != {}:	self.specs = test.getSpecDict()
			#return False
		
		df = self.formatDF(df, test.test_name, test.test_type, col_header)
		
		# Sheet stacking behavior is for power sweep stacking, but current and power need to be separated. Check for different units
		if getLastParen(self.df.columns[0]) != getLastParen(df.columns[0]):	return False
		
		# If the indexes dont line up, do this weird non-interpolating combination of dfs and plot that instead
		matching_ind = self.df.index.equals(df.index)
		
		#Return false if the merge fails (just in case)
		try:	df_new = mergeDFs(self.df, df)
		except:	return False
		
		self.df = df_new
		if chart:	self.df2chart(test.test_name)
		return True
	
	def addSpecLine(self, val, color, start=None, stop=None, xinterval=None, indexname='Frequency (GHz)', y_axis='Y'):
		if self.chart == None:	return
		if val == None:			return
		
		if start == None:	start = self.df.index.min()
		if stop == None:	stop = self.df.index.max()
		
		#self.chart += alt.Chart().mark_rule(color=color).encode(y=alt.datum(float(val)))
		
		if xinterval is None:
			line = pd.DataFrame({'x':[start,stop],'y':[val, val]})
			line_plot = alt.Chart(line).mark_line(color=color).encode(x='x',y='y')
		else:
			line = pd.DataFrame({indexname:[start,stop],'value':[val, val]})
			line_plot = alt.Chart(line).mark_line(color=color).encode(
					x = alt.X(indexname, scale=alt.Scale(domain=xinterval), axis=alt.Axis(title=indexname)),
					y = alt.Y('value:Q', axis=alt.Axis(title=f'{y_axis}')))
		
		self.chart += line_plot
	
	def addSpecComparison(self, spec, value, test_name, spec_name, prefix=None, color_span=COLOR_SPAN):
		if test_name not in self.passing:	self.passing[test_name] = []
		
		#Add a new entry into the spec pass/fail list
		self.passing[test_name].append({})
		self.passing[test_name][-1]['value'] = f'{value:.3f}'
		self.passing[test_name][-1]['spec'] = spec
		name = ('' if prefix == None else f'{prefix} ') + spec_shorts.get(spec_name, spec_name)
		self.passing[test_name][-1]['name'] = name
		
		#Generate a descript color
		reverse = ('max' in spec_name)
		try:	color = get_hex_color(spec, value, color_span, reverse)
		except:	color = "#000000"
		self.passing[test_name][-1]['color'] = color
	
	def getDFSpecValDict(self, df):
		#(Remove 0 columns from median calc for Harmonics main tone and take max of medians) (Separating min and max typ values)
		return {'minimum': df.min().min(), 'min_typ': df.loc[:, (df.fillna(0) != 0).any(axis=0)].median(numeric_only=True).min(),
				'max_typ': df.loc[:, (df.fillna(0) != 0).any(axis=0)].median(numeric_only=True).max(), 'maximum': df.max().max()}
	
	def df2chart(self, test_name=''):
		df = self.df
		
		# Reformat every column name to remove bad quotations
		for n in range(len(df.columns)):	df.rename(columns={df.columns[n]: str(df.columns[n]).replace('"','').strip()}, inplace = True)
		
		# Name the y axis
		y_axis = replacements.get(self.test_type,'Test Type')
		
		# Pull the value used to color failing/passing specs so that it can be changed by test type
		color_span = COLOR_SPAN
		if self.test_type in SPEC_COLOR_THRESHOLDS:
			color_span = float(SPEC_COLOR_THRESHOLDS[self.test_type])
		
		# Format the y axis and dataframe to % of max power if the test is uca
		if self.test_type == 'UCA':
			y_axis = '% of Maximum Power'
			df = df.apply(pd.to_numeric, errors='coerce').apply(lambda x: 100 * x/x.max(), axis=0)
		
		# If this is an IFBW test, only plot the first column
		elif self.test_type == 'IF_BW' or (str(self.test_type) == 'None' and ('IF' in test_name) and ('BW' in test_name)):
			if 'mixer cl' in df.columns:
				df = df.loc[:,['mixer cl']]
			else:
				# Grab every column with 'mixer cl' in it. If there are none, just take the first
				mix_cl_cols = [col for col in df.columns if 'mixer cl' in col.lower()]
				if len(mix_cl_cols) > 0:	df = df.loc[:,mix_cl_cols]
				else:						df = df.iloc[:,0:1]
		
		# If this is a Stability test, change the range across which spec color fades
		elif self.test_type == 'SB':
			color_span = self.specs.get('max_typ',None)
		
		# Special check for Noise measurement test to remove all but first column
		elif 'noise measurement' in test_name.lower():
			if 'T(K)' in df.columns:
				df = df.loc[:,['T(K)']]
		
		# Add taper corrections for AMC-I power sweeps
		if 'Power (dBm)' in self.og_df.columns.to_list() and self.sys_type == "AMC-I" and self.test_type != 'TPP':
			if self.sys_band in TAPER_DB_SCALING:
				taper_correction = TAPER_DB_SCALING[self.sys_band]
				df = df.add(taper_correction)
		
		# Trim dataframe to in-band data of relevant columns and use that to calculate values (Unless the test itself is band specific).
		df_in_band = df.copy()
		if not any([(band in self.test_name) for band in BANDS]):
			df_in_band[df_in_band.index < self.start] = None
			df_in_band[df_in_band.index > self.stop] = None
		
		# Remove traces from the in-band dataframe whose standard deviation is much higher than (> xthresh) the minimum for spec calculation
		df_in_band_calc = df_in_band.copy()
		
		# For dynamic range, also create "extended-band" dataframe and create extended spec
		if self.start >= df.index.min() and self.stop <= df.index.max() and self.test_type == "DR":
			df_ext_band = df.copy()
			# Convert index to float to avoid "Cannot index integers using a float" error
			df_ext_band.index = df_ext_band.index.astype('float')
			df_ext_band[self.start:self.stop] = None
			df_ext_band[df_in_band.index < self.ext_start] = None
			df_ext_band[df_in_band.index > self.ext_stop] = None
		else:
			df_ext_band = None
		
		# Grab the dataframe describing which traces to include in spec calculation
		trace_whitelist = spec_trace_df_dict
		all_cols = list(df.columns)
		good_cols = all_cols
		
		# If there is a column header that was added to the columns, then calculate spec for only those columns
		if self.col_header != None and self.col_header != '':
			df_in_band_calc = df_in_band_calc[[col for col in good_cols if self.col_header in col]]
		
		arch = self.arch if self.arch != 'RX-TXRX' else 'TXRX-RX'
		if self.test_type in trace_whitelist.keys() and str(arch) != 'None' and not ('short' in self.test_name.lower() and 'load' in self.test_name.lower()):
			trace_df = trace_whitelist[self.test_type]
			if arch in trace_df.index:
				names_allowed = [name for name in trace_df.columns if trace_df.at[arch,name]]
				good_cols = []
				for col_name in df.columns:
					if any([(name in col_name) for name in names_allowed]):	good_cols.append(col_name)
				if good_cols != []:
					#print(self.test_name, df_in_band_calc, good_cols)
					df_in_band_calc = df_in_band_calc[good_cols]
				#print(good_cols)
				if df_ext_band is not None:	df_ext_band_calc = df_ext_band[good_cols]
		
		# Pull spec values
		df_vals = self.getDFSpecValDict(df_in_band_calc)
		
		# Width shorter for VNAX systems maybe
		width = 1500# if self.sys_type != 'VNAX' else 700
		
		# Create x interval and set the default range if frequency ranges are applicable for this test
		start = self.start if self.ext_start == None else self.ext_start
		stop = self.stop if self.ext_stop == None else self.ext_stop
		dfmin, dfmax = df_in_band.index.min(), df_in_band.index.max()

		x_label = ""
		plot_format_df = plot_format_df_dict.get('labels',pd.DataFrame())
		if self.test_type in plot_format_df.columns:
			x_label = plot_format_df.at['x_label',self.test_type]
		
		# Determine if data exists solely out-of-band
		if dfmin == None or dfmax == None or start == None or stop == None:	all_oob = True
		else:	all_oob = not (start > dfmin and start < dfmax and stop > dfmin and stop < dfmax)
		# Special check. Dont do any bound limiting if the x-axis is time
		all_oob = all_oob or 'time' in x_label.lower()
		if all_oob:
			start, stop = dfmin, dfmax
		#start, stop = dfmin, dfmax
		xinterval = alt.selection_interval(encodings=['x'], value={'x':[start, stop]})
		
		# Define custom scales and custom trace removal?
		customY = [None, None]
		df = df.copy()[good_cols]
		
		#set this to blank by default
		fstr = ''

		if self.arch == 'TXRX-RX' or self.arch == 'RX-TXRX':
			for column in df.columns:
				for trace in ['S12(dB)','S12(Deg)','S12(Mag)','S22(dB)','S22(Deg)','S22(Mag)']:
					if trace in column:
						df = df.drop(column, axis=1)
		if self.test_type == 'IS':
			customY = [-0.05,2]
		elif self.test_type == 'SB':
			s = self.specs.get('max_typ',None)
			try:	s = float(s)
			except:	s = 6
			customY = [0,2*s]
			try:
				y = float(self.specs.get('maximum',None))
				customY = [0,y]
			except:	pass
		elif self.test_type == 'DR':
			xinterval = alt.selection_interval(encodings=['x'])
		elif self.test_type == 'WQ':
			xinterval = alt.selection_interval(encodings=['x'])
		elif self.test_type == 'GS':
			# Make GS plots skinnier so you can view more at once
			width = 750
			test_id = self.gs_id.lower()
			if 'normalized j10' in self.test_name.lower():
				if 'S11(dB)' in df.columns:
					df.drop('S11(dB)', axis=1, inplace=True)
				if 'S22(dB)' in df.columns:
					df.drop('S22(dB)', axis=1, inplace=True)
				subdf = df.loc[start:stop]
				customY = [subdf.min().min(),subdf.max().max()]
			elif 'trl' in self.test_name.lower():
				std_vals = df.loc[start:stop].std()
				non_noisy_traces = std_vals[std_vals < 1].index
				if len(non_noisy_traces) == 0 or 'xcut' in test_id:
					#thresh = std_vals.min()+0.001
					#non_noisy_traces = std_vals[std_vals < thresh].index
					non_noisy_traces = df.columns
				clean_df = df.loc[start:stop, non_noisy_traces]
				view_Y_limits = [clean_df.min().min(),clean_df.max().max()]
				limit_diff = abs(view_Y_limits[-1]-view_Y_limits[0])+0.001
				#print(test_id, non_noisy_traces, std_vals, view_Y_limits, limit_diff)
				if 'pl-pl' in test_id or 'ro-ro' in test_id:
					customY = [-100,0]
				elif 'ro-swg1' in test_id or 'swg1-ro' in test_id or 'st-st' in test_id or 'xqs' in test_id or 'xswg' in test_id or 'xth' in test_id:
					customY = [-5,5]
				elif 'xj10' in test_id:
					customY = [-50,0]
				customY = [view_Y_limits[0]-(limit_diff/20),view_Y_limits[-1]+(limit_diff/20)]
		elif self.test_type == 'YFAC':
			df.drop(df.columns.difference(['T(K)']), axis=1, inplace=True)
		elif self.test_type == 'DCO':
			#set y-axis label to be IF power (dBm)
			y_axis = 'IF Power (dBm)'
			#reduce number of ticks in x-axis
			fstr = '.2g'
		
		# Grab plot formatting to determine axis labels
		plot_format_df = plot_format_df_dict.get('labels',pd.DataFrame())
		if self.test_type in plot_format_df.columns:
			x_label = plot_format_df.at['x_label',self.test_type]
			if (type(x_label) is str) and (len(x_label) > 1):
				df.index.names = [x_label]
			if 'I (A)' in self.og_df.columns.to_list() and self.sys_type == "AMC-I": #for special case of current (for power sweep) on AMC-I
				y_label = 'Current (A)'
			else:
				y_label = plot_format_df.at['y_label',self.test_type]
			if (type(y_label) is str) and (len(y_label) > 1):
				y_axis = y_label
		
		# If there is reference data, add it to the plot, taking only desired column names
		column_names = df.columns
		if type(self.reference_data) is dict:
			for tag, file in self.reference_data.items():
				ref_df = readFile(file).add_suffix(f' ({tag})')
				# Filter out only the desired columns
				desired_cols = []
				for col_name in ref_df.columns:
					if any([des_col in col_name for des_col in column_names]):	desired_cols.append(col_name)
				if len(desired_cols) > 0:
					df = mergeDFs(df, ref_df[desired_cols])
		column_names = list(df.columns)
		
		# If this is IFBW, then calculate the line of best fit from 322.5MHz to the spec freq
		IFBW_fit_line_data = None
		if self.test_type == 'IF_BW' or self.test_type == 'IFBW':
			# If there is a column header that was added to the columns, then calculate spec for only those columns
			if self.col_header != None and self.col_header != '':
				ifbw_df = df[[col for col in df.columns if self.col_header in col]]
			else:	ifbw_df = df
			#print(ifbw_df)
			# Grab the start and stop frequencies to calculate line of best fit across
			fit_line_start_x = SPEC_DICT['Operational'].get(self.sys_type,{}).get(self.sys_subtype,{}).get(self.sys_band,{}).get('IF Offset (MHz)',None)
			fit_line_stop_x = SPEC_DICT['Operational'].get(self.sys_type,{}).get(self.sys_subtype,{}).get(self.sys_band,{}).get('IF Bandwidth Maximum (GHz)',None)
			#print(fit_line_start_x, fit_line_stop_x)
			try:	fit_line_start_x = float(fit_line_start_x)/1000
			except:	fit_line_start_x = 0.3225
			try:	fit_line_stop_x = float(fit_line_stop_x)
			except:	fit_line_stop_x = 40
			
			# Interpolate values for start and stop freq if needed and trim to those frequencies
			interp_for = [point for point in [fit_line_start_x,fit_line_stop_x] if point not in ifbw_df.index]
			interp_vals = np.interp(interp_for, ifbw_df.index, ifbw_df.iloc[:,0])
			interp_df = pd.DataFrame({ifbw_df.index.name:interp_for, ifbw_df.columns[0]:interp_vals}).set_index(ifbw_df.index.name)
			combined_df = pd.concat([ifbw_df, interp_df]).sort_index()
			# Normalize the index so that 40. can be found as 40.0 :(
			combined_df.index = pd.Index(np.round(combined_df.index, 6))
			
			#trimmed_df = combined_df.loc[fit_line_start_x,fit_line_stop_x]
			trimmed_df = locFloatIndex(combined_df, fit_line_start_x, fit_line_stop_x)
			#print(trimmed_df)
			# Determine the coefficients of the best-fit line; y = slope*x + intercept
			slope, intercept = np.polyfit(trimmed_df.index.values, trimmed_df.iloc[:,0].values, 1)
			
			# Use these coefficients to calculate start and stop points of the line
			fit_line_start_y = slope*fit_line_start_x + intercept
			fit_line_stop_y = slope*fit_line_stop_x + intercept
			
			spec = self.specs.get('maximum', '')
			self.addSpecComparison(spec, slope, test_name, 'max (dB/GHz)', color_span=color_span)
			IFBW_fit_line_data = pd.DataFrame({'x':[fit_line_start_x,fit_line_stop_x], 'y':[fit_line_start_y,fit_line_stop_y]})
		
		# If the column_header is in every column, then it is redundant and can be removed
		if all([self.col_header in col for col in df.columns]) and (len(df.columns) > 1):	df.columns = df.columns.str.removeprefix(self.col_header)
		
		# Reformat the df to be easily fed into the chart
		df = df.reset_index()
		indexname = df.columns[0]
		df = df.melt(indexname)
		
		# Legend work
		leg_title = 'Legend'
		df = df.rename(columns={'variable':leg_title})
		
		selection = alt.selection_point(fields=[leg_title])
		
		# Create the chart
		self.chart = alt.Chart(df).mark_line().encode(#x=indexname,
				x = alt.X(indexname,
					scale=alt.Scale(domain=xinterval),
					axis=alt.Axis(title=indexname, format=fstr)),
				y = alt.Y('value:Q', axis=alt.Axis(title=f'{y_axis}')) if customY == [None, None] else 
					alt.Y('value:Q', axis=alt.Axis(title=f'{y_axis}'), scale=alt.Scale(domain=customY)),
				color = alt.Color(f'{leg_title}:N'),
				opacity = alt.condition(selection, alt.value(1), alt.value(0.2))
				).properties(width=width,height=460).interactive(bind_x = False).transform_filter('isValid(datum.value)')
		
		# Add the spec lines
		vals_added = []
		# For Dynamic Range, split specs into traces to show values for each
		if self.test_type in ['DR']:
			for spec_col in good_cols:
				df_col_vals = self.getDFSpecValDict(df_in_band_calc[spec_col].to_frame())
				for spec, val in self.specs.items():
					if val == None:	continue
					
					# Add spec comparison to the list
					self.addSpecComparison(val, df_col_vals[spec], test_name, spec, prefix=spec_col, color_span=color_span)
					
					# Add the line to the chart
					if val not in vals_added:
						self.addSpecLine(val, spec_colors[spec], self.start, self.stop, xinterval=xinterval, indexname=indexname, y_axis=y_axis)
						vals_added.append(val)
				
		elif self.test_type != 'DANL' and IFBW_fit_line_data is None:
			for spec, val in self.specs.items():
				if val == None:	continue
				
				# Add spec comparison to the list
				self.addSpecComparison(val, df_vals[spec], test_name, spec, color_span=color_span)
				
				#do not put a spec line for current sweep (associated with power sweep) for AMC-I
				if 'I (A)' in self.og_df.columns.to_list() and self.sys_type == "AMC-I": continue
				
				# Add the line to the chart
				if val not in vals_added:
					self.addSpecLine(val, spec_colors[spec], self.start, self.stop, xinterval=xinterval, indexname=indexname, y_axis=y_axis)
					vals_added.append(val)
		
		# Calculate DANL and add just the comparison
		if self.test_type == 'DANL':
			self.addSpecComparison(self.specs.get('max_typ'), calcNoiseMarker(df_in_band), 'Displayed Active Noise Level', 'max', color_span=color_span)
		
		# Add 1% line on UCA tests and 1dB line to IS
		if self.test_type == 'UCA' or self.test_type == 'IS':
			self.chart += alt.Chart().mark_rule(color='blue', strokeDash=[10, 10]).encode(y=alt.datum(1))
		
		# Add slope of best fit to IFBW
		if IFBW_fit_line_data is not None:
			self.chart += alt.Chart(IFBW_fit_line_data).mark_line(color='blue', strokeDash=[10, 10]).encode(x='x',y='y')
		
		# Add extended band spec for dynamic range
		if self.test_type == 'DR' and self.ext_start != None and self.ext_stop != None and df_ext_band is not None:
			try:
				ext_df_vals = {'minimum': df_ext_band_calc.min().min(), 'min_typ': df_ext_band_calc.loc[:, (df_ext_band_calc != 0).any(axis=0)].median(numeric_only=True).min(),
						'max_typ': df_ext_band_calc.loc[:, (df_ext_band_calc != 0).any(axis=0)].median(numeric_only=True).max(), 'maximum': df_ext_band_calc.max().max()}
				test_name = 'Ext. band '+test_name
				
				# Add spec comparison to the list and lines to the chart
				if (val := self.specs.get('minimum',110)) is not None:
					corr = 10
					if 'EB' in str(self.sys_subtype):	corr = 15
					self.addSpecComparison(spec = val-corr, value = ext_df_vals['minimum'], test_name = test_name, spec_name = 'min', color_span=color_span)
					self.addSpecLine(val-corr, spec_colors['minimum'], self.ext_start, self.start, xinterval=xinterval, indexname=indexname, y_axis=y_axis)
					self.addSpecLine(val-corr, spec_colors['minimum'], self.stop, self.ext_stop, xinterval=xinterval, indexname=indexname, y_axis=y_axis)
				
				if (val := self.specs.get('min_typ',120)) is not None:
					self.addSpecComparison(spec = val-10, value = ext_df_vals['min_typ'], test_name = test_name, spec_name = 'typ', color_span=color_span)
					self.addSpecLine(val-10, spec_colors['typical'], self.ext_start, self.start, xinterval=xinterval, indexname=indexname, y_axis=y_axis)
					self.addSpecLine(val-10, spec_colors['typical'], self.stop, self.ext_stop, xinterval=xinterval, indexname=indexname, y_axis=y_axis)
			except:
				pass
		
		# Create the legend chart
		legend = alt.Chart(df).mark_point(filled=True, size=300
				).encode(
					y=alt.Y(f'{leg_title}:O', axis=alt.Axis(orient='right'), sort=column_names),
					color=alt.condition(selection, alt.Color(f'{leg_title}:O', legend=None, scale=alt.Scale(scheme='category10'), sort=column_names), alt.value('lightgray'))
				).add_params(selection)
		
		# Create the x-axis scaling chart
		xview = alt.Chart(df).mark_line().encode(
			x = alt.X(indexname,axis=alt.Axis(title=None,labels=False)),
			y = alt.Y('value:Q',axis=alt.Axis(title='X Zoom',labels=False)),
			color = alt.Color(f'{leg_title}:N'),
			opacity = alt.condition(selection, alt.value(0.4), alt.value(0.1))
			).add_params(xinterval).properties(width=width,height=40)
		
		# Add in-band frequency lines
		if not all_oob:
			xview += alt.Chart().mark_rule(color='blue', strokeDash=[5,5]).encode(x=alt.datum(self.start))
			xview += alt.Chart().mark_rule(color='blue', strokeDash=[5,5]).encode(x=alt.datum(self.stop))
			if self.ext_start != None:	xview += alt.Chart().mark_rule(color='grey', strokeDash=[5,5]).encode(x=alt.datum(self.ext_start))
			if self.ext_stop != None:	xview += alt.Chart().mark_rule(color='grey', strokeDash=[5,5]).encode(x=alt.datum(self.ext_stop))
		
		self.chart = ((self.chart & xview) | legend).configure_axis(labelFontSize = 16, labelLimit = 0)
		
		self.json = self.chart.to_json()


#Creates an altair plot to compare data (unused)
def comparePlot(db, test_rows, sys_table, testset_table, Bands=[], Types=[], Subtypes=[]):
	
	#Filter each column of the table to only include systems that meet the requested options
	sys_filters = [(Bands,System.Band), (Types,System.Type), (Subtypes,System.Subtype)]
	for lst, column in sys_filters:
		if len(lst) > 0:
			sys_table = sys_table.filter(column.in_([val for val in lst]))
	SNs = [sys.SN for sys in sys_table]
	
	#Get all testset IDs belonging to these systems in order to get the tests
	testset_table = testset_table.filter(Testset.SN1.in_([SN for SN in SNs if 'SAX 084' not in SN]))
	IDs = [testset.ID for testset in testset_table]
	
	print('Testsets:',testset_table.count())
	
	#Create lookup dict
	SN_look_dict = {}
	rev_look_dict = {}
	testset_ID_list = []
	for testset in testset_table:
		SN_look_dict[testset.ID] = testset.SN1
		rev_look_dict[testset.ID] = testset.rev
		testset_ID_list.append(testset.ID)
	
	test_rows = test_rows.filter(Test.testsetID.in_(testset_ID_list))
	
	print('Relevant Tests:',test_rows.count())
	
	if test_rows.count() == 0:	return None
	
	# Get in-band and extended-band frequency range information to be passed into the plotter for spec lines and calculation
	Band = None if len(Bands) == 0 else Bands[0]
	Type = None if len(Types) == 0 else Types[0]
	Subtype = None if len(Subtypes) == 0 else Subtypes[0]
	freq_range = getSystemFrequencies(Band, Type, Subtype)
	
	plot = AltairPlot(test_rows.first(), col_header = str(SN_look_dict[test_rows.first().testsetID])+str(rev_look_dict[test_rows.first().testsetID]), freq_range = freq_range)
	
	for n, test in enumerate(test_rows):
		if n==0:	continue
		if 'SHM' in SN_look_dict[test.testsetID]:
			print(f'Skipping SHM {SN_look_dict[test.testsetID]}')
			continue
		plot.addTest(test, col_header = str(SN_look_dict[test.testsetID])+str(rev_look_dict[test.testsetID]), chart=False)
	
	plot.df2chart()
	
	return plot

# Class used to plot lots of data together, using tags to filter traces
class ComparisonPlot():
	def __init__(self, test_rows, tsID_SN_dict = None, include_header = False):
		"""
		
		"""
		self.include_header = include_header
		self.rows = test_rows
		self.tsID_SN_dict = tsID_SN_dict
		self.df = None
		self.chart = None
		self.createDF()
	
	def createDF(self):
		""" Creates one large long-form dataframe from the test table query
		"""
		# First, create the list of dictionaries containing dataframes and associated information
		df_dict_list = []
		for test in self.rows:
			file_data = readFile(test.file, get_header=self.include_header)
			
			# Remove phase columns for now if this is not a stability test
			if 'phase' not in test.test_name:
				if self.include_header:	df = file_data['header']
				else:					df = file_data
				for column in df.columns:
					if '(deg)' in str(column).lower():	del df[column]
			
			if self.include_header:
				df_dict = file_data['header']
				df_dict.update({'DataFrame':file_data['data'],'source':test.test_name})
			else:
				df_dict = {'DataFrame':file_data,'source':test.test_name}
			# Include the source Testset as a column if provided with a lookup table
			if self.tsID_SN_dict is not None:
				testset = '-'.join([sn for sn in self.tsID_SN_dict[test.testsetID]['SNs'] if sn is not None]) + f" {self.tsID_SN_dict[test.testsetID]['rev']}"
			else:
				testset = str(test.testsetID)
			df_dict['testset'] = testset
			df_dict_list.append(df_dict)
		#print(df_dict_list[0])
		self.df = DFs2longDF(df_dict_list)
		#print(self.df.iloc[::1000,:])
		self.createChart()
	
	def createChart(self):
		"""
		"""
		col_list = list(self.df.columns)
		index_col_ind = 0
		for n, col in enumerate(col_list):
			if 'freq' in col.lower():	index_col_ind = n
		index_col = col_list.pop(index_col_ind)
		value_col_ind = 0
		for n, col in enumerate(col_list):
			if 'value' in col.lower():	value_col_ind = n
		value_col = col_list.pop(value_col_ind)
		label_col_ind = 0
		for n, col in enumerate(col_list):
			if 'label' in col.lower():	label_col_ind = n
		label_col = col_list.pop(label_col_ind)
		trace_col_ind = 0
		for n, col in enumerate(col_list):
			if 'trace' in col.lower():	trace_col_ind = n
		trace_col = col_list.pop(trace_col_ind)
		testset_col_ind = 0
		for n, col in enumerate(col_list):
			if 'testset' in col.lower():	testset_col_ind = n
		testset_col = col_list.pop(testset_col_ind)
		
		# Add label back in
		col_list = [label_col] + col_list
		
		# Click selection used for the interactive legend
		#click_selection = alt.selection_point(fields=[label_col])
		# Click and drag selection for trace selecting
		#drag_selection = alt.selection_interval()
		
		# Selection used for the zoomed in plot
		brush = alt.selection_interval()
		
		# Create a list representing all fields that you could filter by, starting with most important, testset and trace
		filter_list = [s for s in [testset_col, trace_col] + col_list.copy() if len(set(list(self.df[s]))) != 1]#skipping fields with one option
		filter_list = [str(col_name) + ':N' for col_name in filter_list]#[:6]#not limiting for now
		
		# Loop through the list and create selections for each
		selection_dict = {}
		for field in filter_list:
			selection_dict[field] = alt.selection_point(fields=[field.replace(':N','')])
		
		# Opacity condition controlling the traces visibility
		opacity = alt.condition(np.bitwise_and.reduce(list(selection_dict.values())), alt.value(0.95), alt.value(0.02))
		
		# The base plot
		base = alt.Chart(self.df).mark_line().encode(
			x=alt.X(f'{index_col}:Q').title('Frequency (GHz)').axis(labelFontSize=10, titleFontSize=12),
			y=alt.Y(f'{value_col}:Q').title('Magnitude (dB)').axis(labelFontSize=10, titleFontSize=12),
			color=f'{label_col}:N',
			tooltip=f'{label_col}:N',
			opacity=opacity
		).add_params().transform_filter('isValid(datum.value)')
		
		# Chart with the main plot, allowing a selection to be made
		chart = base.add_params(brush).properties(width=1000,height=360)
		
		# Chart containing the zoomed in view
		zoom = base.encode(
			x=alt.X(f'{index_col}:Q').title('Frequency (GHz)').scale(zero=False),
			y=alt.Y(f'{value_col}:Q').title('Magnitude (dB)').scale(zero=False),
			color=alt.Color(f'{label_col}:N', legend=None)
		).transform_filter(brush).properties(width=1600,height=640)
		
		# Rough legend options for now
		#base_legend = alt.Chart(self.df).mark_rect().encode(
		#	alt.Y(f'{testset_col}:N').axis(orient='right'),
		#	x=f'{trace_col}:N',
		#	color=alt.condition(click_selection | drag_selection, alt.Color(f'{label_col}:N', legend=None), alt.value('lightgray'))
		#)
		#click_legend = base_legend.add_params(click_selection).properties(title='(Shift) Click')
		#drag_legend = base_legend.add_params(drag_selection).properties(title='Click & Drag')
		
		# If there is one trace name, then dont even add the drag legend
		#if len(list(set(self.df[trace_col]))) == 1:
		#	self.chart = (chart | click_legend) & zoom
		#else:
		#	self.chart = (chart | click_legend | drag_legend) & zoom
		
		# Loop through filter options and create a legend chart for each, adding them to the main chart
		for field, select in selection_dict.items():
			name = field.replace(':N','').capitalize()
			legend = alt.Chart(self.df, title=alt.TitleParams(name, anchor='start')).mark_point(filled=True, size=300).encode(
				alt.Y(field).axis(orient='right', labelFontSize=10, titleFontSize=0, labelLimit=0).title(name),
				color=alt.condition(select, alt.Color(field, legend=None), alt.value('lightgray'))
			).add_params(select)
			chart = chart | legend
		
		self.chart = chart & zoom


def getCSVstring(data, index=False):
	# If it is a .xlsx file, convert to dataframe
	if isinstance(data, str) and '.xlsx' in data:
		data = pd.read_excel(data)
		csv_string = data.to_csv(index=False)
	
	#If the input is a file path, read it into a Pandas Dataframe
	elif isinstance(data, str):
		with open(data, 'r') as f:
			try:
				csv_string = ''.join(f.readlines())
			except:
				csv_string = ''
				print('Bad Data',data)
	
	#Convert the Pandas Dataframe to a CSV string
	elif isinstance(data, pd.DataFrame):
		csv_string = data.to_csv(index=index)
	
	else:	raise ValueError("Invalid input type")
	
	return csv_string

def formatPXAfile(pxa_df, band):
	#Format the dataframe and convert into CSV String
	pxa_df.index = pxa_df.index.map(mapper=lambda x: f"{(x*1000):.1f}")
	pxa_df.rename('', inplace = True).index.rename(name = "DATA", inplace = True)
	pxa_header = '\n'.join(['Amplitude Correction,', 'Description Field,', f"Model:VDI{band}SAX,", ',', ',', 'Frequency Unit,MHz', 'Antenna Unit,None', 'Frequency Interpolation,Linear'])
	
	return '\n'.join([pxa_header, getCSVstring(pxa_df.reset_index())])

def formatCCKSfile(df, sn, model, offset, timestamp):
	ccks_df = df.iloc[:,:1]
	ccks_df = ccks_df.rename(columns={df.columns[0]:''})
	ccks_df.index.rename("DATA", True)
	
	lo_above_rf = 'TRUE' if '-' in offset else 'FALSE'
	if_freq = offset[1:-6]
	
	ccks_header = '\n'.join([f'Serial Number,{sn}', f'Model,{model}', "Frequency Unit,GHz", f"Calibration Timestamp,{timestamp}", "LO Parked,FALSE", f"IF Frequency,{if_freq}", f"LO Above RF,{lo_above_rf}"])
	
	return '\n'.join([ccks_header, getCSVstring(ccks_df.reset_index())])

def formatVNAXTPPfiles(series, sn='VNAX ####', prn_power=12):
	# For WR5.1 -EB systems. Look for special close frequency indicies and copy the value (x @ 130.000000001GHz = x @ 130GHz)
	for rounded, floating in [(128.0,128.000000001),(130.0,130.000000001)]:
		if rounded in series.index and floating in series.index:
			series.loc[floating] = series.loc[rounded]
	
	# Extract values
	xvals = series.index
	yvals = series.values
	
	#write to a csv string
	csvio = io.StringIO()
	writer = csv.writer(csvio, delimiter=',')
	writer.writerow(['Note: Out of band data is not guaranteed to be accurate'])
	writer.writerow(['Freq(GHz)','Power(dBm)'])
	for k,j in zip(xvals, yvals):
		writer.writerow([k,j])
	csvstring = csvio.getvalue()

	#convert xvals to Hz for the prn
	xvals = xvals*1e9
	
	prnio = io.StringIO()
	writer = csv.writer(prnio, delimiter=',', quoting=csv.QUOTE_ALL)
	writer.writerow([f'InputPower:{prn_power}dBm'])
	writer.writerow(['PM5 Log Mag'])

	writer = csv.writer(prnio, delimiter=',')

	writer.writerow(['Freq (Hz)','dBm',''])
	for k,j in zip(xvals,yvals):
		# Format the index to remove trailing zeros
		ind = f'{k:.12e}'.split('e')
		ind = str(float(ind[0])) + 'e' + ind[1]
		writer.writerow([ind,str(float(f'{j:.12g}')),''])
	prnstring = prnio.getvalue()
	
	return {f'{sn} Test Port Power.csv': csvstring, f'{sn} Test Port Power.prn': prnstring}

def getACLfile(data, SN, band, ports, mult):
	letter, date = 'USER', datetime.now().strftime("%d.%b.%y").upper()
	multiplier = '0'
	mult = str(mult).replace('\n','')
	user = True
	if band in acl_band_designations.keys():
		letter = acl_band_designations[band]["Letter"]
		multiplier = str(acl_band_designations[band]["Multiplier"])
		user = acl_band_designations[band]["USER"]
	
	user_start_freq = user_stop_freq = None
	if (mult != multiplier): # check if harmonic factor is same as standard system of that band
		letter = 'USER'
		user_start_freq = (7*float(mult)) + 0.5 # calculate values based on USER range of FSU
		user_stop_freq = (15.5*float(mult)) - 0.5
	
	if (user): # check if USER range exists for given system
		letter = 'USER'
		user_start_freq = (7*float(mult)) + 0.5 # calculate values based on USER range of FSU
		user_stop_freq = (15.5*float(mult)) - 0.5
	
	head = '\r\n'.join(['# Mixer Name',SN,'# Serial Number',SN,'# Band',letter,'# Number of Harmonic',mult,
					  '# Bias','0','# Ports',str(ports),'# Comment','','# Date',date,'# Calibration data'])
	
	#Drop every other point and the center point
	data = data.iloc[::2].drop(data.index[len(data)//2])
	
	if user_start_freq != None and user_stop_freq != None:
		#How far in to remove a point from each side
		remove = 2
		data = data.drop(data.index[[remove-1, -remove]])
		body = '\r\n'.join([f'({(1000000000*key):.6f},{val:.10f})'.replace('( ','(') for key, val in data.to_dict().items()])
		body = '\r\n'.join([f'({(1000000000*user_start_freq):.6f},00.0000000000)', body, f'({(1000000000*user_stop_freq):.6f},00.0000000000)'])
	else:
		body = '\r\n'.join([f'({(1000000000*key):.6f},{val:.10f})'.replace('( ','(') for key, val in data.to_dict().items()])
	
	return {f'{SN} Table_{mult}.acl': '\r\n'.join([head, body, ''])}

def getAnritsuClFile(pos_offset, neg_offset, sn, product):
	anr_df = pos_offset.to_frame()
	anr_df.index.name = anr_df.index.name.replace('(','[').replace(')',']')
	anr_df = anr_df.rename(columns={anr_df.columns[0]:'Conversion Loss (Low) [dB]'})
	anr_df.insert(loc=1, column='Conversion Loss (High) [dB]', value=neg_offset)
	anritsu_header = '\n'.join(['Version,2,', f'Serial Number,{sn},', f'{product},', f'Band,{int(pos_offset.index.min())}-{int(pos_offset.index.max())}'])
	
	return '\n'.join([anritsu_header, getCSVstring(anr_df.reset_index())])

def getPSAXfile(test_dict):
	# Take the first dataframe and add the rest as columns
	first = True
	for test_name, df in test_dict.items():
		if isinstance(df, pd.DataFrame):
			if first:
				first=False
				out_df = df
				out_df.rename(columns={df.columns[0]: test_name}, inplace=True)
			else:
				out_df[test_name] = df.iloc[:,0:1]
	
	return getCSVstring(out_df, index=True)