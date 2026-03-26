

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


if __name__ == '__main__':

	df = pd.read_excel('TRL_coefs.xlsx')

	forward_directivity = df['forward directivity'].apply(complex)
	forward_reflection = df['forward reflection tracking'].apply(complex)

	sys_dir = forward_reflection / forward_directivity

	sys_dir_mag = sys_dir.apply(np.absolute)
	sys_dir_db = 10*np.log10(sys_dir_mag)
	sys_dir_deg = sys_dir.apply(np.angle)

	sys_dir_db.plot()
	plt.show()

