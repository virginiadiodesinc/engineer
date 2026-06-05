import metas_unclib as mu
import numpy as np

if __name__ == '__main__':

	power_unc = 0.0013

	thot = mu.ufloat(293,1.5)
	thot2 = mu.ufloat(293,1.5)
	tcold = mu.ufloat(78.5,1.5)

	atn_db = mu.ufloat(10, 0.015)
	taper_db = mu.ufloat(0.125, 0.015)

	taper_atn_lin = np.power(10, (atn_db+taper_db)/10)
	taper_k = (taper_atn_lin - 1) * thot

	tmix = mu.ufloat(1000,20)

	trx = tmix*taper_atn_lin + taper_k

	