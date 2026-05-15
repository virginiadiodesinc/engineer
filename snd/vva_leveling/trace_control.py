import sys
import numpy as np
import pandas as pd
import pyvisa
from vdi_controller import VDIModuleController

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
    # Capture Baseline Trace
    # ==========================================================
    print("Setting VVA to 10V minimum attenuation for baseline sweep...")
    
    baseline_volts = np.full(num_points, 10.0)
    
    vdi.load_memory_sequence(start_address, baseline_volts)
    
    vdi.set_sweep_start_address(start_address)
    
    # PNA stuff
    trace_name = "R1_Trace"
    pna.write("INIT1:IMM")
    pna.query("*OPC?") 
    
    # Read the baseline trace from the PNA
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
    for i, freq in enumerate(sweep_freqs):
        current_power = baseline_trace[i]
        
        # att is neg
        req_atten = goal_value - current_power 
        
        # If the trace is already below the goal, can't add gain so do nothing
        if req_atten >= 0:
            target_voltages[i] = 10.0
            continue
            
        # build Attenuation vs. Voltage curve for this specific frequency
        # by interpolating across the frequency axis of the calibration table
        interp_atten_at_f = np.zeros(len(cal_volts))
        for j in range(len(cal_volts)):
            interp_atten_at_f[j] = np.interp(freq, cal_freqs, cal_atten[:, j])
            
        # np.interp requires the X-axis (attn) to be continually increasing.
        # sort them to ensure they are strictly increasing.
        sort_idx = np.argsort(interp_atten_at_f)
        sorted_atten = interp_atten_at_f[sort_idx]
        sorted_volts = cal_volts[sort_idx]
        
        # Check if the requested attenuation is beyond what the VVA can physically attenuate
        if req_atten < sorted_atten[0]:
            target_voltages[i] = 0.0  # clamp to max attenuation
        else:
            # Interpolate to find the exact voltage for the requested attenuation
            target_voltages[i] = np.interp(req_atten, sorted_atten, sorted_volts)
            
    # ==========================================================
    # Load calculated voltages into module
    # ==========================================================
    print("Loading calculated flattening sequence into memory...")
    vdi.load_memory_sequence(start_address, target_voltages)
    
    # Resetting the start address primes the sweep triggers once more
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
    
    pna.write("INIT1:IMM")
    pna.query("*OPC?") 
    
    pna.write('CALC1:PAR:SEL "R1_Trace"')
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
    
    print("Calculating optimal voltages for the ramp...")
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
        # f_start = float(input("Enter CW Frequency (GHz) [Default 110.0]: ") or 110.0)
        # f_stop = None # Ignored in CW mode
    # else:
        # f_start = float(input("Enter Start Frequency (GHz) [Default 110.0]: ") or 110.0)
        # f_stop = float(input("Enter Stop Frequency (GHz) [Default 170.0]: ") or 170.0)
        
    # num_points = int(input("Enter number of trace points [Default 101]: ") or 101)
    # start_addr = int(input("Enter starting memory address [Default 0]: ") or 0)
    
    # # Initialize the usb Module
    # print("\nConnecting to VDI Module...")
    # vdi = VDIModuleController()
    # vdi.connect()
    
    # if not vdi.is_connected:
        # print("Failed to connect to the VDI module. Exiting test.")
        # sys.exit(1)
        
    # # Initialize PyVISA and connect to the PNA
    # rm = pyvisa.ResourceManager()
    # pna_address = 'GPIB0::16::INSTR'
    # pna = None
    
    # try:
        # print(f"Connecting to PNA at {pna_address}...")
        # pna = rm.open_resource(pna_address)
        # pna.timeout = 60000 
        
        # # Turn OFF continuous sweeping, enable immediate triggering
        # pna.write("TRIG:SOUR IMM")
        # pna.write("INIT1:CONT OFF")
        
        # # Run the ramp routine
        # calculated_voltages = ramp_output(
            # pna=pna,
            # vdi=vdi,
            # start_power=start_pwr,
            # stop_power=stop_pwr,
            # num_points=num_points,
            # f_start_ghz=f_start,
            # f_stop_ghz=f_stop,
            # sweep_type=sweep_type,
            # start_address=start_addr,
            # atten_file="VVA_Attenuation_Data.xlsx" 
        # )
        
        # print(f"\nSuccess! Successfully loaded {len(calculated_voltages)} points into memory starting at address {start_addr}.")
        
    # except pyvisa.errors.VisaIOError as e:
        # print(f"\nInstrument communication error: {e}")
    # except FileNotFoundError:
        # print("\nError: 'VVA_Attenuation_Data.xlsx' not found. Please ensure your calibration file is in the same directory.")
    # except Exception as e:
        # print(f"\nAn unexpected error occurred: {e}")
    # finally:
        # if pna:
            # print("Restoring PNA to continuous sweep and closing connection...")
            # pna.write("INIT1:CONT ON")
            # pna.close()



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
        
        # INCREASED TIMEOUT TO 60 SECONDS
        pna.timeout = 60000  
        
        # Ensure the PNA is set to a Linear Frequency Sweep
        pna.write("SENS1:SWE:TYPE LIN")
        
        # GUARANTEE the PNA trigger source is Internal/Immediate 
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