import sys
import numpy as np
import pandas as pd
import pyvisa
from vdi_controller import VDIModuleController

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


def flat_output(pna, vdi, goal_value, num_points, f_start_ghz, f_stop_ghz, start_address=0, atten_file="VVA_Attenuation_Data.xlsx"):
    """
    Reads the baseline reference trace, calculates the required voltages to flatten 
    the output to the goal_value, and loads those voltages into memory.

    Parameters:
    -----------
    pna : pyvisa.resources.MessageBasedResource
        The connected PyVISA instance for the Keysight PNA.
    vdi : VDIModuleController
        The connected instance of the VDI USB Module wrapper.
    goal_value : float
        The target power level (in dBm) you want the flattened trace to sit at.
    num_points : int
        The exact number of points configured for the PNA sweep.
    f_start_ghz : float
        The start frequency of the sweep in GHz.
    f_stop_ghz : float
        The stop frequency of the sweep in GHz.
    start_address : int
        The memory address where the voltage sequence should begin.
    atten_file : str
        The filepath to the normalized attenuation Excel file.

    Returns:
    --------
    target_voltages : numpy.ndarray
        The array of voltages calculated and loaded into the module.
    """
    print(f"\n--- Flattening Trace to {goal_value} dB at Memory Address {start_address} ---")

    # ==========================================================
    # Configure the PNA for the Sweep Parameters - need to test this
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
    
    # --- force trace setup ---
    trace_name = "R1_Trace"
    
    # Define measurement (R1 receiver, Port 1 source)
    pna.write(f'CALC1:PAR:DEF:EXT "{trace_name}", "R1,1"')
    
    # Turn on Window 1 and feed the trace to the screen
    pna.write("DISP:WIND1:STATE ON")
    pna.write(f'DISP:WIND1:TRAC2:FEED "{trace_name}"')
    
    # Force ASCII data format and OPC should avoid -420 SCPI error with CLS in main call maybe?
    pna.write("FORM:DATA ASC,0")
    
    pna.query("INIT1:IMM; *OPC?") 
    
    # finally read the baseline trace from the PNA
    pna.write(f'CALC1:PAR:SEL "{trace_name}"')
    baseline_trace = pna.query_ascii_values("CALC1:DATA? FDATA")

    
    
    # ==========================================================
    # Load the Calibration Data
    # ==========================================================
    print(f"Loading calibration data from {atten_file}...")
    atten_df = pd.read_excel(atten_file, sheet_name="Vdown")
    
    cal_freqs = atten_df['Frequency (GHz)'].values
    
    # Extract just the voltage column headers
    volt_cols = [c for c in atten_df.columns if c != 'Frequency (GHz)']
    cal_volts = np.array([float(c.replace('V', '')) for c in volt_cols])
    cal_atten = atten_df[volt_cols].values 
    
    # Calculate frequencies for the PNA's sweep points
    sweep_freqs = np.linspace(f_start_ghz, f_stop_ghz, num_points)
    target_voltages = np.zeros(num_points)
    
    # ==========================================================
    #  Calculate Flattening Voltages
    # ==========================================================
    print("Calculating optimal voltages...")

    # ==================
    # troubleshoot print
    # ==================
    print(f"{'Freq (GHz)':<12} | {'Baseline (dBm)':<16} | {'Req Atten (dB)':<16} | {'Target Volt (V)':<15}")
    print("-" * 65)
    

    for i, freq in enumerate(sweep_freqs):
        current_power = baseline_trace[i]
        
        # att is neg
        req_atten = goal_value - current_power 
        
        # If the trace is already below the goal, can't add gain so do nothing
        if req_atten >= 0:
            target_voltages[i] = 10.0
            continue
            
        # build Attenuation vs. Voltage curve for this specific frequency
        # interpolate across the frequency axis of the calibration table
        interp_atten_at_f = np.zeros(len(cal_volts))
        for j in range(len(cal_volts)):
            interp_atten_at_f[j] = np.interp(freq, cal_freqs, cal_atten[:, j])
            
        # np.interp requires the X-axis (attn in this case) to be continually increasing
        # sort to ensure they are strictly increasing. is this messing up?
        sort_idx = np.argsort(interp_atten_at_f)
        sorted_atten = interp_atten_at_f[sort_idx]
        sorted_volts = cal_volts[sort_idx]
        
        # Check if the requested attenuation is beyond what the VVA can attenuate
        if req_atten < sorted_atten[0]:
            target_voltages[i] = 0.0  # clamp to max attenuation
        else:
            # Interpolate to find the exact voltage for the requested attenuation
            target_voltages[i] = np.interp(req_atten, sorted_atten, sorted_volts)

        #print stuff for troubleshoot
    # ==================
    # troubleshoot print
    # ==================
        print(f"{freq:<12.3f} | {current_power:<16.2f} | {req_atten:<16.2f} | {target_voltages[i]:<15.3f}")
            
    # ==========================================================
    # Load calculated voltages into module
    # ==========================================================
    print("Loading calculated flattening sequence into memory...")
    vdi.load_memory_sequence(start_address, target_voltages)
    
    # Resetting the start address primes the sweep triggers
    vdi.set_sweep_start_address(start_address)
    
    # Not sure if necessary, seems to smooth out trace
    # Triggers an extra sweep to update the screen
    pna.write("INIT1:IMM")
    pna.query("*OPC?") 
    
    print("Flattening complete")
    return target_voltages

