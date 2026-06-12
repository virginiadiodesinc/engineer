import pandas as pd
import numpy as np
import re
import os, os.path
import statistics
import math

from util.functions import readFile
from recorder import errMsg
#from recorder import readFile

build_file_path = r"K:\build"

#DOUBLE CHECK TYPES BY DEFAULT
pretest_info = {'WR6.0': {'bounds':[125,185],'type_default':'M12','link':'V:\\Technology\\Product Build Specifications\\Component Tracking Docs\\6p0IAMC-HP_Tracking.xlsx'}, 
                'WR6.5': {'bounds':[110,170],'type_default':'M12','link':'V:\\Technology\\\Product Build Specifications\\Component Tracking Docs\\6p5IAMC-HP_Tracking.xlsx'}, 
                'WR8.0': {'bounds':[90,140],'type_default':'M12','link':'V:\\Technology\\Product Build Specifications\\Component Tracking Docs\\8p0IAMC-HP_Tracking.xlsx'}, 
                'WR8.6': {'bounds':[85,130],'type_default':'M9','link':'V:\\Technology\\Product Build Specifications\\Component Tracking Docs\\8p6IAMC-HP_Tracking.xlsx'}, 
                'WR9.0': {'bounds':[82,125],'type_default':'M9','link':'V:\\Technology\\Product Build Specifications\\Component Tracking Docs\\9p0IAMC-HP_Tracking.xlsx'}, 
                'WR10.0': {'bounds':[75,110],'type_default':'M6','link':'V:\\Technology\\Product Build Specifications\\Component Tracking Docs\\10IAMC-HP_Tracking.xlsx'},
                'WR12.0': {'bounds':[60,90],'type_default':'M6', 'link':'V:\\Technology\\Product Build Specifications\\Component Tracking Docs\\12IAMC-HP_Tracking.xlsx'}, 
                'WR13.0': {'bounds':[55,85],'type_default':'M6','link':'V:\\Technology\\Product Build Specifications\\Component Tracking Docs\\13IAMC_Tracking.xlsx'}, 
                'WR15.0': {'bounds':[50,75],'type_default':'M4','link':'V:\\Technology\\Product Build Specifications\\Component Tracking Docs\\15IAMC-HP_Tracking.xlsx'}}

def pretest():

    row_data = ['R4_B1-32','A','M3',530,'TF','07/26/2024',20240515,None,20.49,18.23,'Y','N','hello, this is a test','07/26/2025','W:\Test Data\pretesting KDH'],
    colm = ['Block', 'X', 'Type', 'I (mA)', 'Tech', 'Date Built', 'TSC Lot', 'Long pad?', 'Typical (Median)', 'Minimum', 'Part Good?', 'TSC Good?', 'Notes', 'Date Tested', 'Link to Data']
    df = pd.DataFrame(row_data, columns=colm)

    '''
    writer = pd.ExcelWriter("J:\Engineer Directories\KDH\programs\pretesting\9p0IAMC-HP_Tracking KDH Copy.xlsx", mode='a', if_sheet_exists='replace')
    with pd.ExcelWriter("J:\Engineer Directories\KDH\programs\pretesting\9p0IAMC-HP_Tracking KDH Copy.xlsx", engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, index=True, header=False, startrow=len(reader)+1)

    reader = pd.read_excel("J:\Engineer Directories\KDH\programs\pretesting\9p0IAMC-HP_Tracking KDH Copy.xlsx")
    print(reader)
    '''

