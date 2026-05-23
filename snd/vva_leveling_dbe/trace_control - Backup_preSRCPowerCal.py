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
    
    # ==========================================================
    # AUX TRIG 1 SETUP (Triggers once per Sweep)
    # ==========================================================
    pna.write("TRIG:CHAN1:AUX1:ENAB ON")          # Enable: Checked
    pna.write("TRIG:CHAN1:AUX1:OUTP:POL POS")     # Polarity: Positive Pulse
    pna.write("TRIG:CHAN1:AUX1:POS BEF")          # Position: Before Acquisition
    pna.write("TRIG:CHAN1:AUX1:OUTP:INT SWE")     # Per Point: OFF (Trigger per SWEep)
    pna.write("TRIG:CHAN1:AUX1:OUTP:DUR 500e-6")  # Pulse Duration: 500 us (0.0005s)
    pna.write("TRIG:CHAN1:AUX1:HAND OFF")         # Wait-for-Device Handshake: OFF
    
    # ==========================================================
    # AUX TRIG 2 SETUP (Triggers once per Point)
    # ==========================================================
    pna.write("TRIG:CHAN1:AUX2:ENAB ON")          # Enable: Checked
    pna.write("TRIG:CHAN1:AUX2:OUTP:POL POS")     # Polarity: Positive Pulse
    pna.write("TRIG:CHAN1:AUX2:POS BEF")          # Position: Before Acquisition
    pna.write("TRIG:CHAN1:AUX2:OUTP:INT POIN")    # Per Point: ON (Trigger per POINt)
    pna.write("TRIG:CHAN1:AUX2:OUTP:DUR 500e-6")  # Pulse Duration: 500 us (0.0005s)
    pna.write("TRIG:CHAN1:AUX2:HAND OFF")         # Wait-for-Device Handshake: OFF
    
    # ensure the PNA registers the changes
    pna.query("*OPC?")
    print("Aux Trig 1 configured for PER SWEEP. Aux Trig 2 configured for PER POINT.")


