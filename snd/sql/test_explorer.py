from sqlalchemy import select, tuple_, func, text, create_engine
from sqlalchemy.orm import Session
from .SQLHelper import SQLHelper
from .FileReader import readFile
from .calamine_helper import read_plhrm_xlsx_with_calamine, read_j10_xlsx_with_calamine

import datetime
import plotly.express as px
import pandas as pd
import re
import numpy as np
import shutil

SSP_DB_FILE = "W:/durant/github/engineer/snd/sql/db/SSP_DB_copy.db"
SSP_DB_REF = "W:/durant/github/engineer/snd/sql/db/SSP_DB_ref.db"


COLOR_SCHEME = ['#000000']+px.colors.qualitative.Plotly


def line(data, **kwargs):
    return px.line(data, \
        color_discrete_sequence=COLOR_SCHEME,\
        height=800,
        **kwargs)

class TestExplorer(SQLHelper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.define_classes()

    def update_database(self):

        # #close old connection

        # self.engine.dispose()

        # #copy the db file on the network
        # shutil.copy(r'W:\Python3\vdi_ssp\sql\db\SSP_DB.db', SSP_DB_FILE)

        # #reconnect to the new file
        # self.connect_db()

        # #add the new columns
        # self.add_columns()
        # #redefine classes in case we added columns
        # self.define_classes()

        print("Populating test.test_type column for Short-Loads")
        self.rename_shortloads()

        print("Populating test.sn column for TPP,SL,PL,PLHRM")
        self.populate_test_sn_field()

        print("Populating testset.datetime_edited column")
        self.update_testsets_to_datetime()
        tests_to_update = self.find_all_approved_tests(0)

        print("Populating test.approved column")
        self.set_approved_tests(tests_to_update, 1)

    def add_columns(self):

        #add approved column for test table
        with self.engine.connect() as connection:
            connection.execute(text('alter table test add column approved integer'))
            connection.execute(text('alter table test add column sn text'))
            connection.execute(text('alter table testset add column datetime_edited datetime'))

    def define_classes(self, table_names = ['test','testset','system']):

        #after running this function
        #self.test = <class> sqlalchemy.ext.automap.test
        #etc

        all_classes = self.get_automap_classes()

        for c in all_classes:
            for t in table_names:
                if c.__table__.name == t:
                    setattr(self,t,c)

    def set_approved_tests(self, test_ids = [], approved_status=1):
        #test_ids - list of (test.test_name, testset.ID)

        sel = select(self.test)\
        .join(self.testset)\
        .filter(tuple_(self.test.test_name,self.testset.ID).in_(test_ids))

        with Session(self.engine) as sess:

            rows_to_update = sess.execute(sel).all()
            for row in rows_to_update:
                row[0].approved = approved_status
            sess.commit()

        return rows_to_update

    def update_testsets_to_datetime(self):

        sel = select(self.testset)

        with Session(self.engine) as sess:
            rows_to_update = sess.execute(sel).all()
            #print(len(rows_to_update))

            for row in rows_to_update:
                row[0].datetime_edited = datetime.datetime.strptime(row[0].Last_Edit,'%m/%d/%Y %H:%M:%S')
                #print(row[0].datetime_edited)

            sess.commit()

    def rename_shortloads(self):
        #changes short-load tests to have test_type of "SL"

        sel = select(self.test).filter(self.test.test_name.contains("Short-Load"))

        with Session(self.engine) as sess:

            rows_to_update = sess.execute(sel).all()
            for row in rows_to_update:
                row[0].test_type = "SL"
            sess.commit()

    def populate_test_sn_field(self):
        #add SN column for TPP, SL, PLHRM
        sel1 = select(self.test).filter(self.test.test_type=="TPP")
        sel2 = select(self.test).filter(self.test.test_type=="SL")
        sel3 = select(self.test).filter(self.test.test_type=="PLHRM")
        sel4 = select(self.test).filter(self.test.test_type=="PL")

        with Session(self.engine) as sess:

            rows_to_update = sess.execute(sel1).all() + sess.execute(sel2).all() + sess.execute(sel3).all() + sess.execute(sel4).all()
            for row in rows_to_update:
                try:
                    sn = re.search(r'(VNAX\s+\d+)',row[0].test_name).group(1)
                except:
                    #print(row[0].test_name)
                    sn = ""
                row[0].sn = sn

            sess.commit()

    def get_revs_from_sn(self, sn1, sn2=None):

        if sn2 == 'None':
            sn2 = None
        revs = select(self.testset.rev)\
            .filter(self.testset.SN1==sn1)\
            .filter(self.testset.SN2==sn2)\

        return self.executeSelect(revs)

    def newest_tests_from_sns(self, sn1, sn2=None):
        #I guess technically to find 1-port systems, sn2 has to be None
        #but it may have to be the string "None"

        approved_tests = select(self.test.test_name,\
                            self.testset.ID,\
                            func.row_number()\
                               .over(
                                    partition_by=self.test.test_name,
                                    order_by=self.testset.rev.desc()
                                    ).label("row_num"))\
        .join(self.testset)\
        .filter(self.testset.SN1==sn1)\
        .filter(self.testset.SN2==sn2)\
        .subquery()
        
        newest_tests = select(approved_tests)\
            .where(approved_tests.c.row_num == 1)
        
        return self.executeSelect(newest_tests)

    def find_approved_tests(self, sn_tuples):
        payload_tuples = []

        for sn1, sn2 in sn_tuples:
            temp = self.newest_tests_from_sns(sn1,sn2)
            for test in temp:
                payload_tuples.append((test[0],test[1]))

        return payload_tuples

    def find_all_approved_tests(self, number_of_testsets=10):
        #if number_of_testsets is 0, it will run on all test sets
        #returns a list of tuples of all tests comprising the most recently
        #approved rev for each testset
        #[(test.test_name, testset.ID), ...]
        #this is a uniqueID for the test table
    
        #get all approved test sets
        approved_sets = select(self.testset.SN1,self.testset.SN2)\
            .filter(self.testset.Approval==True)\
            .order_by(self.testset.rev.desc())
        
        #only get the newest revision of each 
        newest = approved_sets.distinct()
        rows = self.executeSelect(newest)
        sn1 = rows[0][0]
        sn2 = rows[0][1]
        
        #get all approved tests associated with one serial number combination
        #sorted descending by testset revision
        payload_tuples = []
        
        if number_of_testsets:
            rows = rows[:number_of_testsets]
        
        for sn1, sn2 in rows:
            
            temp = self.newest_tests_from_sns(sn1,sn2)
            for test in temp:
                payload_tuples.append((test[0],test[1]))
            
        return payload_tuples

    def get_attributes_from_sn(self, serial_number, serial_number2=None ,echo=False):
    #need to check system table for Band, Type, Arch, Subtype
        sel1 = select(self.system).filter(self.system.SN==serial_number)
        q = self.executeSelect(sel1)
        if serial_number2:
            sel2 = select(self.system).filter(self.system.SN==serial_number2)
            q2 = self.executeSelect(sel2)

        my_band = q[0][0].Band
        my_type = q[0][0].Type
        my_arch = q[0][0].Arch
        my_subtype = q[0][0].Subtype

        if serial_number2:
            my_arch = q[0][0].Arch
        
        if echo:
            print(f'band: {my_band}')
            print(f'type: {my_type}')
            print(f'arch: {my_arch}')
            print(f'subtype: {my_subtype}')
        
        return my_band, my_type, my_arch, my_subtype

    def get_similar_tests(self, sn1, rev, test_name, sn2=None, approved_only=True, match_subtype=False):
        my_band, my_type, my_arch, my_subtype = self.get_attributes_from_sn(sn1)

        sel0 = select(self.test.file,self.testset.SN1)\
            .join(self.testset)\
            .filter(self.test.test_name==test_name)\
            .filter(self.testset.SN1==sn1)\
            .filter(self.testset.rev==rev)\

        if sn2:
            sel0b = select(self.test.file,self.testset.SN2)\
            .join(self.testset)\
            .filter(self.test.test_name==test_name)\
            .filter(self.testset.SN2==sn2)\
            .filter(self.testset.rev==rev)\

        #pull all tests matching band and type
        #but not this one
        sel1 = select(self.test.file,self.testset.SN1)\
            .join(self.testset)\
            .join(self.system,self.testset.SN1==self.system.SN)\
            .filter(self.system.Band == my_band)\
            .filter(self.system.Type == my_type)\
            .filter(self.test.test_name==test_name)\
            .filter(self.testset.SN1!=sn1)\
            .order_by(self.testset.datetime_edited.desc())
            

        if match_subtype:
            sel1 = sel1.filter(self.system.Subtype == my_subtype)

        if approved_only:
            sel1 = sel1.filter(self.test.approved == True)


        data0 = self.executeSelect(sel0)

        if len(data0) == 0:
            return []

        if sn2:
            output = data0 + self.executeSelect(sel0b) + self.executeSelect(sel1)
        else:
            output = data0 + self.executeSelect(sel1)
        
        return output

    def get_all_tests(self, sn1, rev, test_name, sn2=None):
        sel = select(self.test.file, self.testset.rev)\
            .join(self.testset)\
            .filter(self.test.test_name==test_name)\
            .filter(self.testset.SN1==sn1)\
            .order_by(self.testset.rev.desc())

        if sn2:
            sel1 = select(self.test.file,self.testset.rev)\
            .join(self.testset)\
            .filter(self.test.test_name==test_name)\
            .filter(self.testset.SN2==sn2)\
            .order_by(self.testset.rev.desc())

            return self.executeSelect(sel) + self.executeSelect(sel1)

        else:

            return self.executeSelect(sel)


    def get_similar_test_type(self, sn1, rev, test_type, approved_only=True, match_subtype=False, sn2=None):
        my_band, my_type, my_arch, my_subtype = self.get_attributes_from_sn(sn1)

        sel0 = select(self.test.file,self.test.sn)\
            .join(self.testset)\
            .filter(self.test.test_type==test_type)\
            .filter(self.test.sn==sn1)\
            .filter(self.testset.rev==rev)\

        if sn2:
            sel0b = select(self.test.file,self.test.sn)\
            .join(self.testset)\
            .filter(self.test.test_type==test_type)\
            .filter(self.test.sn==sn2)\
            .filter(self.testset.rev==rev)\

        #pull all tests matching band and type
        sel1 = select(self.test.file,self.testset.SN1)\
            .join(self.testset)\
            .join(self.system,self.testset.SN1==self.system.SN)\
            .filter(self.system.Band == my_band)\
            .filter(self.system.Type == my_type)\
            .filter(self.test.test_type==test_type)\
            .filter(self.testset.SN1!=sn1)\
            .order_by(self.testset.datetime_edited.desc())

        if match_subtype:
            sel1 = sel1.filter(self.system.Subtype == my_subtype)

        if approved_only:
            sel1 = sel1.filter(self.test.approved == True)

        data0 = self.executeSelect(sel0)

        if len(data0) == 0:
            return []

        if sn2:
            output = data0 + self.executeSelect(sel0b) + self.executeSelect(sel1)
        else:
            output = data0 + self.executeSelect(sel1)

        return output
    
    def get_all_tests_of_type(self, sn1, rev, test_type, sn2=None):
        sel = select(self.test.file, self.testset.rev)\
            .join(self.testset)\
            .filter(self.test.test_type==test_type)\
            .filter(self.test.sn==sn1)\
            .order_by(self.testset.rev.desc())

        if sn2:
            sel1 = select(self.test.file,self.testset.rev)\
            .join(self.testset)\
            .filter(self.test.test_type==test_type)\
            .filter(self.test.sn==sn2)\
            .order_by(self.testset.rev.desc())

            return self.executeSelect(sel) + self.executeSelect(sel1)

        else:

            return self.executeSelect(sel)
    def get_similar_systems(self, serial_number, match_arch=True, match_subtype=False, approved_only=True, echo=False):
        
        my_band, my_type, my_arch, my_subtype = self.get_attributes_from_sn(serial_number, echo=echo)
        
        #need to pull testsets to get Approval
        sel1 = select(self.system, self.testset).join(self.testset,self.testset.SN1==self.system.SN)
        sel1=sel1.filter(self.system.Type==my_type)
        sel1=sel1.filter(self.system.Band==my_band)
        
        if approved_only:
            sel1=sel1.filter(self.testset.Approval==True)
        if match_arch:
            sel1=sel1.filter(self.system.Arch==my_arch)
        if match_subtype:
            sel1=sel1.filter(self.system.Subtype==my_subtype)
            
        return self.executeSelect(sel1)

    def process_j10(self, data, num_comparisons):
        df_list=[]

        if not data:
            return px.scatter(title='Calibrated J10')
        
        for j in data[:num_comparisons+1]:
            #use calamine to read only the xj10 page
            system_df = read_j10_xlsx_with_calamine(j[0])
            try:

                out_df = system_df.pop('S21(dB)').to_frame()
                out_df['S12(dB)'] = system_df['S12(dB)']
                out_df['serial_number'] = j[1]
                out_df = out_df.reset_index()
                out_df = out_df.melt(id_vars=['Frequency(GHz)','serial_number'],\
                    var_name='trace_name',value_name='db')
                out_df.index=out_df.pop('Frequency(GHz)')

                df_list.append(out_df)
            except:
                pass

        dfs = pd.concat(df_list)

        return line(dfs,x=dfs.index,y='db',\
            color='serial_number',facet_col='trace_name',\
            title='Calibrated J10')

    def process_harmonics(self, data, num_comparisons):
        #data is a sql Row object [(filepath, serial_number), ...]
        #slider for the harmonic number
        if not data:
            return px.scatter(title='Harmonics Plot')

        df_list=[]
        for j in data[:num_comparisons+1]:
            temp = readFile(j[0]).reset_index()

            temp['serial_number']=j[1]
            temp = temp.melt(id_vars=['Frequency (GHz)','serial_number'],var_name='harmonic#',value_name='dbc')
            df_list.append(temp)

        dfs = pd.concat(df_list)
        dfs = dfs.dropna()
        xmin = dfs['Frequency (GHz)'].min()
        xmax = dfs['Frequency (GHz)'].max()

        return line(dfs,x='Frequency (GHz)',y='dbc',color='serial_number',
            animation_frame='harmonic#',
            range_x=[xmin,xmax],
            range_y=[-100,0],
            title='Harmonics Plot')

    def process_cl(self, data, num_comparisons, name='Mixer Conversion Loss'):
        #slider for HD vs LD
        if not data:
            return px.scatter(title=name)

        df_list = []
        for j in data[:num_comparisons+1]:
            temp = readFile(j[0])
            temp['serial_number']=j[1]
            df_list.append(temp)

        dfs = pd.concat(df_list)
        #dfs.to_csv('test.csv')
        return line(dfs,color='serial_number',markers=True, title=name)

    def process_current(self, data, num_comparisons):
        #slider for HD vs LD
        if not data:
            return px.scatter(title='Current')

        df_list = []
        for j in data[:num_comparisons+1]:
            temp = readFile(j[0])
            temp['serial_number']=j[1]
            df_list.append(temp)

        dfs = pd.concat(df_list)
        #dfs.to_csv('test.csv')
        return line(dfs,color='serial_number',markers=True, title='Current')

    def process_ifbw(self, data, num_comparisons):
        #slider for HD vs LD
        if not data:
            return px.scatter(title='IFBW Sweep')

        df_list = []
        for j in data[:num_comparisons+1]:
            temp = readFile(j[0])
            output = temp.pop('mixer cl').to_frame()
            output['serial_number']=j[1]
            df_list.append(output)

        dfs = pd.concat(df_list)
        #dfs.to_csv('test.csv')
        return line(dfs,color='serial_number',markers=True, title='IFBW Sweep')

    def process_shortload(self, data, num_comparisons):
        #slider for HD vs LD
        if not data:
            return px.scatter(title='Short Load')

        df_list = []
        for j in data[:num_comparisons+1]:
            temp = readFile(j[0])
            temp = temp.drop('S11(deg)',axis=1)
            if len(j[1])==1:
                sn=j[1]
            else:
                sn = re.search(r'\((\w+\s+\d+)\)',j[0]).group(1)
            temp['serial_number']=sn
            df_list.append(temp)

        dfs = pd.concat(df_list)
        return line(dfs,color='serial_number', markers=True,title='Short Load')

    def process_vnax_tpp(self, data, num_comparisons):

        if not data:
            return px.scatter(title='Test Port Power')

        df_list = []
        for j in data[:num_comparisons+1]:
            temp = readFile(j[0])
            dbm_df = temp.pop('Source (dBm)').to_frame().dropna()
            if len(j[1])==1:
                sn=j[1]
            else:
                sn = re.search(r'\((\w+\s+\d+)\)',j[0]).group(1)
            dbm_df['serial_number']=sn
            df_list.append(dbm_df)

        dfs = pd.concat(df_list)
        return line(dfs,color='serial_number',markers=True, title='Test Port Power')

    def process_tpp(self, data, num_comparisons):
        if not data:
            return px.scatter(title='Test Port Power')

        df_list = []
        for j in data[:num_comparisons+1]:
            temp = readFile(j[0])
            temp['serial_number']=j[1]
            df_list.append(temp)

        dfs = pd.concat(df_list)
        return line(dfs,color='serial_number',markers=True, title='Test Port Power')


    def df_thinner(self, df, bins=11):
        counts, bins = np.histogram(df.index,bins=bins);

        med = np.median(counts)
        output_dfs = []

        for j in range(len(counts)):
            current_count = counts[j]
            thinning_factor = int(current_count/med)
            subdf = df[df.index>=bins[j]]
            subsubdf = subdf[subdf.index<=bins[j+1]]
            if thinning_factor>1:
            
                output_dfs.append(subsubdf.iloc[1::thinning_factor])

            else:
                output_dfs.append(subsubdf)

        dfs_out = pd.concat(output_dfs)
        return dfs_out

    def process_plhrm(self, data, num_comparisons, speed_factor=5, bins=21):


        # df_list = []
        melted_dfs = []
        data = [k for k in data if 'html' not in k[0]]

        if not data:
            return px.scatter(title='Powerleveling Harmonics')

        for j in data[:num_comparisons+1]:
            systemdf = read_plhrm_xlsx_with_calamine(j[0],speed_factor)

            #find maintone
            maintone=int(systemdf.drop('input_power',axis=1).mean().idxmax())
            #make main tone power the index
            systemdf['Frequency']=systemdf.index
            systemdf.index=systemdf[maintone]
            dbcs_df = pd.DataFrame()
            #convert to dbc
            for c in systemdf.columns:
                if c !='input_power':
                    if c !='Frequency':
                        dbcs_df[c] = systemdf[c]-systemdf[maintone]


            #drop maintone and input power and find max
            dbcs_df['Frequency']=systemdf['Frequency']
            # worst_dbc = dbcs_df.drop([maintone],axis=1).max(axis=1)
            #melt for outputting
            melted = dbcs_df.drop(maintone,axis=1).reset_index().melt(id_vars=[maintone,'Frequency']).dropna()
            melted.index=melted[maintone]
            melted = melted.drop(maintone,axis=1)
            melted['serial_number']=j[1]
            melted=melted[melted.index>-40]

            # output = pd.DataFrame()
            # output['Frequency']=systemdf['Frequency']
            # output['max_dbc'] = worst_dbc
            # output['serial_number']=j[1]
            # output['input_power']=systemdf['input_power']
            #systemdf['serial_number']=j[1]
            # df_list.append(output)
            melted_dfs.append(melted)

        # uberdf = pd.concat(df_list)
        melts = pd.concat(melted_dfs)
        melts = self.df_thinner(melts, bins)
        # melts = melts.iloc[1::speed_factor]

        rangemin=min(melted['Frequency'])
        rangemax=max(melted['Frequency'])

        return px.scatter(melts,x=melts.index,y='value',
            color='Frequency',facet_col='serial_number',
            animation_frame='variable', range_color=[rangemin,rangemax],\
            range_y=[-80,0],\
            height=800,\
            title='Powerleveling Harmonics')

    def generate_mixamci_approval_plots(self, serial_number, rev, match_subtype=True,num_comparisons=5):
        #Test Names
        current_name = "Current Sweep"
        ifbw_name = "IF Bandwidth"
        cl_name = "Conversion Loss (Post RT)"
        cl_name_si = "Conversion Loss (Post SI)"
        harmonics_name = "(LO) Harmonics"

        current_data = self.get_similar_tests(serial_number,\
            rev, current_name,\
            match_subtype=match_subtype)

        ifbw_data = self.get_similar_tests(serial_number,\
            rev, ifbw_name,\
            match_subtype=match_subtype)

        cl_data = self.get_similar_tests(serial_number,\
            rev, cl_name,\
            match_subtype=match_subtype)

        cl_data_si = self.get_similar_tests(serial_number,\
            rev, cl_name_si,\
            match_subtype=match_subtype)

        harmonics_data = self.get_similar_tests(serial_number,\
            rev, harmonics_name,\
            match_subtype=match_subtype)

        return self.process_cl(cl_data,num_comparisons,'Post RT Conversion Loss'),\
            self.process_cl(cl_data_si,num_comparisons,'Post SI Conversion Loss'),\
            self.process_current(current_data,num_comparisons),\
            self.process_ifbw(ifbw_data,num_comparisons),\
            self.process_harmonics(harmonics_data,num_comparisons)

    def generate_sax_approval_plots(self, serial_number='SAX 123', \
        rev='a', match_subtype=True, low_drive=True,num_comparisons=5):

        if low_drive:
            cl_test_name = '(Low Drive) Mixer Conversion Loss'
            hrm_test_name = '(Low Drive) Harmonics'
        else:
            cl_test_name = '(High Drive) Mixer Conversion Loss'
            hrm_test_name = '(High Drive) Harmonics'

        cl_data = self.get_similar_tests(serial_number,\
            rev, cl_test_name,\
            match_subtype=match_subtype)

        hrm_data = self.get_similar_tests(serial_number,\
            rev, hrm_test_name,\
            match_subtype=match_subtype)

        return self.process_cl(cl_data,num_comparisons), \
        self.process_harmonics(hrm_data,num_comparisons)

    def generate_cc_approval_plots(self, serial_number,rev,match_subtype,num_comparisons):
        cl_test_name = 'Optimal Mixer Conversion Loss'
        hrm_test_name = 'Mixer Harmonics'

        cl_data = self.get_similar_tests(serial_number,\
            rev, cl_test_name,\
            match_subtype=match_subtype)

        hrm_data = self.get_similar_tests(serial_number,\
            rev, hrm_test_name,\
            match_subtype=match_subtype)

        return self.process_cl(cl_data,num_comparisons), \
        self.process_harmonics(hrm_data,num_comparisons)
        

    def generate_sgx_approval_plots(self, serial_number='SGX 123', \
        rev='a', match_subtype=True, low_drive=True, num_comparisons=5):

        if low_drive:
            tpp_test_name = '(Low Drive) Test Port Power'
            hrm_test_name = '(Low Drive) Harmonics'
        else:
            tpp_test_name = '(High Drive) Test Port Power'
            hrm_test_name = '(High Drive) Harmonics'

        tpp_data = self.get_similar_tests(serial_number,\
            rev, tpp_test_name,\
            match_subtype=match_subtype)

        hrm_data = self.get_similar_tests(serial_number,\
            rev, hrm_test_name,\
            match_subtype=match_subtype)

        return self.process_tpp(tpp_data,num_comparisons), \
        self.process_harmonics(hrm_data,num_comparisons)

    def generate_vnax_approval_plots(self, serial_number='VNAX 123',
        serial_number2='VNAX 124',rev='a', match_subtype=False, num_comparisons=5):

        shortload_data = self.get_similar_test_type(serial_number, rev, 'SL', sn2=serial_number2)

        plh_data = self.get_similar_test_type(serial_number, rev, 'PLHRM', sn2=serial_number2)
        #plh left plot only
        #tpp
        tpp_data = self.get_similar_test_type(serial_number,\
            rev, 'TPP',\
            match_subtype=match_subtype,\
            sn2=serial_number2)
        #calibrated j10

        trl_cal_data = self.get_similar_tests(serial_number, rev, 'TRL',\
            sn2=serial_number2)
        solt_cal_data = self.get_similar_tests(serial_number, rev, 'SOLT',\
            sn2=serial_number2)

        #just go with whichever had more results
        if len(trl_cal_data) > len(solt_cal_data):
            cal_data = trl_cal_data
        else:
            cal_data = solt_cal_data

        return self.process_shortload(shortload_data,num_comparisons),\
        self.process_plhrm(plh_data,5),\
        self.process_vnax_tpp(tpp_data,num_comparisons),\
        self.process_j10(cal_data,num_comparisons)

    def generate_demo_approval_plots(self, serial_number='VNAX 3437',\
        serial_number2='VNAX 3438',rev='a',num_comparisons=5):

        shortload_data = self.get_all_tests_of_type(serial_number, rev, 'SL', sn2=serial_number2)
        plh_data = self.get_all_tests_of_type(serial_number, rev, 'PLHRM', sn2=serial_number2)
        tpp_data = self.get_all_tests_of_type(serial_number, rev, 'TPP', sn2=serial_number2)

        trl_cal_data = self.get_all_tests(serial_number, rev, 'TRL')
        solt_cal_data = self.get_all_tests(serial_number, rev, 'SOLT')

        if len(trl_cal_data) > len(solt_cal_data):
            cal_data = trl_cal_data
        else:
            cal_data = solt_cal_data

        return self.process_shortload(shortload_data,num_comparisons),\
        self.process_plhrm(plh_data,5),\
        self.process_vnax_tpp(tpp_data,num_comparisons),\
        self.process_j10(cal_data,num_comparisons)

    def generate_approval_plots(self, serial_number,
    serial_number2=None,
    rev='a',
    match_subtype=True,
    low_drive=True,
    num_comparisons=5):

        if 'SGX' in serial_number:
            return self.generate_sgx_approval_plots(serial_number,rev,match_subtype,low_drive,num_comparisons)
        elif 'SAX' in serial_number:
            return self.generate_sax_approval_plots(serial_number,rev,match_subtype,low_drive,num_comparisons)
        elif 'VNAX' in serial_number:
            return self.generate_vnax_approval_plots(serial_number,serial_number2,rev,match_subtype,num_comparisons)
        elif 'SHM-I' in serial_number:
            return self.generate_mixamci_approval_plots(serial_number,rev,match_subtype,num_comparisons)
        elif 'CC' in serial_number:
            return self.generate_cc_approval_plots(serial_number,rev,match_subtype,num_comparisons)

    def get_test_count(self):

        sel1 = select(self.test)
        data = self.executeSelect(sel1)
        return len(data)

    def get_newest_testsets(self, system_types=['VNAX','SGX','SAX','CCU','CCD'], num_sets=5):

        output = {}

        all_testsets = select(self.testset)\
            .join(self.system,self.testset.SN1==self.system.SN)

        for system in system_types:
            sel = all_testsets.filter(self.system.Type==system)\
                .order_by(self.testset.datetime_edited.desc())\
                .limit(num_sets)

            #print("Query SQL is: " + str(sel))
            with self.engine.connect() as connection:
                df = pd.read_sql(sel, connection)

                output[system]=df.to_html()

        return output