import sys
import numpy as np
import pandas as pd
import pyvisa
from vdi_controller import VDIModuleController
import time

def setup_pna_aux_triggers(pna):
    """
    Configures the Aux Trig 1 and Aux Trig 2 settings on the Keysight PNA.
    Run this once during instrument initialization.
    """
    print("\n--- Initializing PNA Auxiliary Triggers ---")
    
    # AUX TRIG 1 SETUP (Triggers once per Sweep)
    pna.write("TRIG:CHAN1:AUX1:ENAB ON")
    pna.write("TRIG:CHAN1:AUX1:OUTP:POL POS")
    pna.write("TRIG:CHAN1:AUX1:POS BEF")
    pna.write("TRIG:CHAN1:AUX1:OUTP:INT SWE")
    pna.write("TRIG:CHAN1:AUX1:OUTP:DUR 500e-6")
    pna.write("TRIG:CHAN1:AUX1:HAND OFF")
    
    # AUX TRIG 2 SETUP (Triggers once per Point)
    pna.write("TRIG:CHAN1:AUX2:ENAB ON")
    pna.write("TRIG:CHAN1:AUX2:OUTP:POL POS")
    pna.write("TRIG:CHAN1:AUX2:POS BEF")
    pna.write("TRIG:CHAN1:AUX2:OUTP:INT POIN")
    pna.write("TRIG:CHAN1:AUX2:OUTP:DUR 500e-6")
    pna.write("TRIG:CHAN1:AUX2:HAND OFF")
    
    pna.query("*OPC?")
    print("Aux Trig 1 configured for PER SWEEP. Aux Trig 2 configured for PER POINT.")

# ============================================================================
# TEST PORT POWER CALIBRATION (SMEM INJECTION) WONKY
# ============================================================================
def apply_tpp_calibration(pna, vdi, num_points, f_start_ghz, f_stop_ghz, sweep_type='LIN', start_address=0, tpp_file="(VNAX 3437) Test Port Power.csv"):
    """
    Applies a frequency-dependent offset to the R1 trace using SMEM.
    This visually shifts the trace to match the test port power.
    """
    print("\n--- Applying Test Port Power (TPP) Calibration ---")
    trace_name = "R1_Trace"
    
    # 1. Setup raw trace
    pna.write(f'CALC1:PAR:DEF:EXT "{trace_name}", "R1,1"')
    pna.write("DISP:WIND1:STATE ON")
    pna.write(f'DISP:WIND1:TRAC2:FEED "{trace_name}"')
    pna.write("FORM:DATA ASC,0")
    pna.write("CALC1:MATH:FUNC NORM")
    
    # 2. Get Raw Baseline at 10V
    print("Setting VDI to 10V to measure raw Test Port Power...")
    baseline_volts = np.full(num_points, 10.0)
    vdi.load_memory_sequence(start_address, baseline_volts)
    vdi.set_sweep_start_address(start_address)
    
    time.sleep(0.05)
    
    # Dummy + Real sweep
    pna.write("DISP:UPD OFF")
    pna.query("INIT1:IMM; *OPC?")
    pna.write("DISP:UPD ON")
    pna.query("INIT1:IMM; *OPC?")
    
    pna.write(f'CALC1:PAR:SEL "{trace_name}"')
    raw_baseline = pna.query_ascii_values("CALC1:DATA? FDATA")
    
    # 3. Load CSV
    print(f"Calculating offsets using {tpp_file}...")
    tpp_df = pd.read_csv(tpp_file, skiprows=35)
    csv_freqs = tpp_df['Freq(GHz)'].values
    csv_source_pwr = tpp_df['Source (dBm)'].values
    
    if sweep_type.upper() == 'CW':
        sweep_freqs = np.full(num_points, f_start_ghz)
    else:
        sweep_freqs = np.linspace(f_start_ghz, f_stop_ghz, num_points)
        
    interp_source_pwr = np.interp(sweep_freqs, csv_freqs, csv_source_pwr)
    
    # 4. Calculate SMEM Array
    # Target: Final(dBm) = Raw(dBm) + Offset(dB)
    # Trace Math DIV: Final = Raw - Mem(dB)
    # Mem(dB) = -Offset(dB)
    offset_db = interp_source_pwr - np.array(raw_baseline)
    mem_db = -offset_db
    
    # Convert Mem(dB) to linear magnitude for complex array (20*log10(mag) = mem_db)
    linear_mag = 10 ** (mem_db / 20.0)
    
    # Construct interleaved [Real, Imag, Real, Imag...] array
    smem_array = np.zeros(num_points * 2)
    smem_array[0::2] = linear_mag  # Real parts
    smem_array[1::2] = 0.0         # Imag parts
    
    # 5. Inject into PNA
    pna.write("CALC1:MATH:MEM") 
    pna.query("*OPC?")
    
    # Write directly to Standard Memory accepts only complex values
    smem_str = ",".join([f"{val:.6f}" for val in smem_array])
    pna.write(f"CALC1:DATA SMEM,{smem_str}")
    pna.query("*OPC?")
    
    # Turn on Data/Memory 
    pna.write("CALC1:MATH:FUNC DIV")
    pna.query("*OPC?")
    
    # 6. Verify m corrected baseline
    pna.query("INIT1:IMM; *OPC?")
    pna.write(f'CALC1:PAR:SEL "{trace_name}"')
    corrected_baseline = pna.query_ascii_values("CALC1:DATA? FDATA")
    
    print("\n--- TRACE MATH VERIFICATION ---")
    print(f"{'Freq (GHz)':<12} | {'Raw R1 (dBm)':<15} | {'CSV Target (dBm)':<18} | {'Corrected PNA (dBm)':<20}")
    print("-" * 73)
    
    for i in list(range(5)) + list(range(num_points-5, num_points)):
        if i == num_points - 5:
            print("...          | ...             | ...                | ...")
        print(f"{sweep_freqs[i]:<12.3f} | {raw_baseline[i]:<15.2f} | {interp_source_pwr[i]:<18.2f} | {corrected_baseline[i]:<20.2f}")
        
    print("\nTPP Calibration Applied Successfully")

