import os
import pandas as pd
import numpy as np
import csv
import warnings

def readFile(path, get_info=False, get_header=False, correct_index=True, UCA=False):

	fr = FileReader(path, UCA=UCA)
	df = fr.get_df()

	if type(df) == dict:
		#get_info and get_header don't work for XLSX output, which is a dict
		return df

	if get_info or get_header:
		out_dict = {'data': df}
		
		if get_info:
			out_dict['start_freq'] = df.index[0]
			out_dict['stop_freq'] = df.index[-1]
			out_dict['points'] = len(df.index)
			out_dict['header_rows'] = fr.skiprows
			out_dict['data_columns'] = len(df.columns)			

		if get_header:
			out_dict['header'] = fr.header_dict

		return out_dict

	return df

class FileReader:
	#copied Carter's readFile function with the goal of parsing into smaller pieces
	#rewrite into a factory class
	def __init__(self):
		#this doesn't get called if you have __new__ defined
		pass

	def __new__(self, path, **kwargs):
		#just determine the type and pass arguments into the correct subclass
		#first grab the extension and determine filetype
		my_ext = os.path.splitext(path)[-1].lower()
		subclass_dict = {
			'.csv': CSVReader,
			'.xlsx': ExcelReader,
			'.s1p': SNPReader,
			'.s2p': SNPReader,
			'.dat': DATReader,
		}
		subclass = subclass_dict[my_ext]

		explicit_UCA = kwargs.get('UCA',False)
		if (explicit_UCA or ('UCA' in path)):
			subclass = UCAReader

		return subclass(path, **kwargs)

class BaseReader:
	def __init__(self, path, correct_index=True, **kwargs):
		self.path = path
		self.autocorrect_index_units = correct_index
		self.header = 'infer'
		self.prefix = None
		self.skiprows = 0

		try:
			self.fo = open(self.path, 'r')
		except FileNotFoundError as err:
			raise FileNotFoundError(err)
		except Exception as err:
			raise Exception("Error opening file \""+self.path+"\":\n"+str(err))


	def open_file(self):
		try: 
			my_file = csv.reader(self.fo, delimiter=self.split_char)
		except Exception as err:
			self.fo.close()
			raise Exception("csv.reader error opening file \""+self.path+"\":\n"+str(err))

		return my_file
	def get_header_row_and_prefix(self, my_file):

		self.header_dict = {}
		for num, line in enumerate(my_file, -1):
			try:	#Check for when all non blank values can all be floats. If there are no values, go to the next line
				float_list = [float(s) for s in [v for v in line if v != '' and v != '-']]
				float_list[0]
			except:	#If not, use these items as the row column count and go to the next line
				if len(line) == 2 and len(line[0]) > 0 and line[0][-1] == ':':	self.header_dict[line[0]] = line[1]
				continue

			if num < 0:
				self.header = None
				self.prefix = 'N'
			self.skiprows = max(0, num)
			break

		self.fo.close()

	def read_df(self):
		read_frame = pd.read_csv(self.path,\
			sep=self.split_char,\
			index_col=0,\
			skiprows=self.skiprows,\
			na_values='-',\
			header=self.header)

		self.df = read_frame

	def drop_na_values(self):
		self.df = self.df.dropna(how='all')

	def add_prefixes(self):
		if self.prefix != None:
			self.df = self.df.add_prefix(self.prefix)

	def drop_end_row(self):
		try:
			self.df.drop('END',axis=0,inplace=True)
		except:
			pass

	def correct_tpp_units(self):
		try:
			#Now, account for TPP files to convert units
			if 'tpp_mw' in self.path:	self.df = self.df.iloc[:,0:1].apply(self.mW_to_dBm)
			elif 'tpp_dbm' in self.path:	self.df = self.df.iloc[:,0:1]
		except Exception as err:	raise Exception("File \""+self.path+"\" opened but could not be read:\n"+str(err))

	def correct_index_units(self):
			
		# Correct the index by default
		if self.autocorrect_index_units:
			#If there is no index name, name it "Freq"
			if self.df.index.names[0] == None or type(self.df.index.names[0]) == int:	self.df.index.rename("Freq", inplace=True)
			#Finally, correct frequency units
			if 'ghz' in self.df.index.names[0].lower():
				pass
			elif 'mhz' in self.df.index.names[0].lower():
				self.df.index = self.df.index.astype(float) / 1e3
			elif 'khz' in self.df.index.names[0].lower():
				self.df.index = self.df.index.astype(float) / 1e6
			elif 'hz' in self.df.index.names[0].lower():
				self.df.index = self.df.index.astype(float) / 1e9
			else:
				while np.mean(self.df.index.astype(float)) > 2000:
					self.df.index = self.df.index.astype(float) / 1e3
			self.df.index.rename("Frequency (GHz)", inplace=True)

	def apply_extra_corrections(self):
		pass

	def get_df(self):
		file = self.open_file()
		self.get_header_row_and_prefix(file)
		self.read_df()
		self.drop_na_values()
		self.add_prefixes()
		self.drop_end_row()
		self.correct_tpp_units()
		self.correct_index_units()
		if self.df is None:
			raise Exception(f"No data found in {self.path}")
		self.apply_extra_corrections()
		return self.df

	def mW_to_dBm(self,mW):
		return 10*np.log10(np.absolute(mW))



