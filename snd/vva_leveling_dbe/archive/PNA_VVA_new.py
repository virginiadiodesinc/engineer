import pyvisa
import numpy as np
import pandas as pd
import time
import usb_communicator
import power_control_functions as pcf

# ============================================================================
# = Keithley SMU Control 
# ============================================================================
class SMU_K2611B():
    def __init__(self, address, rm):
        """
        Initializes SMU 
        """
        address_string = f'GPIB0::{address}::INSTR'
        self.inst = rm.open_resource(address_string)

        self.inst.write('display.screen = display.SMUA')
        self.inst.write('format.data = format.ASCII')
        self.inst.write('smua.nvbuffer1.clear()')
        self.inst.write('smua.nvbuffer1.appendmode = 1')
        self.inst.write('smua.nvbuffer1.collectsourcevalues = 1')
        self.inst.write('smua.measure.count = 1')
    
    def reset(self):
        self.inst.write('smua.reset()')
        
    def setsourceOn(self):
        self.inst.write('smua.source.output = smua.OUTPUT_ON')
        
    def setsourceOff(self):
        self.inst.write('smua.source.output = smua.OUTPUT_OFF')

    def set_current_limit(self, Imax):
        self.inst.write(f'smua.source.limiti = {Imax}')

    def set_voltage_level(self, Vlevel):
        self.inst.write(f'smua.source.levelv = {Vlevel}')

    def set_mode_voltage_source(self):
        self.inst.write('smua.source.func = smua.OUTPUT_DCVOLTS')
        self.inst.write('display.smua.measure.func = display.MEASURE_DCAMPS')

# ============================================================================
# = PNA CW Sweep & Read Functions
# ============================================================================
def read_averaged_trace(inst, trace_name="R1_Trace"):
    """
    Triggers the VNA, reads the specified trace, and returns the averaged value.
    """
    inst.write("INIT1:IMM")
    inst.query("*OPC?") 
    
    inst.write(f'CALC1:PAR:SEL "{trace_name}"')
    data = inst.query_ascii_values("CALC1:DATA? FDATA")
    
    return np.mean(data)

def run_vva_calibration_sweep(pna, f_start_ghz, f_stop_ghz, freq_steps, volt_points, cw_points=11):
    """
    Steps through a frequency range. At each frequency, sweeps VVA down (10V to 0V)
    and then up (0V to 10V), recording the reference trace at each point.
    """
    freq_list = np.linspace(f_start_ghz, f_stop_ghz, freq_steps)
    v_down_list = np.linspace(10.0, 0.0, volt_points)
    v_up_list = np.linspace(0.0, 10.0, volt_points)
    
    records_vdown = []
    records_vup = []
    
    connection = usb_communicator.usb_communicator()
    connection.connect()
    
    # PNA Setup: Define trace and configure for CW mode
    trace_name = "R1_Trace"
    pna.write(f'CALC1:PAR:DEF:EXT "{trace_name}", "R1,1"')
    pna.write("DISP:WIND1:STATE ON")
    pna.write(f'DISP:WIND1:TRAC2:FEED "{trace_name}"')
    
    pna.write("SENS1:SWE:TYPE CW")
    pna.write(f"SENS1:SWE:POIN {cw_points}")
    pna.write("INIT1:CONT OFF")
    
    print(f"\nStarting Calibration:")
    print(f" -> {freq_steps} Frequency steps ({f_start_ghz} to {f_stop_ghz} GHz)")
    print(f" -> {volt_points} Voltage steps (10V to 0V and back)\n")
    
    for freq in freq_list:
        # Set the CW frequency on the PNA
        pna.write(f"SENS1:FREQ:CW {freq}E9")
        print(f"Sweeping {freq:.3f} GHz...")
        
        # --- VDOWN SWEEP (10V to 0V) ---
        #CHANGE FOR U9 SOURCE
        row_down = {"Frequency (GHz)": freq}
        for v in v_down_list:
            connection.write(pcf.set_voltage(v))
            time.sleep(0.1)  # Let the VVA settle
            
            avg_val = read_averaged_trace(pna, trace_name)
            # Format the dictionary key dynamically so it becomes the column header
            row_down[f"{v:.2f}V"] = avg_val
            
        records_vdown.append(row_down)
        
        # --- VUP SWEEP (0V to 10V) ---
        #CHANGE TO U9 SOURCE
        row_up = {"Frequency (GHz)": freq}
        for v in v_up_list:
            connection.write(pcf.set_voltage(v))
            time.sleep(0.1)  # Let the VVA settle
            
            avg_val = read_averaged_trace(pna, trace_name)
            row_up[f"{v:.2f}V"] = avg_val
            
        records_vup.append(row_up)

    # Turn off the SMU when finished
    
    return records_vdown, records_vup