def process_file(path, file_type, band, start, stop, build_header = None):
    #given a file type of .csv OR .dat return typical, minimum, date tested, link to data (path), and current if there
    #use start and stop bounds from wx fields passed in (cast as an int)

    data = readFile(path)

    if (file_type == "csv"): #this should work for python tests

        tpp = data['Source (dBm)']
        #calculate typical / minimum using bounds set by user
        start_freq = int(start)
        stop_freq = int(stop)

        #exclude data so that its "in band"
        inband_tpp = []
        
        for index, row in data.iterrows():
            if int(index) >= start_freq and int(index) <= stop_freq:
                tpp_val = row['Source (dBm)']
                inband_tpp.append(tpp_val)

        typical = round(statistics.median(inband_tpp), 2)
        minimum = round(min(inband_tpp), 2)
        #extract current from .csv file?
        current = None
        #date_tested, date_built, tech, block, pcb_rev, pcb_lot, tsc_lot = extract_info_main(build_header)
        if (build_header != None):
            return_dict = extract_info_main(headers = build_header)
        else:
            return_dict = {}
            print('please input a build file')
            #should add err messaging here as well
        return_dict['current RF off'], return_dict['min'], return_dict['typ'] = current, minimum, typical

        return return_dict

    elif (file_type == "dat"): #process .dat file
        header, data = load_data(path)
        column_labels = data.columns.values.tolist()
        column_labels = column_labels[1]
        column_labels = column_labels.split(":")

        typical, minimum, current = process_frequency_data(column_labels, data, band, start=int(start), stop=int(stop))

        #should turn the below lines into function

        # Extract date, tech, block, and PCB info
        headers = header.columns.values.tolist()
        return_dict = extract_info_main(headers)
        return_dict['current RF off'], return_dict['min'], return_dict['typ'] = current, minimum, typical
        
        return return_dict

def find_buildfile(parent,path):
    #assuming if taken in labview, build info will already be in header
	#will have to do some string manipulation 

    if ('.txt' in path): #assume this is a .txt build file
        #save build file into dataframe, every line in new row
        try:
            build_file = pd.read_fwf(path)
            headers = format_build_txt_file(build_file=build_file)
            flat_header = extract_info_main(headers)
            #return formatted build info
            return flat_header
        except FileNotFoundError as error:
            print("Can't find that build file")

    else: #if there is no build file in the text box already extract header information

        #in the case of .dat file we have the build info in the file, extract that and return
        if ('.dat' in path):
            #use DBE function to parse the dat file and return header info (build info)
            header, data = load_data(path)

            #serialize header information which has build info in it
            headers = header.columns.values.tolist()
            flat_header = ''.join(headers)

            return flat_header
        
        full_file = readFile(path, get_header=True)
        
        #lastly in the case of a .csv we do not have the build file, we must find it
        #access whatever is in the DUT field of pretested file to search for build file
        dut_string = full_file['header']['DUT']

        device_search = re.search('([vV][dD][iI]|WR)?[0-9]+\.[0-9][iI][aA][mM][cC][a-zA-Z0-9-]+[_ ][rR][1-9]+', dut_string)
        rev_search = re.search('[ _][rR][1-9]+', dut_string)
        block_num_search = re.search('[bB]?[0-9]+-[0-9]+[a-zA-Z]?', dut_string)

        #remove B from the block number (not in build file name)
        block_num_str = block_num_search.group(0).replace("B", "")

        #if no revision is found in device info prompt user
        if (rev_search == None):
            errMsg(parent, msg = 'Please enter rev # in the command prompt', prompt = 'Cannot find revision information')
            rev = int(input("Enter the revision: "))
            device_search = re.search('([vV][dD][iI]|WR)?[0-9]+\.[0-9][iI][aA][mM][cC][a-zA-Z0-9-]+', dut_string)
            device_search = device_search.group(0) + "_R" + str(rev)

        if ('R' in device_search.group(0)): #if Rev is already in the build file name, do nothing
            device_full = device_search.group(0).replace(" ", "_").replace("VDI", "")
            formatted_name = device_full + " " + block_num_str
        else:
            try:
                formatted_name = device_search.group(0) + " " + block_num_str
            except AttributeError as error: #if device_search has already been cast as a string
                formatted_name = device_search + " " + block_num_str

        #Format full build name
        build_path = build_file_path + r"\vdi" + formatted_name + r".txt"

        if (os.path.isfile(build_path)):
            build_file = pd.read_fwf(build_path)
            flat_header = format_build_txt_file(build_file=build_file)
            return flat_header
        else:
            print("Can't find a build file with this path " + str(build_path))
    '''
    example build file name: vdi10.0iamc-hp-m3_r4 2-150c
    
    two key elements: *vdi10.0iamc-hp-m3_r4* *2-150c*

    need to extract these from DUT field, combine parts if necessary then search for it in build folder

    example DUT field: VDI9.0IAMC-HP-M9 R5 B1-02C P0 80-130Ghz
    - need to combine the rev number with the part number
    - get rid of 'B'
    - find block number (1-02C)
    '''

