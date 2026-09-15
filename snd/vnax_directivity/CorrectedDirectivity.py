import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def process_corrected_directivity(file_path, bin_size=5.0, step_size=2.5):
    """
    Processes file to calculate corrected directivity if the 'J10 Short' or 'xj10' sheet exists.
    
    Parameters:
    file_path (str): The path to the Excel file.
    bin_size (float): The window size for the calculation (defaultS to 5 GHz).
    step_size (float): The sliding step size (defaults to 2.5 GHz).
    
    Returns:
    tuple: (df_j10, df_corr_dir) 
           df_j10 is J10 short data 
           df_corr_dir is the dataframe with Frequency and Corrected Directivity.
           Returns (None, None) if the sheet is not found.
    """
    #J10 short is default sheet name, xj10 is deprecated sheet name for the same data
    possible_sheets = ["J10 Short", "j10+short","xj10"]
    
    try:
        xl = pd.ExcelFile(file_path)
        
        # Find the first sheet name from list that actually exists in the file
        #next will forever be confusing
        target_sheet = next((sheet for sheet in possible_sheets if sheet in xl.sheet_names), None)
        
        if target_sheet is None:
            print(f"None of the sheets {possible_sheets} were found in {file_path}.")
            return None, None
            
        # Load into df
        print(f"Loading data from sheet: '{target_sheet}'")
        df = pd.read_excel(file_path, sheet_name=target_sheet)
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None, None

    # Rename the first column to 'Freq' if it comes in unnamed
    #avoids pd index save stuff
    if 'Unnamed: 0' in df.columns:
        df.rename(columns={'Unnamed: 0': 'Freq'}, inplace=True)
    else:
        df.rename(columns={df.columns[0]: 'Freq'}, inplace=True)
        
    # check if 'S11(dB)' exists. If not, calculate it from real and imaginary columns
    if 'S11(dB)' not in df.columns:
        real_col = next((col for col in df.columns if 'real' in col.lower()), None)
        imag_col = next((col for col in df.columns if 'imag' in col.lower()), None)
        
        if real_col and imag_col:
            # Calculate dB magnitude: 20 * log10(sqrt(real^2 + imag^2))
            df['S11(dB)'] = 20 * np.log10(np.sqrt(df[real_col]**2 + df[imag_col]**2))
        else:
            print("Could not find 'S11(dB)' or real/imaginary columns.")
            return None, None
            
    # Create a copy of the original dataframe
    df_j10 = df.copy()

    # Convert to linear magnitude
    df_j10["s11(lin)"] = np.power(10, df_j10["S11(dB)"] / 20)
    
    # Calculate Corrected Directivity sliding over frequency
    min_freq = df_j10['Freq'].min()
    max_freq = df_j10['Freq'].max()
    
    results = []
    current_start = min_freq
    
    # slides until bin exceeds max freq
    while current_start + bin_size <= max_freq:
        current_end = current_start + bin_size
        center_freq = current_start + (bin_size / 2)
        
        # Get data within the current frequency bin
        bin_data = df_j10[(df_j10['Freq'] >= current_start) & (df_j10['Freq'] <= current_end)]
        
        if not bin_data.empty:
            # Calculate pk-pk/2
            peak_to_peak = bin_data["s11(lin)"].max() - bin_data["s11(lin)"].min()
            
            # Avoid logarithm of zero if the signal is flat in bin
            if peak_to_peak > 0:
                corr_dir = 20 * np.log10(peak_to_peak / 2)
            else:
                corr_dir = -np.inf
                
            results.append({
                'Frequency': center_freq, 
                'Corrected Directivity (dB)': corr_dir
            })
            
        # Slide over by the step size
        current_start += step_size
        
    df_corr_dir = pd.DataFrame(results)
    
    #uncomment in prod, removes linear column from df and returns only original j10 short dataframe 
    #used for manual verification
    #comment if you want linear in df
    if "s11(lin)" in df_j10.columns:
        df_j10.drop(columns=["s11(lin)"], inplace=True)
    
    return df_j10, df_corr_dir


if __name__ == "__main__":
    # examplefile checking
    test_file = r"C:\Users\deaton\Downloads\vnax4036b.xlsx"
    
    df_original, df_directivity = process_corrected_directivity(
        file_path=test_file, 
        bin_size=5.0,     
        step_size=2.5     
    )
    
    if df_original is not None and df_directivity is not None:
        print("Processed J10 Short data")
        
        plt.figure(figsize=(10, 6))
        
        # Plot S11 magnitude
        plt.plot(df_original['Freq'], df_original['S11(dB)'], 
                 label='Original J10 S11 (dB)', alpha=0.5, color='blue')
        
        # Plot Corrected Directivity
        plt.plot(df_directivity['Frequency'], df_directivity['Corrected Directivity (dB)'], 
                 label='Corrected Directivity (dB)', marker='o', color='red', linestyle='--')
        
        plt.xlabel('Frequency (GHz)')
        plt.ylabel('Magnitude (dB)')
        plt.title('J10 Short Data and Corrected Directivity')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
"""
        output_filename = "Processed_Directivity_Output.xlsx"

        #write to excel, manually verifying a few points
        with pd.ExcelWriter(output_filename) as writer:
            # Write the original data to the first sheet
            df_original.to_excel(writer, sheet_name="J10 Short", index=False)
            
            # Write the calculated directivity to the second sheet
            df_directivity.to_excel(writer, sheet_name="Corrected Directivity", index=False)
            
        print(f"Data successfully saved to {output_filename}")

"""