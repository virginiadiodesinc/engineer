

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def plot_directivity(df, direction = 'forward'):

	forward_directivity = df[f'{direction} directivity'].apply(complex)
	forward_reflection = df[f'{direction} reflection tracking'].apply(complex)

	sys_dir = forward_reflection / forward_directivity

	sys_dir_mag = sys_dir.apply(np.absolute)
	sys_dir_db = 20*np.log10(sys_dir_mag)

	return sys_dir_db

def get_mag_db(series):

	series_mag = series.apply(np.absolute)
	series_db = 20*np.log10(series_mag)
	return series_db


def plot_reflection_trackings(df):

	forward_reflection = df['forward reflection tracking'].apply(complex)
	reverse_reflection = df['reverse reflection tracking'].apply(complex)

	get_mag_db(forward_reflection).plot()
	get_mag_db(reverse_reflection).plot()

	plt.show()





if __name__ == '__main__':
	plt.ion()

	#df = pd.read_excel('TRL_coefs.xlsx')
	df = pd.read_excel('SOLT_coefs.xlsx')
	df.index = df['Unnamed: 0']

	dir1 = plot_directivity(df, 'forward')
	dir2 = plot_directivity(df, 'reverse')

	plot_reflection_trackings(df)
	plt.figure()

	(-1*dir1).plot()
	(-1*dir2).plot()

	plt.axhline(-18)

	plt.show()