# ============================================================================
# FLAT TRACE FUNCTION
# ============================================================================
def flat_output(pna, vdi, goal_value, num_points, f_start_ghz, f_stop_ghz, start_address=0, atten_file="VVA_Attenuation_Data.xlsx", max_iters=4, tolerance=0.15):
    print(f"\n--- Flattening Trace to {goal_value} dBm at Memory Address {start_address} ---")

    trace_name = "R1_Trace"
    
    # load bearing dummy sweep
    pna.query("INIT1:IMM; *OPC?")
    pna.query("INIT1:IMM; *OPC?") 
    
    pna.write(f'CALC1:PAR:SEL "{trace_name}"')
    baseline_trace = pna.query_ascii_values("CALC1:DATA? FDATA")
    
    print(f"Loading calibration data from {atten_file}...")
    atten_df = pd.read_excel(atten_file, sheet_name="Vdown")
    cal_freqs = atten_df['Frequency (GHz)'].values
    volt_cols = [c for c in atten_df.columns if c != 'Frequency (GHz)']
    cal_volts = np.array([float(c.replace('V', '')) for c in volt_cols])
    cal_atten = atten_df[volt_cols].values 
    
    sweep_freqs = np.linspace(f_start_ghz, f_stop_ghz, num_points)
    
    target_voltages = np.zeros(num_points)
    accumulated_req_atten = np.zeros(num_points)
    current_trace = baseline_trace.copy()
    
    damping_factor = 0.9

    for iteration in range(max_iters):
        print(f"\n=== Iteration {iteration + 1} of {max_iters} ===")
        print(f"{'Freq (GHz)':<12} | {'Actual (dBm)':<15} | {'Error (dB)':<12} | {'Req Atten (dB)':<16} | {'Target Volt (V)':<15}")
        print("-" * 78)
        
        errors = np.zeros(num_points)
        
        for i, freq in enumerate(sweep_freqs):
            actual_power = current_trace[i]
            
            if iteration == 0:
                error = goal_value - actual_power
                accumulated_req_atten[i] = error
            else:
                error = goal_value - actual_power
                accumulated_req_atten[i] += error*damping_factor 
                
            errors[i] = error
            req_atten = accumulated_req_atten[i]
            
            if req_atten >= 0:
                target_voltages[i] = 10.0
            else:
                interp_atten_at_f = np.zeros(len(cal_volts))
                for j in range(len(cal_volts)):
                    interp_atten_at_f[j] = np.interp(freq, cal_freqs, cal_atten[:, j])
                    
                sort_idx = np.argsort(interp_atten_at_f)
                sorted_atten = interp_atten_at_f[sort_idx]
                sorted_volts = cal_volts[sort_idx]
                
                if req_atten < sorted_atten[0]:
                    target_voltages[i] = 0.0  
                else:
                    target_voltages[i] = np.interp(req_atten, sorted_atten, sorted_volts)
                    
            print(f"{freq:<12.3f} | {actual_power:<15.2f} | {error:<12.2f} | {req_atten:<16.2f} | {target_voltages[i]:<15.3f}")
            
        if iteration > 0:
            max_error_this_pass = np.max(np.abs(errors))
            print(f"\nMax Error this pass: {max_error_this_pass:.2f} dB")
            if max_error_this_pass <= tolerance:
                print(f"Tolerance of {tolerance} dB met.")
                break
                
        vdi.load_memory_sequence(start_address, target_voltages)
        vdi.set_sweep_start_address(start_address)
        
        pna.write("DISP:UPD OFF")
        pna.query("INIT1:IMM; *OPC?")
        pna.write("DISP:UPD ON")

        pna.query("INIT1:IMM; *OPC?") 
        pna.write(f'CALC1:PAR:SEL "{trace_name}"')
        current_trace = pna.query_ascii_values("CALC1:DATA? FDATA")

    print("\nFlattening complete")
    return target_voltages


