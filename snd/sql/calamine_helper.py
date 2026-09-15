from python_calamine import CalamineWorkbook
import pandas as pd
import numpy as np

def read_plhrm_xlsx_with_calamine(filename, speed_factor):
    workbook = CalamineWorkbook.from_path(filename)
    sheet_names = workbook.sheet_names

    dfs = []

    my_range = np.arange(1,len(sheet_names)-1,speed_factor)

    for j in my_range:
        #this imports with 0-XXXX index on both row and columns
        sheet = workbook.get_sheet_by_index(j)
        df = pd.DataFrame(sheet.to_python())

        #replace blanks with NAN
        df = df.replace('', pd.NA)
        
        #first rename all the columns to the first row
        df.columns = df.iloc[0]

        #then drop the line of headers
        df = df.drop(index=0)

        #rename the columns to get rid of the extra '0'
        df.columns.name = None

        #reset the index
        df = df.set_index(df.columns[0])

        df['input_power']=float(sheet.name)
        dfs.append(df)

    try:
        return pd.concat(dfs)
    except:
        print(f'fail to load plhrm file: {filename}')
        return []

def read_j10_xlsx_with_calamine(filename):
    workbook = CalamineWorkbook.from_path(filename)

    sheet_names = workbook.sheet_names

    if 'xj10' in sheet_names:
        sheet = workbook.get_sheet_by_name('xj10')
        df = pd.DataFrame(sheet.to_python())

        #replace blanks with NAN
        df = df.replace('', pd.NA)
        
        #first rename all the columns to the first row
        df.columns = df.iloc[0]

        #then drop the line of headers
        df = df.drop(index=0)

        #rename the columns to get rid of the extra '0'
        df.columns.name = None

        #reset the index
        df = df.set_index(df.columns[0])
        df.index.name='Frequency(GHz)'

        return df

    return None