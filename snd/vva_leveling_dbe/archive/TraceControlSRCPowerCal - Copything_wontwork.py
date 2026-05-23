import sys
import numpy as np
import pandas as pd
import pyvisa
import math
import time
from vdi_controller import VDIModuleController

def setup_pna_aux_triggers(pna):
    print("\n--- Initializing PNA Auxiliary Triggers ---")
    pna.write("TRIG:CHAN1:AUX1:ENAB ON")
    pna.write("TRIG:CHAN1:AUX1:OUTP:POL POS")
    pna.write("TRIG:CHAN1:AUX1:POS BEF")
    pna.write("TRIG:CHAN1:AUX1:OUTP:INT SWE")
    pna.write("TRIG:CHAN1:AUX1:OUTP:DUR 500e-6")
    pna.write("TRIG:CHAN1:AUX1:HAND OFF")
    
    pna.write("TRIG:CHAN1:AUX2:ENAB ON")
    pna.write("TRIG:CHAN1:AUX2:OUTP:POL POS")
    pna.write("TRIG:CHAN1:AUX2:POS BEF")
    pna.write("TRIG:CHAN1:AUX2:OUTP:INT POIN")
    pna.write("TRIG:CHAN1:AUX2:OUTP:DUR 500e-6")
    pna.write("TRIG:CHAN1:AUX2:HAND OFF")
    pna.query("*OPC?")
    print("Aux Trig 1 configured for PER SWEEP. Aux Trig 2 configured for PER POINT.")

