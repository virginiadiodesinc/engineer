from SQLHelper import SQLHelper
from viewer import OrmViewer

class Controller:

	def __init__(self):
		self.sql_manager = SQLHelper()
		self.table_dictionary = {}
		self.column_dictionary = {}
		self.object_list = []

		self.main_view = OrmViewer(parent=None, controller=self)
		self.main_view.Show()

		self.second_view = OrmViewer(parent=None, controller=self)
		self.second_view.Show()

		tables = self.get_tables()
		strings = self.tables_to_strings(tables)

		for t,s in zip(tables, strings):
			self.table_dictionary[s] = t

		self.main_view.set_table_names(strings)
		self.second_view.set_table_names(strings)

	def column_selected_event(self, table_str, column_str):
		#table = self.table_dictionary[table_str]
		column = self.column_dictionary[column_str]

		sel = self.sql_manager.getSelect(column)

		all_objects = self.sql_manager.executeSelect(sel)
		object_set = list( set(all_objects) )
		object_list = [k[0] for k in object_set]

		return object_list

	def table_selected_event(self):
		table_str = self.main_view.get_selected_table()
		table_class = self.table_dictionary[table_str]

		my_columns = self.get_columns(table_class)
		'''
		name: testsetID
		type: INTEGER()
		foreign_keys: ForeignKey('testset.ID')
		table: <test>
		primary_key: True
		nullable: False
		'''
		self.column_dictionary = {}

		for col in my_columns:
			col_name = col.name
			self.column_dictionary[col_name]=col

		self.main_view.set_column_names( list( self.column_dictionary.keys() ) )

	def find_foreign_keys(self):

		for table_name in self.table_dictionary:

			table_obj = self.table_dictionary[table_name]
			table_columns = self.sql_manager.get_columns(table_obj)

			for col in table_columns:
				if len(col.foreign_keys) > 0:
					print(col.foreign_keys)

	def join_tables(self):
		main_table_name = self.main_view.get_selected_table()
		sub_table_name = self.second_view.get_selected_table()

		#main_table_col = self.main_view.get_selected_column()
		#sub_table_col = self.second_view.get_selected_column()

		main_table = self.table_dictionary[main_table_name]
		second_table = self.table_dictionary[sub_table_name]

		#main_col = self.column_dictionary[main_table_col]
		#sub_col = self.column_dictionary[sub_table_col]

		sel = self.sql_manager.getSelect(main_table)
		sel = sel.join(second_table)

		print(sel)



	def autojoin_table(self, table_name):

		table_obj = self.table_dictionary[table_name]
		table_columns = self.sql_manager.get_columns(table_obj)

		sel = self.sql_manager.getSelect(table_obj)

		for col in table_columns:
			foreign_keys = list(col.foreign_keys)

			if len(foreign_keys) <= 1:

				for key in foreign_keys:

					target_table = key.column.table.name
					sel = sel.join(self.table_dictionary[target_table])

		return sel


	def run_query(self, table, column, value):
		table_obj = self.table_dictionary[table]
		column_obj = self.column_dictionary[column]

		sel = self.sql_manager.getSelect(table_obj)
		sel = sel.where(column_obj==value)

		self.object_list = self.sql_manager.executeSelect(sel)

		return self.obj_list_to_str()
	
	def obj_list_to_str(self):
		strings = []

		my_class = self.table_dictionary[ self.main_view.get_selected_table() ]

		for obj in self.object_list:
			obj_column_keys = self.sql_manager.get_instance_columns(obj[0])
			substr = ""

			for key in obj_column_keys:

				substr += str(getattr(obj[0],key))

			strings.append(substr)

		return strings

	def tables_to_strings(self, table_objs):

		out = []

		for ob in table_objs:

			out.append(str(ob).split('.')[-1][:-2])

		return out

	def get_tables(self):

		return self.sql_manager.get_automap_classes()

	def get_columns(self, automapped_class):

		return list( self.sql_manager.get_columns(automapped_class) )