# ============================================================================
# FLAT TRACE FUNCTION
# ============================================================================
def flat_output(pna, vdi, goal_value, num_points, f_start_ghz, f_stop_ghz, start_address=0, atten_file="VVA_Attenuation_Data.xlsx", max_iters=4, tolerance=0.15):
    """
    Reads the baseline reference trace, calculates the required voltages to flatten 
    the output to the goal_value, and uses an iterative approach to dial 
    in the voltages
    """
    print(f"\n--- Flattening Trace to {goal_value} dB at Memory Address {start_address} ---")

    # ==========================================================
    # Configure the PNA for the Sweep Parameters
    # ==========================================================
    pna.write(f"SENS1:SWE:POIN {num_points}")
    pna.write(f"SENS1:FREQ:STAR {f_start_ghz}E9")
    pna.write(f"SENS1:FREQ:STOP {f_stop_ghz}E9")

    
    # ==========================================================
    # Capture Baseline Trace
    # ==========================================================
    print("Setting VVA to minimum attenuation for baseline sweep...")
    baseline_volts = np.full(num_points, 10.0)
    vdi.load_memory_sequence(start_address, baseline_volts)
    vdi.set_sweep_start_address(start_address)
    
    trace_name = "R1_Trace"
    pna.write(f'CALC1:PAR:DEF:EXT "{trace_name}", "R1,1"')
    pna.write("DISP:WIND1:STATE ON")
    pna.write(f'DISP:WIND1:TRAC2:FEED "{trace_name}"')
    pna.write("FORM:DATA ASC,0")
    
    
    # load bearing dummy sweep
    pna.query("INIT1:IMM; *OPC?")

    pna.query("INIT1:IMM; *OPC?") 
    
    pna.write(f'CALC1:PAR:SEL "{trace_name}"')
    baseline_trace = pna.query_ascii_values("CALC1:DATA? FDATA")
    
    # ==========================================================
    # Load the Calibration Data
    # ==========================================================
    print(f"Loading calibration data from {atten_file}...")
    atten_df = pd.read_excel(atten_file, sheet_name="Vdown")
    cal_freqs = atten_df['Frequency (GHz)'].values
    volt_cols = [c for c in atten_df.columns if c != 'Frequency (GHz)']
    cal_volts = np.array([float(c.replace('V', '')) for c in volt_cols])
    cal_atten = atten_df[volt_cols].values 
    
    sweep_freqs = np.linspace(f_start_ghz, f_stop_ghz, num_points)
    
    # Arrays to hold our running data across iterations
    target_voltages = np.zeros(num_points)
    accumulated_req_atten = np.zeros(num_points)
    current_trace = baseline_trace.copy()
    

    # ==========================================================
    # Iterative Flattening
    # ==========================================================
    
    #added damping factor to avoid overshoots on corrections
    damping_factor = 0.9

    for iteration in range(max_iters):
        print(f"\n=== Iteration {iteration + 1} of {max_iters} ===")
        print(f"{'Freq (GHz)':<12} | {'Actual (dBm)':<15} | {'Error (dB)':<12} | {'Req Atten (dB)':<16} | {'Target Volt (V)':<15}")
        print("-" * 78)
        
        errors = np.zeros(num_points)
        
        for i, freq in enumerate(sweep_freqs):
            actual_power = current_trace[i]
            
            if iteration == 0:
                # Pass 1: Compare against the 10V baseline
                error = goal_value - actual_power
                accumulated_req_atten[i] = error
            else:
                # Pass 2+: Compare actual measured power against the goal and accumulate the error
                error = goal_value - actual_power
                accumulated_req_atten[i] += error*damping_factor 
                
            errors[i] = error
            req_atten = accumulated_req_atten[i]
            
            # If the trace is already below the goal at minimum attenuation, clamp to 10V
            if req_atten >= 0:
                target_voltages[i] = 10.0
            else:
                # Build Attenuation vs. Voltage curve for this specific frequency
                interp_atten_at_f = np.zeros(len(cal_volts))
                for j in range(len(cal_volts)):
                    interp_atten_at_f[j] = np.interp(freq, cal_freqs, cal_atten[:, j])
                    
                sort_idx = np.argsort(interp_atten_at_f)
                sorted_atten = interp_atten_at_f[sort_idx]
                sorted_volts = cal_volts[sort_idx]
                
                # Check if we are demanding more attenuation than the VVA can provide
                if req_atten < sorted_atten[0]:
                    target_voltages[i] = 0.0  # Clamp to max attenuation
                else:
                    target_voltages[i] = np.interp(req_atten, sorted_atten, sorted_volts)
                    
            print(f"{freq:<12.3f} | {actual_power:<15.2f} | {error:<12.2f} | {req_atten:<16.2f} | {target_voltages[i]:<15.3f}")
            
        # Check if hit target tolerance early
        if iteration > 0:
            max_error_this_pass = np.max(np.abs(errors))
            print(f"\nMax Error this pass: {max_error_this_pass:.2f} dB")
            if max_error_this_pass <= tolerance:
                print(f"Tolerance of {tolerance} dB met.")
                break
                
        # Load the new calculated voltages into the module
        vdi.load_memory_sequence(start_address, target_voltages)
        vdi.set_sweep_start_address(start_address)
        
        #load bearing dummy sweep
        #turns off display for this one because it looks very weird then turns it back on
        pna.write("DISP:UPD OFF")
        pna.query("INIT1:IMM; *OPC?")
        pna.write("DISP:UPD ON")

        # Trigger the PNA to read the newly applied voltages for the next iteration
        pna.query("INIT1:IMM; *OPC?") 
        pna.write(f'CALC1:PAR:SEL "{trace_name}"')
        current_trace = pna.query_ascii_values("CALC1:DATA? FDATA")

    print("\nFlattening complete")
    return target_voltages


# ============================================================================
# RAMP FUNCTIONS
# ============================================================================