# ============================================================================
# RAMP FUNCTIONS
# ============================================================================

def ramp_output(pna, vdi, start_power, stop_power, num_points, f_start_ghz, f_stop_ghz=None, sweep_type='LIN', start_address=0, atten_file="VVA_Attenuation_Data.xlsx"):
    """
    Reads the baseline reference trace, calculates the required voltages to create a 
    power ramp, and loads those voltages into the USB memory. Supports both Linear 
    frequency sweeps and CW power sweeps.

    Parameters:
    -----------
    pna : pyvisa.resources.MessageBasedResource
    vdi : VDIModuleController
    start_power : float
        The starting power level in dBm.
    stop_power : float
        The ending power level in dBm.
    num_points : int
        The exact number of points configured for the PNA sweep.
    f_start_ghz : float
        The start frequency for LIN mode, or the fixed frequency for CW mode.
    f_stop_ghz : float, optional
        The stop frequency for LIN mode. Ignored if sweep_type is 'CW'.
    sweep_type : str
        'LIN' for a linear frequency sweep, or 'CW' for a fixed-frequency power sweep.
    start_address : int
        The memory address where the voltage sequence should begin.
    atten_file : str
        The filepath to the normalized attenuation Excel file.
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
    
    # force trace setup to match name
    trace_name = "R1_Trace"
    
    pna.write(f'CALC1:PAR:DEF:EXT "{trace_name}", "R1,1"')
    pna.write("DISP:WIND1:STATE ON")
    pna.write(f'DISP:WIND1:TRAC2:FEED "{trace_name}"')
    pna.write("FORM:DATA ASC,0")
    # -----------------------
    
    # Chain the trigger and the *OPC? query to prevent -420 errors
    pna.query("INIT1:IMM; *OPC?") 
    
    pna.write(f'CALC1:PAR:SEL "{trace_name}"')
    baseline_trace = pna.query_ascii_values("CALC1:DATA? FDATA")
    
    
    # ==========================================================
    # Generate the Target Power Array
    # ==========================================================
    target_power = np.linspace(start_power, stop_power, num_points)
    
    # ==========================================================
    # Load Calibration Data & Calculate Voltages
    # ==========================================================
    print(f"Loading calibration data from {atten_file}...")
    atten_df = pd.read_excel(atten_file, sheet_name="Vdown")
    
    cal_freqs = atten_df['Frequency (GHz)'].values
    volt_cols = [c for c in atten_df.columns if c != 'Frequency (GHz)']
    cal_volts = np.array([float(c.replace('V', '')) for c in volt_cols])
    cal_atten = atten_df[volt_cols].values 
    
    target_voltages = np.zeros(num_points)

    #######prints for troubleshoots
    print("\nCalculating optimal voltages for the ramp...")
    print(f"{'Freq (GHz)':<12} | {'Baseline (dBm)':<16} | {'Target Pwr (dBm)':<18} | {'Target Volt (V)':<15}")
    print("-" * 67)
    #############################

    for i, freq in enumerate(sweep_freqs):
        current_power = baseline_trace[i]
        
        # Required attenuation is negative
        req_atten = target_power[i] - current_power 
        
        if req_atten >= 0:
            target_voltages[i] = 10.0
            continue
            
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

        print(f"{freq:<12.3f} | {current_power:<16.2f} | {target_power[i]:<18.2f} | {target_voltages[i]:<15.3f}")   
    # ==========================================================
    # Load calculated voltages into module
    # ==========================================================
    print(f"Loading ramp sequence into memory at address {start_address}...")
    vdi.load_memory_sequence(start_address, target_voltages)
    
    vdi.set_sweep_start_address(start_address)
    
    # Trigger one more sweep
    #seems necessary, not sure why, smooths out trace
    pna.write("INIT1:IMM")
    pna.query("*OPC?") 
    
    print("Ramp generation complete")
    return target_voltages

# ============================================================================
# =========MAAAAAAAAAIN
# ============================================================================
if __name__ == "__main__":
 
 # ============================================================================
 # rAMP Test - uncomment entire block if you want to test ramp functions
 # ============================================================================

    # print("=== VVA Trace Ramp Test ===")
    
    # # Prompt for Sweep Mode
    # sweep_type = input("Enter sweep type ('LIN' or 'CW') [Default LIN]: ").strip().upper() or 'LIN'
    
    # # Prompt for Ramp Power Parameters
    # start_pwr = float(input("Enter Ramp Start Power (dBm) [Default -10.0]: ") or -10.0)
    # stop_pwr = float(input("Enter Ramp Stop Power (dBm) [Default -1]: ") or -1)
    
    # # Prompt for Frequencies based on Sweep Mode
    # if sweep_type == 'CW':
    #     f_start = float(input("Enter CW Frequency (GHz) [Default 110.0]: ") or 110.0)
    #     f_stop = None # Ignored in CW mode
    # else:
    #     f_start = float(input("Enter Start Frequency (GHz) [Default 110.0]: ") or 110.0)
    #     f_stop = float(input("Enter Stop Frequency (GHz) [Default 170.0]: ") or 170.0)
        
    # num_points = int(input("Enter number of trace points [Default 101]: ") or 101)
    # start_addr = int(input("Enter starting memory address [Default 0]: ") or 0)
    
    # # Initialize the usb Module
    # print("\nConnecting to VDI Module...")
    # vdi = VDIModuleController()
    # vdi.connect()
    
    # if not vdi.is_connected:
    #     print("Failed to connect to the VDI module. Exiting test.")
    #     sys.exit(1)
        
    # # Initialize PyVISA and connect to the PNA
    # rm = pyvisa.ResourceManager()
    # pna_address = 'GPIB0::16::INSTR'
    # pna = None
    
    # try:
    #     print(f"Connecting to PNA at {pna_address}...")
    #     pna = rm.open_resource(pna_address)
    # #   ##clear output buffer trying to avoid SCPI -420 error?
    #     pna.write("*CLS")
    ##    setup_pna_aux_triggers(pna)  #initializes aux triggers need to test 
    #     pna.timeout = 60000 
        
    #     # Turn OFF continuous sweeping, enable immediate triggering
    #     pna.write("TRIG:SOUR IMM")
    #     pna.write("INIT1:CONT OFF")
        
    #     # Run the ramp routine
    #     calculated_voltages = ramp_output(
    #         pna=pna,
    #         vdi=vdi,
    #         start_power=start_pwr,
    #         stop_power=stop_pwr,
    #         num_points=num_points,
    #         f_start_ghz=f_start,
    #         f_stop_ghz=f_stop,
    #         sweep_type=sweep_type,
    #         start_address=start_addr,
    #         atten_file="VVA_Attenuation_Data.xlsx" 
    #     )
        
    #     print(f"\nSuccess! Successfully loaded {len(calculated_voltages)} points into memory starting at address {start_addr}.")
        
    # except pyvisa.errors.VisaIOError as e:
    #     print(f"\nInstrument communication error: {e}")
    # except FileNotFoundError:
    #     print("\nError: 'VVA_Attenuation_Data.xlsx' not found. Please ensure your calibration file is in the same directory.")
    # except Exception as e:
    #     print(f"\nAn unexpected error occurred: {e}")
    # finally:
    #     if pna:
    #         print("Restoring PNA to continuous sweep and closing connection...")
    #         pna.write("INIT1:CONT ON")
    #         pna.close()



    # ============================================================================
    # Flattening Test - just uncomment the entire block if you want to test flat traces function
    # ============================================================================
    
    print("=== VVA Trace Flattening Test ===")
    
    # Prompt for test parameters
    goal_val = float(input("Enter goal power level in dBm [Default 0.0]: ") or 0.0)
    f_start = float(input("Enter Start Frequency (GHz) [Default 110.0]: ") or 110.0)
    f_stop = float(input("Enter Stop Frequency (GHz) [Default 170.0]: ") or 170.0)
    num_points = int(input("Enter number of trace points [Default 101]: ") or 101)
    start_addr = int(input("Enter starting memory address [Default 0]: ") or 0)
    
    # Initialize the VDI Module
    print("\nConnecting to VDI Module...")
    vdi = VDIModuleController()
    vdi.connect()
    
    if not vdi.is_connected:
        print("Failed to connect to VDI module. Exiting test.")
        sys.exit(1)
        
    # Initialize PyVISA and connect to the PNA
    rm = pyvisa.ResourceManager()
    pna_address = 'GPIB0::16::INSTR'
    pna = None

    try:
        print(f"Connecting to PNA at {pna_address}...")
        pna = rm.open_resource(pna_address)
        #clear output buffer
        pna.write("*CLS")

        ##setup_pna_aux_triggers(pna)  #initializes aux triggers need to test 
        # INCREASED TIMEOUT TO 60 SECONDS
        pna.timeout = 60000  
        
        # Ensure the PNA is set to a Linear Frequency Sweep
        pna.write("SENS1:SWE:TYPE LIN")
        
        # PNA trigger source is Internal/Immediate 
        # (So it doesn't wait for a hardware trigger to start)
        pna.write("TRIG:SOUR IMM")
        
        # (put into Hold)
        pna.write("INIT1:CONT OFF")
        
        # Run flattening routine
        calculated_voltages = flat_output(
            pna=pna,
            vdi=vdi,
            goal_value=goal_val,
            num_points=num_points,
            f_start_ghz=f_start,
            f_stop_ghz=f_stop,
            start_address=start_addr,
            atten_file="VVA_Attenuation_Data.xlsx" 
        )
    
        print(f"\n loaded {len(calculated_voltages)} points into memory starting at address {start_addr}.")
        
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