import pandas as pd
import matplotlib.pyplot as plt
import datetime
import plotly.express as px
import plotly

import os

class SourcePowerHarmonics:
	""" Power Leveling Harmonics plotting class
	Holds data, specs, plotly figure, and its html
	This is Steves class, with Jaes request added. No JS!
	"""
	def __init__(self, data_xlsx):
		
		#dict of dataframes
		#keys are input power levels
		#these files are already corrected for TPP

		if data_xlsx == None:
			return

		self.start_time = datetime.datetime.now()
		print(self.start_time)

		print('loading from excel')
		self.data = pd.read_excel(data_xlsx, sheet_name=None, index_col=0)
		self.data.pop('settings', None)
		print(datetime.datetime.now() - self.start_time)

		print('reading dataframe information')
		self.get_data_informations()
		print(datetime.datetime.now() - self.start_time)

		print('processing data')
		self.process_data()
		print(datetime.datetime.now() - self.start_time)

	def get_data_informations(self):
		# uses random sheet (as any is fine) to get min and max frequency as well as min and max power (and number of points per sheet)
		first_sheet = next(iter(self.data.values())).sort_index()

		self.min_frequency = first_sheet.index[0]
		self.max_frequency = first_sheet.index[-1]
		
		self.num_points = len(first_sheet.index)
		
		keys_as_list = list(self.data.keys())
		keys_as_floats = [float(k) for k in keys_as_list]

		self.min_input_power = str(min(keys_as_floats))
		self.max_input_power = str(max(keys_as_floats))
			
		# uses the max input power sheet df (which doesn't matter?) to get the main tone of the system
		power_df = self.data[self.max_input_power]
		self.rf_mult = int(power_df.mean().idxmax())

	def process_data(self):
		dbc_data = {}
		longform_df_dbc = pd.DataFrame()

		for input_power in self.data.keys():

			temp_df = self.data[input_power].sort_index()
			temp_dbc = temp_df.sub(temp_df[self.rf_mult],axis=0)
			temp_dbc['main_tone_power'] = temp_df[self.rf_mult]

			dbc_data[input_power] = temp_dbc

			longform_df_dbc = pd.concat([longform_df_dbc,temp_dbc])

		self.dbc_data = dbc_data
		self.longform_df_dbc = longform_df_dbc

	def get_harmonics_at_output_power(self, main_tone_power, tolerance=0.5):

		mask = abs(self.longform_df_dbc['main_tone_power'] - main_tone_power) < tolerance

		return self.longform_df_dbc[mask]

	def scatter_plot(self, df, plot_title):

		plt.figure()
		ax = plt.subplot(111)
		for column in df:
			plt.scatter(df.index,df[column],label=column)

		# Shrink current axis by 20%
		box = ax.get_position()
		ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

		# Put a legend to the right of the current axis
		ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
		plt.title(plot_title)

	def px_scatter(self, df):
		pass

	def generate_plots(self, power_list, tolerance):
		output_df = pd.DataFrame()

		for j in power_list:
			df = self.get_harmonics_at_output_power(j, tolerance)
			df['goal_power'] = j

			output_df = pd.concat([output_df,df])

		return output_df

class FileFinder:
	def __init__(self, sn1=3937, sn2=3938, rev='a'):
		
		#example filepath: W:\ExtenderTestDB\3937-3938,g\Powerleveling Harmonics\Output files
		filepath0 = r'W:\ExtenderTestDB'
		if sn2:
			filepath1 = f'{sn1}-{sn2},{rev}'
		else:
			filepath1 = f'{sn1},{rev}'
		filepath2 = r'Powerleveling Harmonics'

		temp_path = os.path.join(filepath0, filepath1, filepath2)
		temp_list = os.listdir(temp_path)

		if 'Output files' in temp_list:
			self.mypath = os.path.join(temp_path,'Output files')
		else:
			self.mypath = temp_path



		self.files = [k for k in os.listdir(self.mypath) if 'xlsx' in k]

	def get_paths(self):
		path1 = None
		path2 = None
		if len(self.files) > 0:
			path1 = os.path.join(self.mypath,self.files[0])
		if len(self.files) > 1:
			path2 = os.path.join(self.mypath,self.files[-1])

		return path1, path2

