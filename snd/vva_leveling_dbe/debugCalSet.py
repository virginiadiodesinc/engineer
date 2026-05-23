import pyvisa

rm = pyvisa.ResourceManager()
pna = rm.open_resource('GPIB0::16::INSTR')
pna.timeout = 5000  
pna.clear()         

print("\n--- Interrogating PNA (Emptying the Vault) ---")
pna.write("*CLS")   

def safe_query(command):
    try:
        pna.write(command)
        return pna.read().strip()
    except pyvisa.errors.VisaIOError:
        return f"[TIMED OUT] VNA Error: {pna.query('SYST:ERR?').strip()}"

# 1. Ask the VNA for the exact name of the active trace on the screen
active_trace = safe_query("SYST:ACT:MEAS?")
print(f"1. Active Trace Name is: {active_trace}")

# 2. Select that specific trace so SCPI knows what we are talking about
pna.write(f'CALC1:PAR:SEL {active_trace}')

# 3. NOW ask what the Correction Type is!
print(f"2. Trace Cal Type: {safe_query('CALC1:CORR:TYPE?')}")

pna.close()



# import pyvisa

# rm = pyvisa.ResourceManager()
# pna = rm.open_resource('GPIB0::16::INSTR')
# pna.timeout = 5000  # Give it 5 seconds to think
# pna.clear()         # Clear the GPIB bus of any lingering ghost commands

# print("\n--- Interrogating PNA (put your hands up) ---")
# pna.write("*CLS")   # Clear the VNA's error queue

# def safe_query(command):
#     try:
#         pna.write(command)
#         response = pna.read().strip()
#         return response
#     except pyvisa.errors.VisaIOError:
#         # If it times out, ask the VNA what we did wrong
#         err = pna.query("SYST:ERR?").strip()
#         return f"[TIMED OUT] VNA Error: {err}"

# # 1. Verify we are looking at the right Cal Set
# print(f"1. Active Cal Set Name: {safe_query('SENS1:CORR:CSET:ACT? NAME')}")

# # 2. Ask the trace what its correction family is called
# print(f"2. Trace Cal Type: {safe_query('CALC1:CORR:TYPE?')}")

# # 3. Ask the Cal Set what exact Error Terms are inside it
# print(f"3. Error Terms Catalog: {safe_query('SENS1:CORR:CSET:ETERM:CAT?')}")

# pna.close()