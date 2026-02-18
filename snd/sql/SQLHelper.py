from sqlalchemy import create_engine, select, inspect
from sqlalchemy.orm import sessionmaker, scoped_session, Session, declarative_base
from sqlalchemy.ext.automap import automap_base

import pandas as pd

import sys

SSP_DB_FILE = "W:/durant/github/vdi_ssp/sql/db/SSP_DB_copy.db"
SSP_DB_DATA_DIR = "W:/Python3/vdi_ssp/sql/db/files"

class SQLHelper:

	def __init__(self):

		self.engine = create_engine("sqlite:///" + SSP_DB_FILE, echo=False)
		SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
		self.Base = declarative_base()
		self.db = scoped_session(SessionLocal)

		self.meta_counter = 0
		#a dict of metadata to return
		self.meta = {}

		#a list of tuples
		self.filter_tuples = []

	def get_table_names(self):
		inspector = inspect(self.engine)
		return inspector.get_table_names()

	def get_columns_from_table_name(self, table_name):
		inspector = inspect(self.engine)
		return inspector.get_columns(table_name)

	def get_automap_classes(self):
		Base = automap_base()
		Base.prepare(autoload_with=self.engine)

		self.autobase = Base

		return list(self.autobase.classes)

	def get_columns(self, automapped_class):
		mapper = inspect(automapped_class)

		return list(mapper.columns)

	def get_instance_columns(self, instance_of_class):
		mapper = inspect(instance_of_class).mapper
		col_objs = list(mapper.columns)

		column_keys = []

		for ob in col_objs:
			column_keys.append(ob.key)

		return column_keys

	def getSelect(self, automapped_class):

		sel = select(automapped_class)
		return sel

	def load_filters_from_csv(self, filepath):
		df = pd.read_csv(filepath)

		self.filter_tuples = []

		for index, row in df.iterrows():
			filter_class = row['class']
			filter_variable = row['variable']
			filter_value = row['value']
			if row['exact']:
				filter_operator = 'equals'
			else:
				filter_operator = 'like'

			fclass_obj = getattr(sys.modules[__name__],filter_class)
			fvar_obj = fclass_obj.__dict__[filter_variable]

			self.filter_tuples.append((fvar_obj, filter_value, filter_operator))

	def addFilter(self, filter_target, filter_value, filter_operator='equals'):
		''' 
		filter_operator can be 'equals' or 'like'
		'''
		self.filter_tuples.append( (filter_target, filter_value, filter_operator) )

	def getMetaData(self):
		return self.meta

	def getFilters(self):
		return self.filter_tuples

	def getData(self):

		result = self.executeSelect( self.getSelect() )
		return result

	def executeSelect(self, sel):

		with Session(self.engine) as sess:
			#result will be a list of rows
			#each row is a tuple of ORMs
			#if theres only one ORM it's a tuple of length 1
			result = sess.execute(sel).all()
		return result

	# def _getApprovedTPP(self, systype='SGX', band='WR10', approved=True):
	# 	#hard coded select statement
	# 	sel = select( Test.file, Testset.SN1 )\
	# 		.join(Testset)\
	# 		.join(System,Testset.SN1==System.SN)\
	# 		.filter(System.Band==band)\
	# 		.filter(Testset.Approval==approved)\
	# 		.filter(System.Type==systype)\
	# 		.filter(Test.test_name.like('%High%'))

	# 	return sel

	# def _getVNAXTPP(self, systype='VNAX', band='WR10', approved=True):
	# 	#hard coded select statement
	# 	sel = select( TPP_Test.file, Testset.SN1, Testset.SN2 )\
	# 		.join(Testset)\
	# 		.join(System,Testset.SN1==System.SN)\
	# 		.filter(System.Band==band)\
	# 		.filter(Testset.Approval==approved)\
	# 		.filter(System.Type==systype)

	# 	return sel

	# def _getApprovedFiles(self, approved=True):
	# 	#hard coded select statement
	# 	sel = select(Test.file)\
	# 		.join(Testset)\
	# 		.filter(Testset.Approval==approved)

	# 	return sel