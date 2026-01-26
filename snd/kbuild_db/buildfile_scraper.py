import os
import time
import re
import pandas as pd

import datetime
from sql_models import Block, Build, SimpleBuild, Base, engine, SessionLocal

from sqlalchemy import select


def print_elapsed_time(old_time):
	print( (time.time_ns() - old_time)/1e9 )


def get_block_revision(input_string):
	#run either on a block engraving string, or a buildfile path
	block_revision = None

	underscore_location = input_string.rfind('_')
	if underscore_location == -1:
		#component_name = input_string
		pass
	else:
		block_revision = input_string[(underscore_location+1):]
		#component_name = input_string[:underscore_location]
		#print(block_revision)
		#example K:\build\vdi15.0swg-pl-10_1r5 8-01.txt
		#K:\build\vdi12.0swg-pl-10_1r7 4-124.txt
		if block_revision[0].isalpha:
			block_revision = block_revision[1:]

	#example: wr9.0x3yr2 2-15
	end_string_revision_regex = r'(r\d+$)'

	substrings = re.findall(end_string_revision_regex, input_string)
	if len(substrings) > 0:
		#input_string = input_string.rstrip(substrings[-1])
		block_revision = substrings[-1][1:]
		return block_revision

	#example K:\build\vdi2.2bc4p10-20_r4-x1 1-19.txt
	xn_revision_regex = r'(r\d+-x\d+$)'
	substrings = re.findall(xn_revision_regex, input_string)
	if len(substrings) > 0:
		#input_string = input_string.rstrip(substrings[-1])
		block_revision = substrings[-1].split('-')[0][1:]
		return block_revision

	#example K:/build/d320 1-70e.txt
	#block engraving: 320R4X2
	#avoid finding: WR8X2
	varactor_r4x2_regex = r'(\d+r\d+x\d$)'
	substrings = re.findall(varactor_r4x2_regex, input_string.lower())
	if len(substrings) > 0:
		numrx = substrings[-1].split('x')[0]
		block_revision = numrx.split('r')[-1]
		return block_revision

	return block_revision

def parse_build_filepath(build_filepath):
	build_name = None
	block_revision = None
	block_serial = None
	build_revision = None

	split_path = os.path.split(build_filepath)
	myfile = split_path[1]
	myfile = os.path.splitext(myfile)[0]

	#example: vdi3.4swg2-30_r6 3-15
	#example: vdiwr15.0amp-hp-0055_0072_r2 1-001

	component = myfile.split(' ')[0]
	block_serial = myfile.split(' ')[-1]

	block_revision = get_block_revision(component)

	build_name = component

	try:
		sn_last_char = block_serial.lower()[-1]
	except:
		print(block_serial)
		sn_last_char = '0'

	if sn_last_char.isalpha():
		build_revision = ord(sn_last_char)-96
		block_serial = block_serial[:-1]
	else:
		build_revision = 1

	return build_name, block_revision, block_serial, build_revision


def read_build_file(build_filepath):

	block_engraving = None
	initials = None
	build_date = None
	block_revision = None
	lines = []
	rstripped_lines = []

	try:
		with open(build_filepath) as f:
			lines = f.readlines()
			block_engraving = lines[0].split(' ')[0].rstrip('\n')
			initials = lines[8].rstrip('\n')
			block_revision = get_block_revision(block_engraving.lower())
	except:
		pass

	try:
		build_date_string = lines[9].rstrip('\n')
		build_date = datetime.datetime.strptime(build_date_string,'%m/%d/%Y').date()
	except:
		pass

	for line in lines:
		rstripped_lines.append(line.rstrip())
	try:
		rstripped_lines[1] = rstripped_lines[1].split(' ')[0]
	except:
		pass

	return block_engraving, block_revision, initials, build_date, rstripped_lines

def compare_revisions(block_revision_fromfile, block_revision_frompath):
	try:
		float(block_revision_fromfile)
		block_revision_fromfile_isfloat = True
	except:
		block_revision_fromfile_isfloat = False
	try:
		float(block_revision_frompath)
		block_revision_frompath_isfloat = True
	except:
		block_revision_frompath_isfloat = False

	if block_revision_fromfile_isfloat and block_revision_frompath_isfloat:
		if block_revision_fromfile == block_revision_frompath:
			return block_revision_fromfile
		else:
			#if they are both numeric but don't match leave it None
			return None
	elif block_revision_fromfile_isfloat:
		return block_revision_fromfile
	elif block_revision_frompath_isfloat:
		return block_revision_frompath
	elif not block_revision_frompath and not block_revision_fromfile:
		return 0
	else:
		#if both aren't numeric or None/0 leave it None
		return None

