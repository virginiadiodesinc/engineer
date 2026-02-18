from viewer_gui import OrmViewerFrame

class OrmViewer(OrmViewerFrame):

	def __init__(self, parent, controller):
		OrmViewerFrame.__init__(self, parent)
		#sel = self.sql_manager.getSelect(my_classes[1])
		#data = self.sql_manager.executeSelect(sel)

		self.controller = controller

	def set_table_names(self, table_list):

		self.m_listBox1.Set(table_list)

	def set_column_names(self, column_list):

		self.m_listBox2.Set(column_list)

	def get_listbox_selection(self, listbox_obj):

		index = listbox_obj.GetSelection()
		return listbox_obj.GetString(index)

	def get_selected_table(self):
		return self.get_listbox_selection(self.m_listBox1)

	def get_selected_column(self):
		return self.get_listbox_selection(self.m_listBox2)

	def table_selected(self, event):
		event.Skip()

		self.controller.table_selected_event()

	def column_selected(self, event):
		event.Skip()

		my_table = self.get_selected_table()
		my_col = self.get_selected_column()

		choices_list = self.controller.column_selected_event(my_table, my_col)

		self.m_listBox4.Set(choices_list)

	def run_query(self, event):
		event.Skip()

		self.controller.join_tables()

		# my_table = self.get_selected_table()
		# my_col = self.get_selected_column()
		# my_value = self.m_textCtrl1.GetValue()

		# obj_list = self.controller.run_query(my_table, my_col, my_value)

		# self.m_listBox4.Set(obj_list)