def format_build_txt_file(build_file):
    #Takes in dataframe returned from read_fwf and reads each row into a singular string (flat header)

    colm_name = build_file.columns[0]
    flat_header = colm_name

    for index, row in build_file.iterrows():
        flat_header += (" " + str(row[colm_name]))

    return flat_header

def load_data(dat_filepath):
	try:
		header_dataframe = pd.read_table(dat_filepath, delimiter=',', nrows=0, header=0)
		df = pd.read_table(dat_filepath, skiprows=1, usecols=[0, 1, 2, 3], header=0, index_col=False)
		return header_dataframe, df
	except FileNotFoundError:
	    exit()

def process_frequency_data(column_labels, df, band, start, stop):
    #scales frequency and retrieves current with RF value, takes column labels from .dat file, and returns a bunch of values (after parsing file)
    #scaled_freq, power_dbm,power_in_band,freq_in_band,current

    #band stored like {'WR8.0':[90,140]}
    #start_freq = pretest_info[band]['bounds'][0]
    #stop_freq = pretest_info[band]['bounds'][1]
    start_freq = start
    stop_freq = stop

    #readFile already does multipliciation of .dat files by default do we don't need to scale
    freq_factor = int(column_labels[1].split()[0])
    freq_range = df.iloc[:, 0] * freq_factor
    #freq_range = df['Frequency (GHz)']
    power_mw = df.iloc[:, 1]
    
    mw2dbm = lambda x: 10 * np.log10(x)
    
    power_dbm=mw2dbm(power_mw)
    power_dbm=np.nan_to_num(power_dbm,nan=0.0) #why doesn't this work?
    power_in_band, freq_in_band, current = [], [], []
    for i in range(len(df)): #for i in range(# points)
        if (np.round(freq_range[i]) >= start_freq) and (np.round(freq_range[i]) <= stop_freq):
            power_in_band.append(power_dbm[i])
            freq_in_band.append(freq_range[i])

    typicalPower = round(float(np.median(power_in_band)),2)
    minPower = round(float(np.min(power_in_band)),2)
    
    current.append(np.min(df.iloc[:,2]))
    current.append(np.max(df.iloc[:,2]))
    current_max = int(1000*round(float(np.max(df.iloc[:,2])),3))
    
    return typicalPower,minPower,current_max

def extract_info_main(headers):
    headers_unchanged = headers
    #remove ; in headers string
    if (type(headers) is str):
        headers = headers_unchanged.replace(";", " ")
    flat_headers = ''.join(headers)

    #extract date information
    dates = extract_dates(flat_headers)
    date_tested = dates[len(dates)-1]
    date_built = dates[0]

    if (type(headers) is str): #the case for .dat and .txt files
        headers = list(headers.split(" "))

    #extract tech and block information
    tech = extract_tech(flat_headers)
    block_full = extract_block(flat_headers)
    block_full = block_full.replace(" ", "_")

    #extract block 'revision' - i.e. B
    block_x = block_full[-1]
    if (block_x.isdigit()): #if last character is a number set rev to A
        block_x = 'A'

    #extract pcb and tsc information
    pcb_rev, pcb_lot = extract_pcb_info(headers)
    tsc_lot = extract_tsc_lot_info(flat_headers,headers)
    blk_type = extract_type(flat_headers)

    return_dict = {}
    return_dict['date tested'], return_dict['date built'], return_dict['technician'], return_dict['block'], return_dict['block x']  = date_tested, date_built, tech, block_full, block_x
    return_dict['PCB rev'], return_dict['PCB lot'], return_dict['TSC lot'] = pcb_rev, pcb_lot, tsc_lot
    return_dict['type'] = blk_type

    return return_dict