def ramp_output(pna, vdi, start_power, stop_power, num_points, f_start_ghz, f_stop_ghz=None, sweep_type='LIN', start_address=0, atten_file="VVA_Attenuation_Data.xlsx", max_iters=4, tolerance=0.15):
    """
    Reads the baseline reference trace, calculates the required voltages to create a 
    power ramp, and uses an iterative closed-loop approach to dial in the voltages.
    Supports both Linear frequency sweeps and CW power sweeps.
    """
    print(f"\n--- Generating Power Ramp ({start_power} dBm to {stop_power} dBm) in {sweep_type.upper()} Mode ---")
    
    # ==========================================================
    #  Configure the PNA for the Sweep Mode
    # ==========================================================
    pna.write(f"SENS1:SWE:POIN {num_points}")
    
    if sweep_type.upper() == 'CW':
        pna.write("SENS1:SWE:TYPE CW")
        pna.write(f"SENS1:FREQ:CW {f_start_ghz}E9")
        sweep_freqs = np.full(num_points, f_start_ghz)
        print(f"PNA configured for CW Sweep at {f_start_ghz} GHz.")
    else:
        pna.write("SENS1:SWE:TYPE LIN")
        pna.write(f"SENS1:FREQ:STAR {f_start_ghz}E9")
        pna.write(f"SENS1:FREQ:STOP {f_stop_ghz}E9")
        sweep_freqs = np.linspace(f_start_ghz, f_stop_ghz, num_points)
        print(f"PNA configured for Linear Sweep from {f_start_ghz} to {f_stop_ghz} GHz.")

    # ==========================================================
    # Capture Baseline Trace
    # ==========================================================
    print("Capturing baseline sweep at minimum attenuation...")
    baseline_volts = np.full(num_points, 10.0)
    vdi.load_memory_sequence(start_address, baseline_volts)
    vdi.set_sweep_start_address(start_address)
    
    trace_name = "R1_Trace"
    pna.write(f'CALC1:PAR:DEF:EXT "{trace_name}", "R1,1"')
    pna.write("DISP:WIND1:STATE ON")
    pna.write(f'DISP:WIND1:TRAC2:FEED "{trace_name}"')
    pna.write("FORM:DATA ASC,0")
    
    #load bearing dummy sweep
    pna.query("INIT1:IMM; *OPC?")
    

    pna.query("INIT1:IMM; *OPC?") 
    pna.write(f'CALC1:PAR:SEL "{trace_name}"')
    baseline_trace = pna.query_ascii_values("CALC1:DATA? FDATA")
    
    # ==========================================================
    # Generate the Target Power Array
    # ==========================================================
    target_power = np.linspace(start_power, stop_power, num_points)
    
    # ==========================================================
    # Load Calibration Data
    # ==========================================================
    print(f"Loading calibration data from {atten_file}...")
    atten_df = pd.read_excel(atten_file, sheet_name="Vdown")
    cal_freqs = atten_df['Frequency (GHz)'].values
    volt_cols = [c for c in atten_df.columns if c != 'Frequency (GHz)']
    cal_volts = np.array([float(c.replace('V', '')) for c in volt_cols])
    cal_atten = atten_df[volt_cols].values 
    
    # Arrays to hold our running data across iterations
    target_voltages = np.zeros(num_points)
    accumulated_req_atten = np.zeros(num_points)
    current_trace = baseline_trace.copy()

    # ==========================================================
    # Iterative Ramp 
    # ==========================================================
    #added damping factor to avoid overshoots on corrections
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
                # Pass 1: Compare target power against the 10V baseline trace
                error = target_p - actual_power
                accumulated_req_atten[i] = error
            else:
                # Pass 2+: Compare actual measured power against the target and accumulate error
                error = target_p - actual_power
                accumulated_req_atten[i] += error*damping_factor
                
            errors[i] = error
            req_atten = accumulated_req_atten[i]
            
            if req_atten >= 0:
                target_voltages[i] = 10.0
            else:
                # Interpolate calibration data for this specific frequency point
                interp_atten_at_f = np.zeros(len(cal_volts))
                for j in range(len(cal_volts)):
                    interp_atten_at_f[j] = np.interp(freq, cal_freqs, cal_atten[:, j])
                    
                sort_idx = np.argsort(interp_atten_at_f)
                sorted_atten = interp_atten_at_f[sort_idx]
                sorted_volts = cal_volts[sort_idx]
                
                if req_atten < sorted_atten[0]:
                    target_voltages[i] = 0.0  # Clamp to max attenuation
                else:
                    target_voltages[i] = np.interp(req_atten, sorted_atten, sorted_volts)

            print(f"{freq:<12.3f} | {actual_power:<15.2f} | {error:<12.2f} | {target_p:<12.2f} | {target_voltages[i]:<15.3f}")   
            
        # Check if we have hit our target tolerance early
        if iteration > 0:
            max_error_this_pass = np.max(np.abs(errors))
            print(f"\nMax Error this pass: {max_error_this_pass:.2f} dB")
            if max_error_this_pass <= tolerance:
                print(f"Tolerance of {tolerance} dB met.")
                break
                
        # Load calculated voltages into module for the next iteration
        vdi.load_memory_sequence(start_address, target_voltages)
        vdi.set_sweep_start_address(start_address)

        #load bearing dummy sweep
        #turns off display for this one because it looks very weird then turns it back on
        pna.write("DISP:UPD OFF")
        pna.query("INIT1:IMM; *OPC?")
        pna.write("DISP:UPD ON")
        
        # Trigger the PNA to read the newly applied voltages for the next iteration
        pna.query("INIT1:IMM; *OPC?") 
        pna.write(f'CALC1:PAR:SEL "{trace_name}"')
        current_trace = pna.query_ascii_values("CALC1:DATA? FDATA")
    
    print("\nRamp generation complete")
    return target_voltages