def add_build(build_filepath):
	
	block_engraving, block_revision_fromfile, initials, build_date, filerows = read_build_file(build_filepath)
	build_name, block_revision_frompath, block_serial, build_revision = parse_build_filepath(build_filepath)

	block_revision = compare_revisions(block_revision_fromfile, block_revision_frompath)

	#append extra strings to avoid index error
	extra_rows = ['']*30
	filerows = filerows+extra_rows

	with SessionLocal() as sess:

		q = sess.query(Block)
		q = q.filter(Block.block_engraving == block_engraving)\
					.filter(Block.block_revision == block_revision)\
					.filter(Block.block_serial == block_serial).all()

		if len(q) == 0:
			block_row = Block(
						block_engraving = block_engraving,
						block_revision_fromfile = block_revision_fromfile,
						block_revision_frompath = block_revision_frompath,
						block_revision = block_revision,
						block_serial = block_serial,
						)

			sess.add(block_row)
			sess.commit()

			q = sess.query(Block)
			q = q.filter(Block.block_engraving == block_engraving)\
					.filter(Block.block_revision == block_revision)\
					.filter(Block.block_serial == block_serial).all()

		block_id = q[0].ID

		build_row = Build(
					build_name = build_name,
					block_id = block_id,

					build_file_path = build_filepath,
					build_date = build_date,
					build_revision = build_revision,
					)
		try:
			sess.add(build_row)
			sess.commit()
		except:
			pass

		simplebuild_row = SimpleBuild(
					build_name = build_name,
					block_id = block_id,
					build_file_path = build_filepath,
					build_revision = build_revision,
					row1 = filerows[0],
					row2 = filerows[1],
					row3 = filerows[2],
					row4 = filerows[3],
					row5 = filerows[4],
					row6 = filerows[5],
					row7 = filerows[6],
					row8 = filerows[7],
					row9 = filerows[8],
					row10 = filerows[9],
					row11 = filerows[10],
					row12 = filerows[11],
					row13 = filerows[12],
					row14 = filerows[13],
					row15 = filerows[14],
					row16 = filerows[15],
					row17 = filerows[16],
					row18 = filerows[17],
					row19 = filerows[18],
					row20 = filerows[19],
					row21 = filerows[20],
					row22 = filerows[21],
					row23 = filerows[22],
					row24 = filerows[23],
					row25 = filerows[24],
					row26 = filerows[25],
					row27 = filerows[26],
					row28 = filerows[27],
					row29 = filerows[28],
					row30 = filerows[29],
			)

		try:
			sess.add(simplebuild_row)
			sess.commit()
		except:
			pass
		
def empty_db():
	metaobj = Base.metadata
	metaobj.drop_all(engine)
	metaobj.create_all(engine)

def get_kbuild_files():


	files = os.listdir(r'K:/build')

	return files

def rebuild_db(actually_do_this=False):
	if actually_do_this:
		start_time = time.time_ns()
		
		files = pd.read_csv('kdrive20260112.csv', index_col=0)['0']

		print_elapsed_time(start_time)

		empty_db()

		print_elapsed_time(start_time)


		for k in files:
			add_build(k)

		print_elapsed_time(start_time)

def try_parsing_date(input_string):
	try:
		build_date = datetime.datetime.strptime(input_string,'%m/%d/%Y').date()

		if build_date.year < 1950:
			build_date = None

	except:
		build_date = None
	return build_date

def cleanup_initials(input_string):
	try:
		output_string = input_string[:3]
	except:
		output_string = None
	return output_string

def update_db(days_before_now = 2):

	start_time = time.time_ns()

	files = os.listdir(r'K:/build')
	now = time.time()
	then = now - (days_before_now * (60 * 60 * 24))

	new_files = []
	print_elapsed_time(start_time)

	for k in files:
		mtime = os.path.getmtime(os.path.join(r'K:/build',k))
		if (mtime - then) > 0:
			new_files.append(k)
	print_elapsed_time(start_time)

	for k in new_files:
		add_build(os.path.join(r'K:/build',k))

	return new_files

def get_paths_from_db():
	sel = select(SimpleBuild.build_file_path)

	return pd.read_sql(sel, engine)

def find_new_paths():
	start_time = time.time_ns()
	#list
	files = get_kbuild_files()
	print_elapsed_time(start_time)
	#df
	paths = get_paths_from_db()
	print_elapsed_time(start_time)

	paths['split'] = paths['build_file_path'].apply(lambda x: os.path.split(x)[-1])
	print_elapsed_time(start_time)

	new_files = []
	for file in files:
		if file in paths['split'].values:
			pass
		else:
			new_files.append(file)
	print_elapsed_time(start_time)
	
	return new_files

if __name__ == '__main__':

	pass