def extract_type(flat_headers):
    #search for type if present in header string
    type_match = re.findall(r'-M[0-9]{1,2}', flat_headers, re.IGNORECASE)
    return type_match[0][1:len(type_match[0])] if type_match else ""

def extract_dates(flat_headers):
    date_match = re.findall(r'[0-9]+/[0-9]+/[0-9]+', flat_headers, re.IGNORECASE)
    date_match.sort() #sort from earliest to oldest dates found
    if date_match:
        return date_match
    else:
        return ""
    #return date_match[0] if date_match else "", date_match[1] if len(date_match) > 1 else "" #syntax didn't work like i thought??

def extract_tech(flat_headers):
    #search for initials in header string
    tech_match = re.findall(r'\s[a-z]{2,3}[ |/]', flat_headers, re.IGNORECASE)
    double_tech_match = re.findall(r'\s[a-z]{2,3}/[a-z]{2,3}\s', flat_headers, re.IGNORECASE)
    if double_tech_match:
        return double_tech_match[-1][1:len(double_tech_match[-1])-1]
    else:
        new_tech_match = [tech for tech in tech_match if (('TTL' not in tech) and ('SSP' not in tech) and ('SP' not in tech) and ('TSC' not in tech) and ('Per' not in tech) and ('nan' not in tech) and ('to' not in tech) and ('No' not in tech))]

        return new_tech_match[-1][1:len(new_tech_match[-1])] if new_tech_match else ""

def extract_rev(flat_headers):
    block_match = re.search(r'R[0-9]{1}(\s+)', flat_headers, re.IGNORECASE)
    return block_match.group(0) if block_match else ""

def extract_block(flat_headers):
    block_match = re.search(r'R[0-9]{1}(\s+)B?[0-9]{1}-[0-9]{2,3}([a-z]?)', flat_headers, re.IGNORECASE)
    return block_match.group(0) if block_match else ""

def extract_pcb_info(headers):
    pcb_rev, pcb_lot = "", ""
    indexes_pcb = [index for index, string in enumerate(headers) if (("pcb" in string.lower()) or ("pcbr*" in string.lower()))]
    if indexes_pcb:
        pcb_rev, pcb_lot = process_pcb_info(headers[indexes_pcb[0]])
    return pcb_rev, pcb_lot

def process_pcb_info(pcb_info):
    pcb_rev_tmp = pcb_info.lstrip().rstrip()
    rev_match = re.search(r'pcb\s*r\s*(\d+)', pcb_rev_tmp.lower())
    pcb_rev = rev_match.group(1) if rev_match else ""
    pcblot_match = re.search(r'(\d{8})', pcb_rev_tmp.lower())
    pcb_lot = pcblot_match.group(1) if pcblot_match else ""
    return pcb_rev, pcb_lot

def extract_tsc_lot_info(flat_headers,headers):
    indexes_tsc = [index for index, string in enumerate(headers) if ("tsc" in string.lower())]
    #indexes_tsc = [index for index, string in enumerate(headers) if "TSC" in string and( "lot" in string.lower())]
    if indexes_tsc:
        tsc_lot = headers[indexes_tsc[0]]
        tsc_lot = tsc_lot.lstrip()
        tsclot_match = re.search(r'[0-9]{8}',tsc_lot,re.IGNORECASE)
        if tsclot_match:
            tsc_lot = tsclot_match.group(0)
            return tsc_lot
    else:
        tsc_lot = ""
        return tsc_lot

    lotsearch = re.split(r'\w\w-\w\w\w\w-\w\w\w\w',flat_headers,re.IGNORECASE)
    if (len(lotsearch) > 1):
        lotsearch = lotsearch[1]
        lotmatch = re.search(r'(\s?)[0-9]{8}(\s?)',lotsearch,re.IGNORECASE)
        if lotmatch:
            tsc_lot = lotmatch.group(0)[1:len(lotmatch.group(0))]
            return tsc_lot

if __name__ == "__main__":
    pretest()