# ============================================================================
# ========= MAAAAAAIN
# ============================================================================
if __name__ == "__main__":
    
    print("=========================================")
    print("        VVA Trace Control System         ")
    print("=========================================")
    print("Select an operation mode:")
    print(" [1] Flatten a trace (Constant Power)")
    print(" [2] Generate a Power Ramp")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice not in ['1', '2']:
        print("Invalid selection. Exiting.")
        sys.exit(1)

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
        pna.write("*CLS")           # Clear output buffer
        setup_pna_aux_triggers(pna)  #initializes aux triggers need to test 
        pna.timeout = 60000         # 60 second timeout for iterative sweeps
        
        # PNA trigger source is Internal/Immediate 
        pna.write("TRIG:SOUR IMM")
        pna.write("INIT1:CONT OFF") # Put PNA into Hold mode
        
        # ==========================================
        # 1 - FLATTEN TRACE
        # ==========================================
        if choice == '1':
            print("\n--- Trace Flattening Setup ---")
            goal_val = float(input("Enter goal power level in dBm [Default 0.0]: ") or 0.0)
            f_start = float(input("Enter Start Frequency (GHz) [Default 110]: ") or 110)
            f_stop = float(input("Enter Stop Frequency (GHz) [Default 170]: ") or 170)
            num_points = int(input("Enter number of trace points [Default 101]: ") or 101)
            start_addr = int(input("Enter starting memory address [Default 0]: ") or 0)
            iterations = int(input("Enter max iterations [Default 4]: ") or 4)
            tolerance = float(input("Enter tolerance [Default 0.15]: ") or 0.15)
            
            pna.write("SENS1:SWE:TYPE LIN")
            
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
        #  2 - POWER RAMP
        # ==========================================
        elif choice == '2':
            print("\n--- Power Ramp Setup ---")
            sweep_type = input("Enter sweep type ('LIN' or 'CW') [Default LIN]: ").strip().upper() or 'LIN'
            start_pwr = float(input("Enter Ramp Start Power (dBm) [Default -10.0]: ") or -10.0)
            stop_pwr = float(input("Enter Ramp Stop Power (dBm) [Default -1.0]: ") or -1.0)
            
            if sweep_type == 'CW':
                f_start = float(input("Enter CW Frequency (GHz) [Default 110.0]: ") or 110.0)
                f_stop = None # Ignored in CW mode
            else:
                f_start = float(input("Enter Start Frequency (GHz) [Default 110.0]: ") or 110.0)
                f_stop = float(input("Enter Stop Frequency (GHz) [Default 170.0]: ") or 170.0)
                
            num_points = int(input("Enter number of trace points [Default 101]: ") or 101)
            start_addr = int(input("Enter starting memory address [Default 0]: ") or 0)
            iterations = int(input("Enter max iterations [Default 4]: ") or 4)
            tolerance = float(input("Enter tolerance [Default 0.15]: ") or 0.15)
            
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
    # Cleanup crew
    # ==========================================
    except pyvisa.errors.VisaIOError as e:
        print(f"\nInstrument communication error: {e}")
    except FileNotFoundError:
        print("\nError: 'VVA_Attenuation_Data.xlsx' not found. Please ensure your calibration file is in the same directory.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        if pna:
            print("Restoring PNA to continuous sweep and closing connection...")
            pna.write("INIT1:CONT ON")
            pna.close()



