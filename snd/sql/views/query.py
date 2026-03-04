from views.query_gui import Query
from sqlalchemy import inspect, select

class QueryView (Query):

	def __init__(self, parent, controller):
		Query.__init__(self, parent)
		#sel = self.sql_manager.getSelect(my_classes[1])
		#data = self.sql_manager.executeSelect(sel)

		self.controller = controller


	def update_list(self, string_list):
		self.m_listBox5.Set(string_list)

	def load_table(self, table_object):
		pass

class QueryObject():

	def __init__(self, controller):
		self.available_columns = []
		self.controller = controller
		self.table_object = None
		self.columns = []

	def reset_table(self, table_obj):

		self.table_object = table_obj

		mapper = inspect(self.table_object)
		self.columns = list(mapper.columns)

	def join_table(self, my_col, other_table, other_col):

		my_column_obj = getattr(self.table_object, my_col)
		other_col_obj = getattr(other_table, other_col)

		sel = select(self.table_object)
		sel = sel.join(my_column_obj == other_col_obj)

		return sel