import pandas as pd
import sys, os

#pd.options.mode.chained_assignment = None  # default='warn'

PYTHON_RESOURCE_DIR = 'W:/Python Testing Resources'
SYSTEM_SPEC_PATH = PYTHON_RESOURCE_DIR + '/Device Specs'

from contextlib import contextmanager
@contextmanager
def suppress_stdout():
	with open(os.devnull, "w") as devnull:
		old_stdout = sys.stdout
		sys.stdout = devnull
		try:  
			yield
		finally:
			sys.stdout = old_stdout

def getBandSettings():
	return pd.read_csv(SYSTEM_SPEC_PATH + '/Band_settings.csv', index_col = 0)

'''======== Loading all specifications and testing requirements from local spreadsheets ========'''

#Returns spec data in a dictionary of spec category, system Type, system Subtype, and system Architecture
def getSpecDict():
	system_specs = {'Operational':{},'Performance':{},'Test Requirements':{}}
	Types = [os.path.basename(x.path) for x in os.scandir(SYSTEM_SPEC_PATH) if x.is_dir()]
	if 'PSAX' in Types:
		Types.remove('PSAX')
		Types.append('PSAX')
	for Type in Types:
		system_specs['Operational'][Type], system_specs['Performance'][Type], system_specs['Test Requirements'][Type] = {}, {}, {}
		current_dir = SYSTEM_SPEC_PATH + '/' + Type
		Subtypes = [os.path.basename(x.path).replace(Type, '') for x in os.scandir(current_dir) if x.is_dir()]
		for Subtype in Subtypes:
			try:#to load performance and operational specs
				info = pd.read_excel(current_dir + '/' + Type+Subtype + '/Specifications.xlsx', sheet_name = None, index_col = 0, dtype=object)
				system_specs['Operational'][Type][Subtype] = info['Operational']
				system_specs['Performance'][Type][Subtype] = info['Performance']
			except:
				print("Tried to load specifications for " + Type+Subtype + " and failed.")
			
			system_specs['Test Requirements'][Type][Subtype] = {}
			try:#to load testing requirements
				system_specs['Test Requirements'][Type][Subtype] = pd.read_excel(current_dir + '/' + Type+Subtype + '/Testing Requirements' + '.xlsx', sheet_name = None, index_col = 0, dtype=object)
			except:
				print("Tried to load testing requirements for " + Type+Subtype + " and failed.")
	return system_specs

#Returns the spec data in a way that jinja can more take advantage of
def getJinjaSpecDict():
	with suppress_stdout():	spec_dict = getSpecDict()
	del spec_dict['Test Requirements']
	for spec in spec_dict.keys():
		for system in spec_dict[spec].keys():
			for subtype in spec_dict[spec][system]:
				df = spec_dict[spec][system][subtype].copy()
				df.insert(0, subtype, df.index)
				row_list = [list(df.columns)] + df.values.tolist()
				spec_dict[spec][system][subtype] = row_list
	return spec_dict

BAND_SETTINGS = getBandSettings()
SPEC_DICT = getSpecDict()
