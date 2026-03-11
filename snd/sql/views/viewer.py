from views.viewer_gui import OrmViewerFrame

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

	def filter_values(self, event):
		event.Skip()

		filter_string = self.m_textCtrl1.GetValue()

		current_choices = self.m_listBox4.GetItems()

		filtered_choices = [c for c in current_choices if filter_string in c]
		self.m_listBox4.Set(filtered_choices)

	def load_selected_table(self, event):
		event.Skip()

		my_table = self.get_selected_table()
		self.controller.load_table(my_table)


	def run_query(self, event):
		event.Skip()

		my_table = self.get_selected_table()
		my_col = self.get_selected_column()
		my_value = self.get_listbox_selection(self.m_listBox4)

		self.controller.run_query(my_table, my_col, my_value)