from .keithley_236_functions import SMU_K236
from .postprocess import convert_keithley_string_to_list
import time
import pandas as pd

if __name__ == '__main__':

    smu = SMU_K236()
    smu.connect()

    time.sleep(1)

    src,meas = smu.takeHeatTest()

    print(src)

    print(meas)

    df = pd.DataFrame()
    df['src'] = convert_keithley_string_to_list(src)
    df['meas'] = convert_keithley_string_to_list(meas)

    df.to_csv('keithley_out.csv')