# ============================================================================
# SOURCE POWER CALIBRATION
# ============================================================================
def apply_source_power_cal(pna, vdi, num_points, start_address=0, prn_file="VNAX 3437 Test Port Power.prn"):
    """
    Parses a local PRN file, injects it into the VNA's Source Power Cal table,
    executes the sweep, and applies the RREC math directly.
    """
    print("\n--- Executing Source Power Calibration (SPC) ---")
    import math 
    import time
    
    pna.write("*CLS")
    
    # 0. Preset-proofing: Force the VNA to build and select the R1 Trace
    trace_name = "R1_Trace"
    try: pna.write(f'CALC1:PAR:DEL "{trace_name}"')
    except: pass
    
    pna.write(f'CALC1:PAR:DEF:EXT "{trace_name}", "R1,1"')
    pna.write("DISP:WIND1:STATE ON")
    pna.write(f'DISP:WIND1:TRAC2:FEED "{trace_name}"')
    pna.write(f'CALC1:PAR:SEL "{trace_name}"')
    
    # 1. Set VDI to 10 Volts (baseline)
    print("Setting VDI to 10V baseline...")
    baseline_volts = np.full(num_points, 10.0)
    vdi.load_memory_sequence(start_address, baseline_volts)
    vdi.set_sweep_start_address(start_address)
    time.sleep(0.1)
    
    # 2. Parse PRN file locally from your PC
    print(f"Reading PRN Loss Table from your computer: {prn_file}")
    freqs = []
    powers = []
    with open(prn_file, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                try:
                    f_val = float(parts[0])
                    p_val = float(parts[1])
                    if not math.isnan(f_val) and not math.isnan(p_val):
                        freqs.append(f_val)
                        powers.append(p_val)
                except ValueError:
                    continue 
                    
    # Inject arrays directly into VNA Loss Table
    pna.write("SOUR1:POW:CORR:COLL:TABL:SEL LOSS")
    freq_str = ",".join([f"{val:.0f}" for val in freqs])
    data_str = ",".join([f"{val:.3f}" for val in powers])
    pna.write(f"SOUR1:POW:CORR:COLL:TABL:FREQ {freq_str}")
    pna.write(f"SOUR1:POW:CORR:COLL:TABL:DATA {data_str}")
    pna.write("SOUR1:POW:CORR:COLL:TABL:LOSS ON")
    
    # 3. Acquire using internal R1
    print("Acquiring Source Power Calibration... (Waiting for VNA Sweep)")
    pna.write('SOUR1:POW:CORR:COLL:ACQ REC,"R1"')
    pna.query("*OPC?") 
    
    err = pna.query("SYST:ERR?").strip()
    if "+0" not in err and "No error" not in err:
        print(f"\n[ERROR] Acquisition Failed! VNA says: {err}")
        return
    
    # 4. Save with the RREC Argument 
    print("Saving Source Calibration AND Reference Receiver Calibration to PNA...")
    pna.write("SOUR1:POW:CORR:COLL:SAVE RREC")
    pna.query("*OPC?")
    
    # 5. Apply the Math & Ki
    print("disabling SRC Power Cal Corrections")
    #pna.write("SENS1:CORR:STAT ON") # Link the new RREC math to live sweeps
    pna.write("SOUR1:POW:CORR OFF") # Kill the ALC to prevent multiplier starvation
    
    # 6. Take a fresh live sweep so the screen updates immediately
    pna.write("DISP:UPD ON")
    pna.query("INIT1:IMM; *OPC?")
    
    print("\nSource Power Calibration Complete! Check the PNA screen to verify the live R1 trace shifted.")

# ============================================================================
# FLAT TRACE FUNCTION
# ============================================================================
def flat_output(pna, vdi, goal_value, num_points, f_start_ghz, f_stop_ghz, start_address=0, atten_file="VVA_Attenuation_Data.xlsx", max_iters=4, tolerance=0.15):
    print(f"\n--- Flattening Trace to {goal_value} dBm at Memory Address {start_address} ---")

    trace_name = "R1_Trace"
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
                accumulated_req_atten[i] += error * damping_factor 
                
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
                accumulated_req_atten[i] += error * damping_factor
                
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
#  CAL-SET INJECTION 
# ============================================================================
def apply_direct_calset_injection(pna, vdi, num_points, f_start_ghz, f_stop_ghz, sweep_type='LIN', start_address=0, prn_file="VNAX 3437 Test Port Power.prn"):
    """
    janky injection of tpp into calset that will probably break everything yeehaw
    """
    print("\n--- Executing Direct CalSet Injection (Response Tracking) ---")
    import math 
    import time
    
    pna.write("*CLS")
    
    # 0. Wipe the slate clean to prevent Error -168
    print("Initializing Trace and Channels...")
    try: pna.write("CALC1:PAR:DEL:ALL") # Kill the factory default S11 trace
    except: pass
    
    trace_name = "R1_Trace"
    pna.write(f'CALC1:PAR:DEF:EXT "{trace_name}", "R1,1"')
    pna.write("DISP:WIND1:STATE ON")
    pna.write(f'DISP:WIND1:TRAC2:FEED "{trace_name}"')
    pna.write(f'CALC1:PAR:SEL "{trace_name}"')
    pna.write("CALC1:FORM MLOG")
    pna.write("SENS1:CORR:STAT OFF") # Ensure we are reading absolute raw data
    
    # 1. Set VDI to 10 Volts (baseline)
    print("Setting VDI to 10V baseline...")
    baseline_volts = np.full(num_points, 10.0)
    vdi.load_memory_sequence(start_address, baseline_volts)
    vdi.set_sweep_start_address(start_address)
    time.sleep(0.1)
    
    # 2. Capture the Raw Baseline Sweep
    print("Capturing raw R1 baseline sweep...")
    
    # TRIGGER SAFETY LOCK: Force Hold mode before sending immediate trigger
    pna.write("INIT1:CONT OFF")
    pna.write("DISP:UPD ON") 
    pna.query("*OPC?") # Wait for settings to settle
    
    # Take ONE clean sweep
    pna.query("INIT1:IMM; *OPC?")
    
    pna.write(f'CALC1:PAR:SEL "{trace_name}"')
    raw_baseline = np.array(pna.query_ascii_values("CALC1:DATA? FDATA"))
    
    # 3. Parse PRN file locally
    print(f"Reading PRN Loss Table from your computer: {prn_file}")
    prn_freqs = []
    prn_powers = []
    with open(prn_file, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                try:
                    f_val = float(parts[0]) / 1e9 # Convert Hz to GHz
                    p_val = float(parts[1])
                    if not math.isnan(f_val) and not math.isnan(p_val):
                        prn_freqs.append(f_val)
                        prn_powers.append(p_val)
                except ValueError:
                    continue 
                    
    if sweep_type.upper() == 'CW':
        sweep_freqs = np.full(num_points, f_start_ghz)
    else:
        sweep_freqs = np.linspace(f_start_ghz, f_stop_ghz, num_points)
        
    interp_target_pwr = np.interp(sweep_freqs, prn_freqs, prn_powers)
    
    # 4. Calculate the Response Tracking Error Term
    print("Calculating Response Tracking error terms...")
    # Math: Corrected = Raw - ErrorTerm_dB
    # Therefore: ErrorTerm_dB = Raw - Target
    err_db = raw_baseline - interp_target_pwr
    
    # Convert dB to linear magnitude (Keysight error terms are linear)
    linear_mag = 10 ** (err_db / 20.0)
    
    # Build interleaved complex array (Real, Imag)
    err_term_array = np.zeros(num_points * 2)
    err_term_array[0::2] = linear_mag  # Real magnitude
    err_term_array[1::2] = 0.0         # Imaginary is 0
    
    err_term_str = ",".join([f"{val:.6f}" for val in err_term_array])
    
    # 5. Build the CalSet Bucket and Inject
    print("Injecting mathematical array into VNA CalSet...")
    cset_name = "VDI_R1_CAL"
    
    # Delete it if it already exists so we get a fresh bucket without conflicts
    try: pna.write(f'SENS1:CORR:CSET:DEL "{cset_name}"')
    except: pass
    
    pna.write(f'SENS1:CORR:CSET:CREate "{cset_name}"')
    
    # Attach the empty bucket to the active channel
    pna.write(f'SENS1:CORR:CSET:ACTivate "{cset_name}", 1')
    
    # Use the PNA-specific ETERm command with your golden string!
    pna.write(f'SENS1:CORR:CSET:ETERm "Response Tracking (a1)", {err_term_str}')
    pna.query("*OPC?")

    # 6. Apply to Live Sweeps
    print("Enabling CalSet Corrections...")
    
    # THE FINAL LINK: Tell the measurement to use our bucket as a generic Response Cal!
    pna.write('CALC1:CORR:TYPE "Response"')
    pna.query("*OPC?")
    
    pna.write("SENS1:CORR:STAT ON")
    
    # Take a final live sweep to update display
    pna.write("INIT1:CONT OFF")
    pna.query("INIT1:IMM; *OPC?")
    
    # Error Check
    err = pna.query("SYST:ERR?").strip()
    if "+0" not in err and "No error" not in err:
         print(f"\n[WARNING] VNA reported: {err}")
    else:
         print("\nDirect CalSet Injection Complete! Check the PNA screen to verify the live R1 trace is shifted.")


# ============================================================================
# ========= MAIN INTERFACE
# ============================================================================
if __name__ == "__main__":
    
    print("=========================================")
    print("        VVA Trace Control System         ")
    print("=========================================")

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
        # We do NOT send *CLS here, because we don't want to break the state loading
        setup_pna_aux_triggers(pna) 
        pna.timeout = 300000        
        
        pna.write("TRIG:SOUR IMM")
        pna.write("INIT1:CONT OFF") 
        
        # ==========================================
        # 1. Global Sweep Setup
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
        # 2. Source Power Cal 
        # ==========================================
        run_spc = input("\nRun error injection (y/n) [Default n]: ").strip().lower()
        
        if run_spc == 'y':
            prn_path = "VNAX 3437 Test Port Power.prn"
            
            
            apply_direct_calset_injection(
                pna=pna, 
                vdi=vdi, 
                num_points=num_points,
                f_start_ghz=f_start,
                f_stop_ghz=f_stop,
                start_address=start_addr,
                prn_file=prn_path 
            )
            
            input("\n[PAUSED] R1 = TPP ???? .\nPress Enter to continue to the operations menu...")
        else:
            print("\nSkipping SPC. Proceeding with the VNA's current correction state.")
            
        # ==========================================
        # 3. Operations Menu
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
            
        iterations = int(input("Enter max iterations [Default 4]: ") or 4)
        tolerance = float(input("Enter tolerance [Default 0.15]: ") or 0.15)
        
        # ==========================================
        # ROUTE 1 - FLATTEN TRACE
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
        # ROUTE 2 - POWER RAMP
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

    except pyvisa.errors.VisaIOError as e:
        print(f"\nInstrument communication error: {e}")
    except FileNotFoundError as e:
        print(f"\nError: File not found ({e}). Please ensure your Excel file or PRN file is in the same folder as this Python script.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        if pna:
            print("Restoring PNA to continuous sweep and closing connection...")
            pna.write("INIT1:CONT ON")
            pna.close()