class SNPReader(BaseReader):
	def __init__(self, path, **kwargs):
		super().__init__(path, **kwargs)
		self.split_char = ' '

		#Quick new test to see if its one of those tab-delimited .s1p files
		text = self.fo.read()
		self.fo.seek(0)
		if text.count('\t') > text.count(self.split_char):
			self.split_char = '\t'

class UCAReader(BaseReader):
	def __init__(self, path, **kwargs):
		super().__init__(path, **kwargs)
		self.split_char = '\t'

	def read_df(self):
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			read_frame = pd.read_csv(self.path,\
				sep=self.split_char,\
				index_col=False,\
				skiprows=self.skiprows,\
				na_values='-',
				header=self.header)

			if self.prefix != None:
				read_frame = read_frame.add_prefix(self.prefix)

			read_frame.index = read_frame.pop(read_frame.columns[0])

		self.df = read_frame

	def drop_na_values(self):
		pass
	def correct_index_units(self):
		pass

	def apply_extra_corrections(self):
		#if its a UCA we have to apply the frequency factor
		freq_fac = 1
		info = ' '.join(self.df.columns)
		ind = info.find('Freq fac: ')
		if ind != -1:
			freq_fac = int(info[ind+10:].split(' ')[0])
		self.df.index = self.df.index * freq_fac


		#and also this extra pivot table
		self.df = self.df.reset_index()

		#Use pivot_table() as opposed to pivot to avoid error
		self.df = self.df.pivot_table(\
			index = self.df.columns[-1],\
			columns = self.df.columns[0],\
			values = self.df.columns[1])
		self.df.columns = [format(col, '.4f') + ' (GHz)' for col in self.df.columns]
		#Correct "Unnamed: 5" index title
		if ':' in self.df.index.name:
			self.df.rename_axis('UCA Input (V)', inplace=True)

class DATReader(BaseReader):
	def __init__(self, path, **kwargs):
		super().__init__(path, **kwargs)
		self.split_char = '\t'

	def apply_extra_corrections(self):
		#if its a DAT we have to apply the frequency factor
		freq_fac = 1
		info = ' '.join(self.df.columns)
		ind = info.find('Freq fac: ')
		if ind != -1:	freq_fac = int(info[ind+10:].split(' ')[0])
		self.df.index = self.df.index * freq_fac


class CSVReader(BaseReader):
	def __init__(self, path, **kwargs):
		super().__init__(path, **kwargs)
		self.split_char = ','

class ExcelReader(BaseReader):
	def __init__(self, path, **kwargs):
		self.path = path

	def readXLSX(path, sheet=None):
		dfs = pd.read_excel(path, sheet_name=sheet, index_col=0)
		return {k:v for k,v in dfs.items() if k != 'Header'}

	def get_df(self):
		#I think this just reads the first page
		dfs = pd.read_excel(self.path, sheet_name=None, index_col=0)
		return {k:v for k,v in dfs.items() if k != 'Header'}