def export_vva_calibration(records_vdown, records_vup, filename="VVA_Calibration_Data.xlsx"):
    """
    Exports the sweep data into an Excel file with two distinct sheets.
    """
    df_down = pd.DataFrame(records_vdown)
    df_up = pd.DataFrame(records_vup)
    
    # Use pandas ExcelWriter to manage multiple sheets
    with pd.ExcelWriter(filename) as writer:
        df_down.to_excel(writer, sheet_name="Vdown", index=False)
        df_up.to_excel(writer, sheet_name="Vup", index=False)
        
    print(f"\nCalibration data successfully exported to {filename}")

def calculate_relative_attenuation(input_filename="VVA_Calibration_Data.xlsx", output_filename="VVA_Attenuation_Data.xlsx"):
    """
    Reads the raw VVA calibration data, normalizes each frequency to the 10V  reading,
    and exports a new Excel file with the relative attenuation in dB.
    """
    print(f"\nReading raw data from {input_filename}...")
    
    try:
        
        raw_data = pd.read_excel(input_filename, sheet_name=None)
    except FileNotFoundError:
        print(f"Error: Could not find '{input_filename}'. Run the sweep first!")
        return
        
    # Open the new Excel file to save processed data
    with pd.ExcelWriter(output_filename) as writer:
        
        # Loop through both sheets
        for sheet_name, df in raw_data.items():
            
            
            df_normalized = df.copy()
            #ref to max power
            baseline_col = "10.00V"
            
            # Get a list of all columns besides the Frequency column
            voltage_cols = [col for col in df.columns if col != "Frequency (GHz)"]
            
            # MAFFS
            for col in voltage_cols:
                df_normalized[col] = df[col] - df[baseline_col]
                
            # Save sheet 
            df_normalized.to_excel(writer, sheet_name=sheet_name, index=False)
            
    print(f"Post-processing complete! Normalized attenuation data saved to {output_filename}")





if __name__ == "__main__":
    print("--- VVA Calibration: Frequency & Voltage Sweep ---")
    
    # sweep params
    f_start = float(input("Enter Start Frequency (GHz) [Default 110]: ") or 110)
    f_stop = float(input("Enter Stop Frequency (GHz) [Default 170]: ") or 170)
    freq_steps = int(input("Enter number of frequency steps [Default 30]: ") or 30)
    volt_points = int(input("Enter number of voltage points [Default 21]: ") or 21)
    cw_points = int(input("Enter number of CW Frequency points [Default 11]: ") or 11)
    
    rm = pyvisa.ResourceManager()
    
    # Addresses
    pna_address = 'GPIB0::16::INSTR' 
    smu_address = 20  #DELETE ONCE WE MOVE TO MCU
    
    pna = None
    try:
        print(f"\nConnecting to instruments...")
        pna = rm.open_resource(pna_address)
        pna.timeout = 10000  
        
        # Initialize the SMU 
        #DELETE LATER
        smu = SMU_K2611B(address=smu_address, rm=rm)
        
        # Run the full routine
        rec_down, rec_up = run_vva_calibration_sweep(
            pna=pna, 
            f_start_ghz=f_start, 
            f_stop_ghz=f_stop, 
            freq_steps=freq_steps, 
            volt_points=volt_points,
            cw_points=cw_points
        )
        
        #export excel file
        export_vva_calibration(rec_down, rec_up, filename="VVA_Calibration_Data.xlsx")
        #generate separate attn file
        calculate_relative_attenuation()
        
    except pyvisa.errors.VisaIOError as e:
        print(f"\nFailed to connect or communicate with the instruments: {e}")
    finally:
        if pna:
            print("Restoring PNA to continuous sweep...")
            pna.write("INIT1:CONT ON")
            pna.close()

