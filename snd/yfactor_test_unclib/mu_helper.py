import metas_unclib as mu
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def str_to_ufloat(input_string):
	'''
	if complex number, replace with np.nan
	'''
	try:
		substrings = input_string.split('±')
		if 'j' in substrings[0]:
			return np.nan
		else:
			ufloat = mu.ufloat( float(substrings[0]), float(substrings[1]) )
			return ufloat
	except:
		return float(input_string)

def read_csv(filename, **kwargs):
	df = pd.read_csv(filename, **kwargs)
	for c in df.columns:
		#for each column
		substr = df[c].iloc[0]
		if (type(substr) == str):
			#try to find columns that are strings
			if substr.find('±') > -1:
				#if the string has a ± character, try to parse the whole column into ufloats
				df[c] = df[c].apply(str_to_ufloat)

	return df

def split_csv_columns(filename, **kwargs):
	#for every column with type of ufloat we split into two columns
	df = read_csv(filename, **kwargs)
	for c in df.columns:
		substr = df[c].iloc[0]
		if (type(substr) == mu.ufloat):
			new_series = df[c].apply(lambda x: x.stdunc)
			location = df.columns.get_loc(c)
			df.insert(location+1,f'{c}_unc',new_series)

			df[c] = df[c].apply(lambda x: x.value)
	return df
	


def plot_ufloat(x_values, y_ufloats, line_kwargs=None, fill_kwargs=None):
	"""
	Plots METAS UncLib ufloat objects with shaded standard uncertainty regions.
	
	Parameters:
	* x_values : x-axis data points.
	* y_ufloats : y-axis data points containing METAS ufloat objects.
	* line_kwargs : Arguments passed to plt.plot().
	* fill_kwargs : Arguments passed to plt.fill_between().


	Example: plot_ufloat(
		x_data, y_data1, 
		line_kwargs={'color': 'teal', 'linestyle': '-', 'marker': 'o', 'linewidth': 2, 'label': 'WR4.3NS-B'},
		fill_kwargs={'hatch': '.', 'alpha': 0.4, 'edgecolor': 'black','color':'green'} 
	)

	"""
	
	# Initialize empty dictionaries if None are provided
	line_kwargs = line_kwargs or {}
	fill_kwargs = fill_kwargs or {}
	
	# Extract nominal values and uncertainties
	# #These are np.array by default but casting anyways to be certain 
	y_nom = np.array(mu.get_value(y_ufloats))
	y_err = np.array(mu.get_stdunc(y_ufloats))
	x_nom = np.array(x_values)
	
	# unpack line input dictionary and catch plt.plot return to match colors by default
	line, = plt.plot(x_nom, y_nom, **line_kwargs)
	
	# Set up sensible defaults for the shaded region
	default_fill = {
		'color': line.get_color(), 
		'alpha': 0.3,
		'hatch': '//',
		'label': "_nolegend_"
	}
	
	# Update default dict with user args
	default_fill.update(fill_kwargs)
	
	# Unpack fill dictionary
	plt.fill_between(
		x_nom, 
		y_nom - y_err, 
		y_nom + y_err, 
		**default_fill
	)