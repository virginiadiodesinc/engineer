import pyvisa
import numpy as np
import pandas as pd
from vdi_controller import VDIModuleController
import time 

# ============================================================================
# = PNA CW Sweep & Read Functions
# ============================================================================
def run_vva_calibration_sweep(pna, vdi, f_start_ghz, f_stop_ghz, freq_steps, volt_points):
    """
    Steps through a frequency range. At each frequency, loads a voltage sweep into 
    the VDI module and lets the PNA's hardware triggers execute the sequence.
    """
    freq_list = np.linspace(f_start_ghz, f_stop_ghz, freq_steps)
    v_down_list = np.linspace(10.0, 0.0, volt_points)
    v_up_list = np.linspace(0.0, 10.0, volt_points)
    
    records_vdown = []
    records_vup = []
    
    # PNA Setup: Define trace and configure for CW mode
    trace_name = "R1_Trace"
    pna.write(f'CALC1:PAR:DEF:EXT "{trace_name}", "R1,1"')
    pna.write("DISP:WIND1:STATE ON")
    pna.write(f'DISP:WIND1:TRAC2:FEED "{trace_name}"')
    
    pna.write("SENS1:SWE:TYPE CW")
    
    pna.write(f"SENS1:SWE:POIN {volt_points}")
    pna.write("INIT1:CONT OFF")
    
    print(f"\nStarting Hardware-Triggered Calibration:")
    print(f" -> {freq_steps} Frequency steps ({f_start_ghz} to {f_stop_ghz} GHz)")
    print(f" -> {volt_points} Voltage steps per trace (10V to 0V and back)\n")
    
    for freq in freq_list:
        # Set the CW frequency on the PNA
        pna.write(f"SENS1:FREQ:CW {freq}E9")
        print(f"Sweeping {freq:.3f} GHz...")
        
        # ==========================================
        # --- VDOWN SWEEP (10V to 0V) ---
        # ==========================================
        
        # Load the descending voltage array into memory
        vdi.load_memory_sequence(0, v_down_list)
        # reset to address 0 on the sweep trigger
        vdi.set_sweep_start_address(0)
        
        # Trigger PNA sweep
        pna.write("INIT1:IMM")
        pna.query("*OPC?") 
        
        # Read trace 
        # (Trace index directly corresponds to voltage array index)
        pna.write(f'CALC1:PAR:SEL "{trace_name}"')
        data_down = pna.query_ascii_values("CALC1:DATA? FDATA")
        
        row_down = {"Frequency (GHz)": freq}
        for v, val in zip(v_down_list, data_down):
            row_down[f"{v:.2f}V"] = val
        
        time.sleep(0.1)
        print(f"\nSleeping")
        records_vdown.append(row_down)
        
        # ==========================================
        # --- VUP SWEEP (0V to 10V) ---
        # ==========================================
        
        # Load the ascending voltage array into VDI memory
        vdi.load_memory_sequence(0, v_up_list)
        #reset to address 0 on the sweep trigger
        vdi.set_sweep_start_address(0)
        
        # Trigger PNA sweep
        pna.write("INIT1:IMM")
        pna.query("*OPC?") 
        
        # Read trace
        pna.write(f'CALC1:PAR:SEL "{trace_name}"')
        data_up = pna.query_ascii_values("CALC1:DATA? FDATA")
        
        row_up = {"Frequency (GHz)": freq}
        for v, val in zip(v_up_list, data_up):
            row_up[f"{v:.2f}V"] = val

        time.sleep(0.1)
        print(f"\nSleeping")
        records_vup.append(row_up)

    return records_vdown, records_vup

def export_vva_calibration(records_vdown, records_vup, filename="VVA_Calibration_Data.xlsx"):
    """Exports the sweep data into an Excel file with two distinct sheets."""
    df_down = pd.DataFrame(records_vdown)
    df_up = pd.DataFrame(records_vup)
    
    with pd.ExcelWriter(filename) as writer:
        df_down.to_excel(writer, sheet_name="Vdown", index=False)
        df_up.to_excel(writer, sheet_name="Vup", index=False)
        
    print(f"\nCalibration data successfully exported to {filename}")

def calculate_relative_attenuation(input_filename="VVA_Calibration_Data.xlsx", output_filename="VVA_Attenuation_Data.xlsx"):
    """Reads raw data, normalizes to the 10V reading, and exports relative attenuation in dB."""
    print(f"\nReading raw data from {input_filename}...")
    try:
        raw_data = pd.read_excel(input_filename, sheet_name=None)
    except FileNotFoundError:
        print(f"Error: Could not find '{input_filename}'. Run the sweep first!")
        return
        
    with pd.ExcelWriter(output_filename) as writer:
        for sheet_name, df in raw_data.items():
            df_normalized = df.copy()
            baseline_col = "10.00V"
            voltage_cols = [col for col in df.columns if col != "Frequency (GHz)"]
            
            for col in voltage_cols:
                df_normalized[col] = df[col] - df[baseline_col]
                
            df_normalized.to_excel(writer, sheet_name=sheet_name, index=False)
            
    print(f"Post-processing complete! Normalized attenuation data saved to {output_filename}")


if __name__ == "__main__":
    print("--- VVA Calibration: Frequency & Voltage Sweep ---")
    
    # Sweep params
    f_start = float(input("Enter Start Frequency (GHz) [Default 110]: ") or 110)
    f_stop = float(input("Enter Stop Frequency (GHz) [Default 170]: ") or 170)
    freq_steps = int(input("Enter number of frequency steps [Default 30]: ") or 30)
    volt_points = int(input("Enter number of voltage points [Default 21]: ") or 21)
    
    # Initialize the module replaced SMU code
    vdi = VDIModuleController()
    vdi.connect()
    if not vdi.is_connected:
        print("Exiting due to VDI module connection failure.")
        exit()
    
    rm = pyvisa.ResourceManager()
    pna_address = 'GPIB0::16::INSTR' 
    pna = None
    
    try:
        print(f"\nConnecting to PNA...")
        pna = rm.open_resource(pna_address)
        pna.timeout = 10000  
        
        # Run the full routine
        rec_down, rec_up = run_vva_calibration_sweep(
            pna=pna, 
            vdi=vdi, 
            f_start_ghz=f_start, 
            f_stop_ghz=f_stop, 
            freq_steps=freq_steps, 
            volt_points=volt_points
        )
        
        # Export excel file
        export_vva_calibration(rec_down, rec_up, filename="VVA_Calibration_Data.xlsx")
        
        # Generate separate attn file
        calculate_relative_attenuation()
        
    except pyvisa.errors.VisaIOError as e:
        print(f"\nFailed to connect or communicate with the instruments: {e}")
    finally:
        if pna:
            print("Restoring PNA to continuous sweep...")
            pna.write("INIT1:CONT ON")
            pna.close()