import shutil
from snd.sql.test_explorer import TestExplorer

from sqlalchemy import select
from sqlalchemy.orm import Session

import datetime
import re


SSP_DB_FILE = "W:/durant/github/engineer/snd/sql/db/SSP_DB_copy.db"
SSP_DB_REF = "W:/durant/github/engineer/snd/sql/db/SSP_DB_ref.db"


def get_table_rows(test_explorer, table_name, primary_key):
    table_class = getattr(test_explorer, table_name)
    table_col = getattr(table_class, primary_key)

    sel = select(table_col, table_class)

    return test_explorer.executeSelect(sel)

def copy_row(ref_row, new_row, attrs):

    for at in attrs:
        setattr(new_row, at, getattr(ref_row, at))

def sync_table(ref_explorer,\
    cur_explorer,\
    table_name='system',\
    primary_key='SN',\
    attrs=['SN','Band','Type','Subtype','Arch']):

    new_rows = []

    ref_rows = get_table_rows(ref_explorer,table_name,primary_key)
    cur_rows = get_table_rows(cur_explorer,table_name,primary_key)

    a,b = zip(*ref_rows)
    c,d = zip(*cur_rows)

    new_row_ids = set(a) - set(c)

    ref_class = getattr(ref_explorer,table_name)
    ref_attr = getattr(ref_class,primary_key)

    for idx in new_row_ids:
        sel = select(ref_class).filter(ref_attr==idx)
        row = ref_explorer.executeSelect(sel)[0][0]

        new_row = getattr(cur_explorer,table_name)()
        copy_row(row, new_row, attrs)

        new_rows.append(new_row)

    return new_rows

def update_test_rows(rows):
    for row in rows:
        if "Short-Load" in row.test_name:
            row.test_type = "SL"

        try:
            sn = re.search(r'(VNAX\s+\d+)',row.test_name).group(1)
        except:
            #print(row[0].test_name)
            sn = ""
        row.sn = sn

    return rows

def populate_datetime_edited(rows):

    for row in rows:
        row.datetime_edited = datetime.datetime.strptime(row.Last_Edit,'%m/%d/%Y %H:%M:%S')

    return rows

def get_approved_testsets(rows):
    output = []

    for row in rows:
        if row.Approval==True:
            output.append(row.sn1,row.sn2)

    return output

def sync_approved_status(current_db, ref_db):
    newly_approved_rows = []

    ref_select = select(ref_db.testset.ID,ref_db.testset.Approval)
    cur_select = select(current_db.testset.ID,current_db.testset.Approval)

    ref_rows = ref_db.executeSelect(ref_select)
    cur_rows = current_db.executeSelect(cur_select)

    for a, b in zip(ref_rows, cur_rows):
        
        if a[1] != b[1]:
            print(f'{a[0]}, {b[0]} not equal')
            newly_approved_rows.append(b[0])

    return newly_approved_rows


def approve_testset_by_id(current_db, testsetid):

    sel = select(current_db.testset).filter(current_db.testset.ID == testsetid)
    row = current_db.executeSelect(sel)[0]
    row.Approval = True

    return (row.sn1, row.sn2)

def sync_database(current_db):
    #current_db is a TestExplorer

    #copy newest db to our reference dir
    shutil.copy(r'W:\Python3\vdi_ssp\sql\db\SSP_DB.db', SSP_DB_REF)

    ref_db = TestExplorer(db_file = SSP_DB_REF)

    new_system_rows = sync_table(ref_db, current_db, 'system',\
        'SN', ['SN','Band','Type','Subtype','Arch'] )
    new_testset_rows = sync_table(ref_db, current_db, 'testset',\
        'ID', ['ID','SN1','SN2','rev','Order','Customer','Engineer','Last_Edit','Approval','Comments','Deleted'] )
    new_test_rows = sync_table(ref_db, current_db, 'test',\
        'testsetID', ['testsetID','test_name','file','minimum_spec','min_typ_spec','max_typ_spec','maximum_spec','test_type'] )

    update_test_rows(new_test_rows)
    populate_datetime_edited(new_testset_rows)
    #get a list of SN1, SN2 for new approved testsets
    approved_testsets = get_approved_testsets(new_testset_rows)

    with Session(current_db.engine) as sess:
        sess.add_all(new_system_rows)
        sess.add_all(new_testset_rows)
        sess.add_all(new_test_rows)

        sess.commit()

    testset_ids_to_approve = sync_approved_status(current_db, ref_db)
    for j in testset_ids_to_approve:
        #loop through these testset ids, approve them, and add sn1/sn2 to the list
        sn1,sn2 = approve_testset_by_id(current_db, j)

        approved_testsets.append((sn1,sn2))

    approved_tests = current_db.find_approved_tests(approved_testsets)
    current_db.set_approved_tests(approved_tests, 1)



if __name__ == '__main__':

    curdb = TestExplorer(db_file = SSP_DB_FILE)
    refdb = TestExplorer(db_file = SSP_DB_REF)

    sync_approved_status(curdb, refdb)