# ============================================================================
# RAMP FUNCTIONS
# ============================================================================
def ramp_output(pna, vdi, start_power, stop_power, num_points, f_start_ghz, f_stop_ghz=None, sweep_type='LIN', start_address=0, atten_file="VVA_Attenuation_Data.xlsx", max_iters=4, tolerance=0.15):
    
    print(f"\n--- Generating Power Ramp ({start_power} dBm to {stop_power} dBm) in {sweep_type.upper()} Mode ---")
    
    trace_name = "R1_Trace"
    
    #load bearing dummy sweep
    pna.query("INIT1:IMM; *OPC?")
    pna.query("INIT1:IMM; *OPC?") 
    
    pna.write(f'CALC1:PAR:SEL "{trace_name}"')
    baseline_trace = pna.query_ascii_values("CALC1:DATA? FDATA")
    
    target_power = np.linspace(start_power, stop_power, num_points)
    
    print(f"Loading calibration data from {atten_file}...")
    atten_df = pd.read_excel(atten_file, sheet_name="Vdown")
    cal_freqs = atten_df['Frequency (GHz)'].values
    volt_cols = [c for c in atten_df.columns if c != 'Frequency (GHz)']
    cal_volts = np.array([float(c.replace('V', '')) for c in volt_cols])
    cal_atten = atten_df[volt_cols].values 
    
    if sweep_type.upper() == 'CW':
        sweep_freqs = np.full(num_points, f_start_ghz)
    else:
        sweep_freqs = np.linspace(f_start_ghz, f_stop_ghz, num_points)

    target_voltages = np.zeros(num_points)
    accumulated_req_atten = np.zeros(num_points)
    current_trace = baseline_trace.copy()

    damping_factor = 0.9
    
    for iteration in range(max_iters):
        print(f"\n=== Iteration {iteration + 1} of {max_iters} ===")
        print(f"{'Freq (GHz)':<12} | {'Actual (dBm)':<15} | {'Error (dB)':<12} | {'Target Pwr':<12} | {'Target Volt (V)':<15}")
        print("-" * 75)
        
        errors = np.zeros(num_points)

        for i, freq in enumerate(sweep_freqs):
            actual_power = current_trace[i]
            target_p = target_power[i]
            
            if iteration == 0:
                error = target_p - actual_power
                accumulated_req_atten[i] = error
            else:
                error = target_p - actual_power
                accumulated_req_atten[i] += error*damping_factor
                
            errors[i] = error
            req_atten = accumulated_req_atten[i]
            
            if req_atten >= 0:
                target_voltages[i] = 10.0
            else:
                interp_atten_at_f = np.zeros(len(cal_volts))
                for j in range(len(cal_volts)):
                    interp_atten_at_f[j] = np.interp(freq, cal_freqs, cal_atten[:, j])
                    
                sort_idx = np.argsort(interp_atten_at_f)
                sorted_atten = interp_atten_at_f[sort_idx]
                sorted_volts = cal_volts[sort_idx]
                
                if req_atten < sorted_atten[0]:
                    target_voltages[i] = 0.0 
                else:
                    target_voltages[i] = np.interp(req_atten, sorted_atten, sorted_volts)

            print(f"{freq:<12.3f} | {actual_power:<15.2f} | {error:<12.2f} | {target_p:<12.2f} | {target_voltages[i]:<15.3f}")   
            
        if iteration > 0:
            max_error_this_pass = np.max(np.abs(errors))
            print(f"\nMax Error this pass: {max_error_this_pass:.2f} dB")
            if max_error_this_pass <= tolerance:
                print(f"Tolerance of {tolerance} dB met.")
                break
                
        vdi.load_memory_sequence(start_address, target_voltages)
        vdi.set_sweep_start_address(start_address)

        pna.write("DISP:UPD OFF")
        pna.query("INIT1:IMM; *OPC?")
        pna.write("DISP:UPD ON")
        
        pna.query("INIT1:IMM; *OPC?") 
        pna.write(f'CALC1:PAR:SEL "{trace_name}"')
        current_trace = pna.query_ascii_values("CALC1:DATA? FDATA")
    
    print("\nRamp generation complete")
    return target_voltages

