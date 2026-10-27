import numpy as np
import metas_unclib as mu


def corrected_transmission(gamma1, gamma2, s11, s22, s12, s21):
    a = s12*gamma1*gamma2
    b = (1-s11*gamma1)*(1-s22*gamma2)
    result = s21 / ( 1 - a/b )
    
    return result

def s11_to_gamma(s11_db):
    if s11_db == 0:
        return 1
    s11_lin = np.power(10,s11_db/20)
    vswr = (1+s11_lin)/(1-s11_lin)
    gamma = (vswr-1)/(vswr+1)
    return gamma

class YFactor:
    def __init__(self):

        self.trec_nominal = 1000
        self.tc_nominal = 80
        tc_sigma = 3
        self.th_nominal = 290
        th_sigma = 3
        self.p_sigma = 0.005

        self.tc_u = mu.ufloat(self.tc_nominal,tc_sigma,desc='T Cold (K)')
        self.th_u = mu.ufloat(self.th_nominal,th_sigma,desc='T Hot (K)')

    def calculate(self):

        ylin_nominal = (self.th_nominal + self.trec_nominal) / (self.tc_nominal + self.trec_nominal)
        ylog_nominal = 10*np.log10(ylin_nominal)
        
        pcold_u = mu.ufloat(-60,self.p_sigma,desc='P Cold (dBm)')
        phot_u = mu.ufloat(-60+ylog_nominal,self.p_sigma,desc='P Hot (dBm)')
        
        ylog_u = phot_u-pcold_u
        ylin_u = np.power(10,ylog_u/10)
        
        self.trx = (self.th_u - ylin_u*self.tc_u)/(ylin_u-1)


    def iterate(self):
        for j in [1000,5000,10000]:
            self.trec_nominal = j
            self.calculate()
            print(self.trx)
            mu.print_text_unc_budget(self.trx)
            print('\n')


class ENR:
    
    def __init__(self, yf):

        self.pns_sigma = 0.003

        self.trt_nominal = 290
        self.trt_sigma = 3

        self.ns_enr_nominal = 6
        self.ns_s11 = -20
        self.mixer_s11 = -20
        self.atn_s11 = -40
        self.atn_s21_nominal = 6
        self.atn_s21_sigma = 0.05

        self.trt_u = mu.ufloat(self.trt_nominal,self.trt_sigma,desc='NS T Room Temp (K)')

        yf.calculate()
        self.trec = yf.trx

    def calculate(self):
        enr_eff = self.ns_enr_nominal - self.atn_s21_nominal
        enr_lin = np.power(10,enr_eff/10)

        tns_nominal = (enr_lin * self.trt_nominal) + self.trt_nominal
        ns_ylin_nominal = (tns_nominal + self.trec.value) / (self.trt_nominal + self.trec.value)
        ns_ylog_nominal = 10*np.log10(ns_ylin_nominal)

    #     taper_loss = mu.ufloat(3,0.05,desc='Taper Loss (dB)')
    #     taper_loss_lin = np.power(10,taper_loss/10)
    #     taper_temp = (taper_loss_lin-1) * ln2_t_hot
        nscold_u = mu.ufloat(-40,self.pns_sigma,desc='P NS Off (dBm)')
        nshot_u = mu.ufloat(-40+ns_ylog_nominal,self.pns_sigma,desc='P NS On (dBm)')
    #     mixer_s11 = -6
    #     atn_s11 = -45
    #     ns_s11 = -10
        atn_s21_db = self.atn_s21_nominal*-1

        mixer_gamma = s11_to_gamma(self.mixer_s11)
        atn_s11_lin = np.power(10,self.atn_s11/10)
        ns_gamma = s11_to_gamma(self.ns_s11)
        atn_s21_lin = np.power(10,atn_s21_db/10)

        ns_ylog = nshot_u-nscold_u
        ns_ylin = np.power(10,ns_ylog/10)
        #Trx = (ln2_t_hot - Ylin*ln2_t_cold)/(Ylin-1)
    #     Trx_prime = (Trx-taper_temp)/taper_loss_lin
        Trx_prime = self.trec
        
        Tns = Trx_prime*(ns_ylin-1)+ns_ylin*self.trt_u
        measured_enr = (Tns-self.trt_u)/self.trt_u
        measured_enr_db = 10*np.log10(measured_enr)
        
        # print(f'trx with power uncertainty {Trx_prime}')
        # print(f'measured enr_db with power uncertainty {measured_enr_db}')
        atn_s21_u = mu.ufloat(atn_s21_lin,self.atn_s21_sigma,desc='attenuator')
        
        transmission = corrected_transmission(ns_gamma, mixer_gamma, atn_s11_lin, atn_s11_lin, atn_s21_lin, atn_s21_lin)
        # print(f'transmission coefficient {transmission}')
        # print(f'ideal transmission {atn_s21_lin}')
        transmission_error = transmission-atn_s21_lin
        # print(f'error {transmission_error}')
        
        atten_uncertainty = mu.ufloat(0,self.atn_s21_sigma,desc='atn uncertainty')
        
        atten_correction = mu.ufloat(atn_s21_lin, transmission_error,desc='tranmission coefficient')
        # print(f'ufloat correction: {atten_correction}')
        atten_correction_db = 10*np.log10(atten_correction) + atten_uncertainty
        # print(f'ufloat correction, db: {atten_correction_db}')
        self.enr_db = measured_enr_db-atten_correction_db
        
        # print(f'enr_db final {self.enr_db}')
        # mu.print_text_unc_budget(self.enr_db)

    def iterate(self):
        for j in [0,3,6]:
            self.atn_s21_nominal = j
            self.calculate()
            print(self.enr_db)
            mu.print_text_unc_budget(self.enr_db)
            print('\n')


if __name__ == '__main__':

    yf = YFactor()
    # yf.iterate()
    for j in [1000,5000,10000]:
        yf.trec_nominal=j
        yf.calculate()
        enr = ENR(yf)
        enr.iterate()
        