"""-------------------------File reading functions-------------------------"""
#Reads every column of a file into a dataframe, inferring headers if
#possible and converting tpp files and frequency units appropriately
def readFile_old(path, get_info = False, get_header = False, correct_index = True, UCA = False):
	# Redirect .xlsx files
	if '.xlsx' in path:
		return readXLSX(path)
	
	#By default, infer the header and use no prefix
	read_frame = None
	header, prefix = 'infer', None
	columns = 2
	skiprows = 0
	
	#Will probably remove this
	if '.dat' in path:
		DAT = True
		if 'UCA' in path:	UCA = True
	else:
		DAT = False
	
	#Determine the character to split by based on the file type
	split_char = ' ' if ((path.lower().rfind('.s1p') != -1) or (path.lower().rfind('.s2p')) != -1) else ','
	if ((path.lower().rfind('.dat') != -1)):	split_char = '\t'
	
	#Open the file to read line by line
	try:	fo = open(path, 'r')
	except FileNotFoundError as err:	raise FileNotFoundError(err)
	except Exception as err:	raise Exception("Error opening file \""+path+"\":\n"+str(err))
	
	#Quick new test to see if its one of those tab-delimited .s1p files
	text = fo.read()
	fo.close()
	if text.count('\t') > text.count(split_char):	split_char = '\t'
	
	fo = open(path, 'r')
	try:	my_file = csv.reader(fo, delimiter = split_char)
	except Exception as err:
		fo.close()
		raise Exception("Error opening file \""+path+"\":\n"+str(err))
	header_dict = {}
	for num, line in enumerate(my_file, -1):
		try:	#Check for when all non blank values can all be floats. If there are no values, go to the next line
			float_list = [float(s) for s in [v for v in line if v != '' and v != '-']]
			float_list[0]
		except:	#If not, use these items as the row column count and go to the next line
			if len(line) == 2 and len(line[0]) > 0 and line[0][-1] == ':':	header_dict[line[0]] = line[1]
			continue
		#The nunber of columns is the number of elements in this list
		columns = len(float_list)
		#If the values are on the first line of the file, then use prefixed headers
		if num < 0:	header, prefix = None, 'N'
		#Skip one under this many rows, load the file, and exit the loop
		skiprows=max(0,num)
		
		read_frame = pd.read_csv(path, sep=split_char, index_col=0, skiprows=skiprows, na_values='-', header=header)
		read_frame = read_frame.dropna(how='all')# Remove NAN rows
		
		if prefix != None:	read_frame = read_frame.add_prefix(prefix)
		
		#Catch the "Information lost" warning for UCA files
		if UCA:
			with warnings.catch_warnings():
				warnings.simplefilter("ignore")
				read_frame = pd.read_csv(path, sep=split_char, index_col=False, skiprows=skiprows, na_values='-', header=header)
				if prefix != None:	read_frame = read_frame.add_prefix(prefix)
			read_frame.index = read_frame.pop(read_frame.columns[0])
		break
	fo.close()
	
	#If the read_frame is still None, return because no data was found
	if read_frame is None:	raise Exception(f"No data found in {path}")
	#Drop any 'END' lines (Useful for couplers)
	try:	read_frame.drop('END', axis=0, inplace=True)
	except:	pass
	#If any dataframe manipulation fails, tell the user that the file could not be read
	try:
		#Now, account for TPP files to convert units
		if 'tpp_mw' in path:	read_frame = read_frame.iloc[:,0:1].apply(mW_to_dBm)
		elif 'tpp_dbm' in path:	read_frame = read_frame.iloc[:,0:1]
		
		# Correct the index by default
		if correct_index:
			#If there is no index name, name it "Freq"
			if read_frame.index.names[0] == None or type(read_frame.index.names[0]) == int:	read_frame.index.rename("Freq", inplace=True)
			#Finally, correct frequency units
			if 'ghz' in read_frame.index.names[0].lower():
				pass
			elif 'mhz' in read_frame.index.names[0].lower():
				read_frame.index = read_frame.index.astype(float) / 1e3
			elif 'khz' in read_frame.index.names[0].lower():
				read_frame.index = read_frame.index.astype(float) / 1e6
			elif 'hz' in read_frame.index.names[0].lower():
				read_frame.index = read_frame.index.astype(float) / 1e9
			else:
				while np.mean(read_frame.index.astype(float)) > 2000:
					read_frame.index = read_frame.index.astype(float) / 1e3
			read_frame.index.rename("Frequency (GHz)", inplace=True)
		
		#Also, account for UCA files to convert format
		if UCA or DAT:
			freq_fac = 1
			info = ' '.join(read_frame.columns)
			ind = info.find('Freq fac: ')
			if ind != -1:	freq_fac = int(info[ind+10:].split(' ')[0])
			read_frame.index = read_frame.index * freq_fac
			if UCA:
				read_frame = read_frame.reset_index()
				#Use pivot_table() as opposed to pivot to avoid error
				read_frame = read_frame.pivot_table(index = read_frame.columns[-1], columns = read_frame.columns[0], values = read_frame.columns[1])
				read_frame.columns = [format(col, '.4f') + ' (GHz)' for col in read_frame.columns]
				#Correct "Unnamed: 5" index title
				if ':' in read_frame.index.name:	read_frame.rename_axis('UCA Input (V)', inplace=True)
	except Exception as err:	raise Exception("File \""+path+"\" opened but could not be read:\n"+str(err))
	
	#Output file data in a dict of other information if requested
	if get_info or get_header:
		out_dict = {'data': read_frame}
		if get_info:
			out_dict['start_freq'] = read_frame.index[0]
			out_dict['stop_freq'] = read_frame.index[-1]
			out_dict['points'] = len(read_frame.index)
			out_dict['header_rows'] = skiprows
			out_dict['data_columns'] = len(read_frame.columns)
		if get_header:
			out_dict['header'] = header_dict
		return out_dict
	
	return read_frame

def readXLSX(path, sheet=None):
	dfs = pd.read_excel(path, sheet_name=sheet, index_col=0)
	return {k:v for k,v in dfs.items() if k != 'Header'}

#Convert from mW to dBm
def mW_to_dBm(mW):
	return 10*np.log10(np.absolute(mW))