# ============================================================================
# ========= MAAAAAIN
# ============================================================================
if __name__ == "__main__":
    
    print("=========================================")
    print("        VVA Trace Control System         ")
    print("=========================================")

    # ==========================================
    # Hardware Initialization
    # ==========================================
    print("\nConnecting to VDI Module...")
    vdi = VDIModuleController()
    vdi.connect()
    
    if not vdi.is_connected:
        print("Failed to connect to the VDI module. Exiting test.")
        sys.exit(1)
        
    rm = pyvisa.ResourceManager()
    pna_address = 'GPIB0::16::INSTR'
    pna = None
    
    try:
        print(f"Connecting to PNA at {pna_address}...")
        pna = rm.open_resource(pna_address)
        pna.write("*CLS")           
        setup_pna_aux_triggers(pna) 
        pna.timeout = 60000         
        
        pna.write("TRIG:SOUR IMM")
        pna.write("INIT1:CONT OFF") 
        
        # ==========================================
        #  Sweep Setup
        # ==========================================
        print("\n--- Global Sweep Setup ---")
        sweep_type = input("Enter sweep type ('LIN' or 'CW') [Default LIN]: ").strip().upper() or 'LIN'
        
        if sweep_type == 'CW':
            f_start = float(input("Enter CW Frequency (GHz) [Default 110.0]: ") or 110.0)
            f_stop = f_start 
            pna.write("SENS1:SWE:TYPE CW")
            pna.write(f"SENS1:FREQ:CW {f_start}E9")
        else:
            f_start = float(input("Enter Start Frequency (GHz) [Default 110.0]: ") or 110.0)
            f_stop = float(input("Enter Stop Frequency (GHz) [Default 170.0]: ") or 170.0)
            pna.write("SENS1:SWE:TYPE LIN")
            pna.write(f"SENS1:FREQ:STAR {f_start}E9")
            pna.write(f"SENS1:FREQ:STOP {f_stop}E9")
            
        num_points = int(input("Enter number of trace points [Default 101]: ") or 101)
        start_addr = int(input("Enter starting memory address [Default 0]: ") or 0)
        
        pna.write(f"SENS1:SWE:POIN {num_points}")
        pna.write("SENS1:SWE:DWEL 0.002")
        
        # ==========================================
        # Apply Calibration & Display Baseline
        # ==========================================
        apply_tpp_calibration(
            pna=pna, 
            vdi=vdi, 
            num_points=num_points, 
            f_start_ghz=f_start, 
            f_stop_ghz=f_stop, 
            sweep_type=sweep_type, 
            start_address=start_addr,
            tpp_file="(VNAX 3437) Test Port Power.csv"
        )
        
        # Pause the script so the user can verify the max power on the PNA screen
        input("\n[PAUSED] Reference adjusted to TPP \nPress Enter to continue to the operations menu...")

        # ==========================================
        #   Menu
        # ==========================================
        print("\n=========================================")
        print("Select an operation mode:")
        print(" [1] Flatten a trace (Constant Power)")
        print(" [2] Generate a Power Ramp")
        print("=========================================")
        
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice not in ['1', '2']:
            print("Invalid selection. Exiting.")
            sys.exit(1)

        # Prompt for parameters shared by both routines
        iterations = int(input("Enter max iterations [Default 4]: ") or 4)
        tolerance = float(input("Enter tolerance [Default 0.15]: ") or 0.15)

        # ==========================================
        # Rt 1: FLATTEN TRACE
        # ==========================================
        if choice == '1':
            goal_val = float(input("Enter goal power level in dBm [Default -5.0]: ") or -5.0)
            
            calculated_voltages = flat_output(
                pna=pna,
                vdi=vdi,
                goal_value=goal_val,
                num_points=num_points,
                f_start_ghz=f_start,
                f_stop_ghz=f_stop,
                start_address=start_addr,
                atten_file="VVA_Attenuation_Data.xlsx",
                max_iters=iterations,
                tolerance=tolerance
            )
            
        # ==========================================
        # Rt 2: POWER RAMP
        # ==========================================
        elif choice == '2':
            start_pwr = float(input("Enter Ramp Start Power (dBm) [Default -10.0]: ") or -10.0)
            stop_pwr = float(input("Enter Ramp Stop Power (dBm) [Default -1.0]: ") or -1.0)
            
            calculated_voltages = ramp_output(
                pna=pna,
                vdi=vdi,
                start_power=start_pwr,
                stop_power=stop_pwr,
                num_points=num_points,
                f_start_ghz=f_start,
                f_stop_ghz=f_stop,
                sweep_type=sweep_type,
                start_address=start_addr,
                atten_file="VVA_Attenuation_Data.xlsx",
                max_iters=iterations,
                tolerance=tolerance
            )
            
        print(f"\nSuccess! Loaded {len(calculated_voltages)} points into memory starting at address {start_addr}.")

    # ==========================================
    # Error Handling & Cleanup
    # ==========================================
    except pyvisa.errors.VisaIOError as e:
        print(f"\nInstrument communication error: {e}")
    except FileNotFoundError:
        print("\nError: 'VVA_Attenuation_Data.xlsx' or TPP Calibration CSV not found. ensure files are in the same directory.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        if pna:
            print("\nRestoring PNA to continuous sweep and closing connection...")
            pna.write("INIT1:CONT ON")
            pna.close()

