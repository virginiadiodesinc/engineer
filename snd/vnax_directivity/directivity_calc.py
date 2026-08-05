

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import os

def get_directivity(df, direction = 'forward'):
	'''
	direction = forward, reverse, or None
	'''
	if direction is None:
		directivity = df['directivity'].apply(complex)
		reflection = df['reflection tracking'].apply(complex)

	else:
		directivity = df[f'{direction} directivity'].apply(complex)
		reflection = df[f'{direction} reflection tracking'].apply(complex)

	sys_dir = directivity / reflection

	sys_dir_mag = sys_dir.apply(np.absolute)
	sys_dir_db = 20*np.log10(sys_dir_mag)

	return sys_dir_db

def get_1port_directivity(df):
	'''
	direction = forward, reverse, or None
	'''
	directivity = df['directivity'].apply(complex)
	reflection = df['reflection tracking'].apply(complex)

	sys_dir = directivity / reflection

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

def plot_residual_directivity_binned(xlsx='vnax4044b.xlsx',port=1,legend_name='',bin_size_ghz=5):
	logval=20

	if port==1:
		identifier = 'S11'
	else:
		identifier = 'S22'

	df = pd.read_excel(xlsx,sheet_name='J10 Short',index_col=0)
	df[f'{identifier}(lin)'] = np.power(10,(df[f'{identifier}(dB)']/logval))

	s11vals = df[f'{identifier}(lin)'].values

	#start at index = 0 and mask ~5ghz, then find peaks
	index_val = 0
	current_freq = df.index[index_val]




def plot_residual_directivity(xlsx='vnax4044b.xlsx',port=1,legend_name=''):
	logval=20

	if port==1:
		identifier = 'S11'
	else:
		identifier = 'S22'

	df = pd.read_excel(xlsx,sheet_name='J10 Short',index_col=0)
	df[f'{identifier}(lin)'] = np.power(10,(df[f'{identifier}(dB)']/logval))

	s11vals = df[f'{identifier}(lin)'].values
	derivative = list( s11vals[1:]-s11vals[:-1] )
	derivative.append(0)

	crossings_indices = np.where(np.diff(np.sign(derivative)))[0]

	df['deriv'] = derivative
	df['crossings'] = 0
	for j in crossings_indices:
		df['crossings'].iloc[j] = 1


	subdf = df[df['crossings']>0]
	peakvals = subdf[f'{identifier}(lin)'].values
	cross_indices = subdf.index.values

	peakdiffs = peakvals[:-1]-peakvals[1:]
	peakdiffs_db = logval*np.log10( abs(peakdiffs)/2 )

	peak_indices = (cross_indices[:-1]+cross_indices[1:])/2

	df[f'{identifier}(dB)'].plot(label=f'p{port} J10+Short', color='gray')
	plt.scatter(peak_indices, peakdiffs_db, label=legend_name, color='red')

	return df, peakdiffs_db, peak_indices

def plot_directivity_metrics(folder_path, num_ports=2,name1='vnax xxx', name2='vnax yyy'):
	files = os.listdir(folder_path)

	file_paths = [os.path.join(folder_path,k) for k in files]

	coefs_path = [k for k in file_paths if 'coefs' in k]
	data_path = [k for k in file_paths if 'vnax' in k]

	coefs_df = pd.read_excel(coefs_path[0],index_col=0)

	if num_ports==1:
		directivity = get_directivity(coefs_df,None) * -1
		plt.figure()
		plot_residual_directivity(data_path[0],1,name1)
		directivity.plot(label='p1 raw directivity',color='black')
		plt.legend()

	elif num_ports==2:
		fwd_directivity = get_directivity(coefs_df, 'forward') * -1
		rev_directivity = get_directivity(coefs_df, 'reverse') * -1

		plt.figure()
		plot_residual_directivity(data_path[0],1,name1)
		fwd_directivity.plot(label='p1 raw directivity',color='black')
		plt.legend()

		plt.figure()
		plot_residual_directivity(data_path[0],2,name2)
		rev_directivity.plot(label='p2 raw directivity',color='black')
		plt.legend()

if __name__ == '__main__':
	#plt.ion()
	pass
	df = pd.read_excel('TRL_coefs_wr19.xlsx')
	# df = pd.read_excel('SOLT_coefs.xlsx')
	df.index = df['Unnamed: 0']

	dir1 = get_directivity(df, 'forward')
	dir2 = get_directivity(df, 'reverse')

	#plot_reflection_trackings(df)
	plt.figure()

	(-1*dir1).plot()
	(-1*dir2).plot()

	#plt.axhline(-18)
	plt.legend()

	plt.show()