def make_plots(path):
	sph1 = SourcePowerHarmonics(path)
	df1 = sph1.generate_plots([-35,-30,-25,-20,-15,-10,-5,0],0.5)
	df2 = sph1.generate_plots([-15,-10,-5,0],0.5)

	fig1 = px.scatter(df1, facet_col='goal_power',facet_col_wrap=2)
	fig2 = px.scatter(df2, facet_col='goal_power',facet_col_wrap=2)

	fig1.add_hline(y=-20, line_dash="dot",
          annotation_text="20dbc",
          annotation_position="bottom right")
	fig2.add_hline(y=-20, line_dash="dot",
              annotation_text="20dbc",
              annotation_position="bottom right")

	fig1.add_hline(y=-10, line_dash="dot",
          annotation_text="10dbc",
          annotation_position="top left")
	fig2.add_hline(y=-10, line_dash="dot",
          annotation_text="10dbc",
          annotation_position="top left")

	return fig1,fig2

if __name__ == '__main__':
	sn1=4046
	sn2=None
	rev='b'
	a = FileFinder(sn1=sn1, sn2=sn2, rev=rev)

	path1, path2 = a.get_paths()
	basepath = r'J:\engineer directories\durant\plh data'

	if path1:
		fig1, fig2 = make_plots(path1)
		plotly.offline.plot(fig1, filename=os.path.join(basepath,f'{sn1},{rev}_a.html'))
		plotly.offline.plot(fig2, filename=os.path.join(basepath,f'{sn1},{rev}_b.html'))

	if path2:
		fig3, fig4 = make_plots(path2)
		plotly.offline.plot(fig3, filename=os.path.join(basepath,f'{sn2},{rev}_a.html'))
		plotly.offline.plot(fig4, filename=os.path.join(basepath,f'{sn2},{rev}_b.html'))


	# path1 = r"W:\ExtenderTestDB\2759-2944,h\PLH\VNAX 2759 PLH\output.xlsx"
	# path2 = r"W:\ExtenderTestDB\2759-2944,h\PLH\VNAX 2944 PLH\output.xlsx"

	# sph1 = SourcePowerHarmonics(path1)

	# df1 = sph1.generate_plots([-35,-30,-25,-20,-15,-10,-5,0],0.5)
	# df2 = sph1.generate_plots([-15,-10,-5,0],0.5)


	# sph2 = SourcePowerHarmonics(path2)
	# df3 = sph2.generate_plots([-35,-30,-25,-20,-15,-10,-5,0],0.5)
	# df4 = sph2.generate_plots([-15,-10,-5,0],0.5)

	# fig1 = px.scatter(df1, facet_col='goal_power',facet_col_wrap=2)
	# fig2 = px.scatter(df2, facet_col='goal_power',facet_col_wrap=2)
	# fig3 = px.scatter(df3, facet_col='goal_power',facet_col_wrap=2)
	# fig4 = px.scatter(df4, facet_col='goal_power',facet_col_wrap=2)

	# fig1.add_hline(y=-20, line_dash="dot",
 #          annotation_text="20dbc",
 #          annotation_position="bottom right")
	# fig2.add_hline(y=-20, line_dash="dot",
 #              annotation_text="20dbc",
 #              annotation_position="bottom right")
	# fig3.add_hline(y=-20, line_dash="dot",
 #              annotation_text="20dbc",
 #              annotation_position="bottom right")
	# fig4.add_hline(y=-20, line_dash="dot",
 #              annotation_text="20dbc",
 #              annotation_position="bottom right")
	# fig1.add_hline(y=-10, line_dash="dot",
 #          annotation_text="10dbc",
 #          annotation_position="top left")
	# fig2.add_hline(y=-10, line_dash="dot",
 #          annotation_text="10dbc",
 #          annotation_position="top left")
	# fig3.add_hline(y=-10, line_dash="dot",
 #          annotation_text="10dbc",
 #          annotation_position="top left")
	# fig4.add_hline(y=-10, line_dash="dot",
 #          annotation_text="10dbc",
 #          annotation_position="top left")

