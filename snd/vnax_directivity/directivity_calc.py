

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

def plot_residual_directivity(xlsx='vnax4037b.xlsx'):

	df = pd.read_excel(xlsx,sheet_name='xj10',index_col=0)
	df['S11(lin)'] = np.power(10,df['S11(dB)']/20)

	s11vals = df['S11(lin)'].values
	derivative = list( s11vals[1:]-s11vals[:-1] )
	derivative.append(0)

	crossings_indices = np.where(np.diff(np.sign(derivative)))[0]

	df['deriv'] = derivative
	df['crossings'] = 0
	for j in crossings_indices:
		df['crossings'].iloc[j] = 1


	subdf = df[df['crossings']>0]
	peakvals = subdf['S11(lin)'].values
	cross_indices = subdf.index.values

	peakdiffs = peakvals[:-1]-peakvals[1:]
	peakdiffs_db = 20*np.log10( abs(peakdiffs) )

	peak_indices = (cross_indices[:-1]+cross_indices[1:])/2


	return df, peakdiffs_db, peak_indices



#if __name__ == '__main__':
	# plt.ion()

	# #df = pd.read_excel('TRL_coefs.xlsx')
	# df = pd.read_excel('SOLT_coefs.xlsx')
	# df.index = df['Unnamed: 0']

	# dir1 = plot_directivity(df, 'forward')
	# dir2 = plot_directivity(df, 'reverse')

	# plot_reflection_trackings(df)
	# plt.figure()

	# (-1*dir1).plot()
	# (-1*dir2).plot()

	# plt.axhline(-18)

	# plt.show()