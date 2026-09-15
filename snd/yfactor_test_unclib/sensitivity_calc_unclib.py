import metas_unclib as mu
import numpy as np

def s11_to_gamma(s11_db):
    s11_lin = np.power(10,s11_db/20)
    vswr = (1+s11_lin)/(1-s11_lin)
    gamma = (vswr-1)/(vswr+1)
    return gamma

def gammas_to_unc(gamma1, gamma2):
    unc = -20*np.log10(1-gamma1*gamma2)
    return unc

if __name__ == '__main__':

    ln2_t_cold = mu.ufloat(80,1,desc='T Cold (K)')
    ln2_t_hot = mu.ufloat(293,1,desc='T Hot (K)')
    ln2cold = mu.ufloat(-80,0.01,desc='P Cold (dBm)')
    ln2hot = mu.ufloat(-79,0.01,desc='P Hot (dBm)')
    taper_loss = mu.ufloat(0.3,0.01,desc='Taper Loss (dB)')
    taper_loss_lin = np.power(10,taper_loss/10)
    taper_temp = (taper_loss_lin-1) * ln2_t_hot
    ns_t_rt = mu.ufloat(293,1,desc='NS Room Temp (K)')
    nscold = mu.ufloat(-50,0.01,desc='P NS Off (dBm)')
    nshot = mu.ufloat(-40,0.01,desc='P NS On (dBm)')
    mixer_s11 = -6
    horn_s11 = -30
    ns_s11 = -20

    mixer_gamma = s11_to_gamma(mixer_s11)
    horn_gamma = s11_to_gamma(horn_s11)
    ns_gamma = s11_to_gamma(ns_s11)

    rl1_unc_db = mu.ufloat(0,gammas_to_unc(mixer_gamma,horn_gamma),desc='mixer to horn rl (dB)')
    rl2_unc_db = mu.ufloat(0,gammas_to_unc(mixer_gamma,ns_gamma),desc='mixer to ns rl (dB)')

    Ylog = ln2hot-ln2cold
    Ylin = np.power(10,Ylog/10)
    ns_ylog = nshot-nscold
    ns_ylin = np.power(10,ns_ylog/10)
    Trx = (ln2_t_hot - Ylin*ln2_t_cold)/(Ylin-1)
    Trx_prime = (Trx-taper_temp)/taper_loss_lin
    Tns = Trx_prime*(ns_ylin-1)+ns_ylin*ns_t_rt
    enr = (Tns-ns_t_rt)/ns_t_rt
    enr_db = 10*np.log10(enr)
    enr2_db = enr_db+rl1_unc_db+rl2_unc_db

    print(Trx_prime)
    mu.print_text_unc_budget(Trx_prime)

    print(Tns)
    mu.print_text_unc_budget(Tns)

    print(enr_db)
    mu.print_text_unc_budget(enr_db)

    print(enr2_db)
    mu.print_text_unc_budget(enr2_db)