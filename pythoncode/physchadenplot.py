import pandas as pd
import numpy as np
from tabulate import tabulate

# Đọc dữ liệu từ file CSV
df = pd.read_csv('data/hypothekendaten_final_with_id.csv', delimiter=';')

def flexible_numeric_conversion(value, decimals=2):
    if isinstance(value, str):
        try:
            return round(float(value.replace(',', '.')), decimals)
        except ValueError:
            return np.nan
    elif isinstance(value, (int, float)):
        return round(value, decimals)
    else:
        return np.nan

# Convert columns to numeric
numeric_columns = ['aktuelles_LtV', 'darlehenbetrag', 'aktueller_immobilienwert', 'Schadensfaktor', 'AEP', 'Risikogewicht', 'Ueberschwemmungstiefe', 'Quadratmeterpreise', 'wohnflaeche']
for col in numeric_columns:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: flexible_numeric_conversion(x))

# Remove rows with NaN values
df = df.dropna(subset=[col for col in numeric_columns if col in df.columns])

# Function to determine Risikogewicht based on LtV
def get_risikogewicht(ltv):
    if ltv <= 0.50:
        return 0.20
    elif 0.50 < ltv <= 0.60:
        return 0.25
    elif 0.60 < ltv <= 0.80:
        return 0.30
    elif 0.80 < ltv <= 0.90:
        return 0.40
    elif 0.90 < ltv <= 1.00:
        return 0.50
    else:
        return 0.70

# Recalculate Risikogewicht based on aktuelles_LtV
df['Risikogewicht'] = df['aktuelles_LtV'].apply(get_risikogewicht)

# Function to calculate values
def calculate_values(row):
    E_j = row['aktueller_immobilienwert']
    schadenfaktor = row['Schadensfaktor']
    p_I_ij = row['AEP'] if 'AEP' in row.index else 0.01
    
    immobilienschaden = E_j * schadenfaktor
    EAI = immobilienschaden * p_I_ij
    new_immobilienwert = E_j - immobilienschaden
    
    # Tính toán mới LtV dựa trên tài sản thế chấp mới
    new_LtV = row['darlehenbetrag'] / new_immobilienwert if new_immobilienwert > 0 else np.inf
    
    # Sử dụng Risikogewicht đã được tính lại
    risikogewicht = row['Risikogewicht']
    neue_risikogewicht = get_risikogewicht(new_LtV)
    
    # Tính toán RWA
    akt_RWA = row['darlehenbetrag'] * risikogewicht
    new_RWA = row['darlehenbetrag'] * neue_risikogewicht
    RWA_change = (new_RWA / akt_RWA) - 1 if akt_RWA > 0 else np.inf
    
    return pd.Series({
        'Immobilienschaden': immobilienschaden, 
        'EAI': EAI, 
        'Neuer Immobilienwert': new_immobilienwert, 
        'Neue LtV': new_LtV, 
        'Risikogewicht': risikogewicht,
        'Neue Risikogewicht': neue_risikogewicht,  
        'Akt. RWA': akt_RWA,
        'Neue RWA': new_RWA, 
        'RWA Änderung': RWA_change
    })

# Apply calculations to each row
results = df.apply(calculate_values, axis=1)

# Combine results with original DataFrame
df_results = pd.concat([df, results], axis=1)

# Filter data to keep only rows with non-zero Schadensfaktor
df_damage = df_results[df_results['Schadensfaktor'] != 0].copy()

# Calculate sums for Akt. RWA and Neue RWA
akt_rwa_sum = df_damage['Akt. RWA'].sum()
neue_rwa_sum = df_damage['Neue RWA'].sum()

# Select the relevant columns and sort by absolute RWA Änderung
table_data = df_damage[['ID', 'aktuelles_LtV', 'Neue LtV', 'Risikogewicht', 'Neue Risikogewicht', 'Akt. RWA', 'Neue RWA', 'RWA Änderung']].copy()
table_data['Abs RWA Änderung'] = table_data['RWA Änderung'].abs()
table_data = table_data.sort_values('Abs RWA Änderung', ascending=False).head(13)

# Format the data for better readability
table_data['aktuelles_LtV'] = table_data['aktuelles_LtV'].map(lambda x: f"{x:.2f}")
table_data['Neue LtV'] = table_data['Neue LtV'].map(lambda x: f"{x:.2f}")
table_data['Risikogewicht'] = table_data['Risikogewicht'].map(lambda x: f"{x:.2f}")
table_data['Neue Risikogewicht'] = table_data['Neue Risikogewicht'].map(lambda x: f"{x:.2f}")
table_data['Akt. RWA'] = table_data['Akt. RWA'].map(lambda x: f"{x:,.2f}")
table_data['Neue RWA'] = table_data['Neue RWA'].map(lambda x: f"{x:,.2f}")
table_data['RWA Änderung'] = table_data['RWA Änderung'].map(lambda x: f"{x:.2f}")

# Remove the temporary column used for sorting
table_data = table_data.drop('Abs RWA Änderung', axis=1)

# Kiểm tra và loại bỏ các cột bị trùng lặp
table_data = table_data.loc[:, ~table_data.columns.duplicated()]

# Tạo hàng tổng kết với đúng số lượng cột
sum_row = pd.DataFrame([['Sum', '', '', '', '', f"{akt_rwa_sum:,.2f}", f"{neue_rwa_sum:,.2f}", '']], 
                       columns=table_data.columns)

# Kết hợp hàng tổng kết với bảng
table_data = pd.concat([table_data, sum_row], ignore_index=True)

# Tạo bảng kết quả và in ra
table = tabulate(table_data, headers='keys', tablefmt='pipe', showindex=False)
print("\nTop 13 rows of relevant columns with RWA sums:")
print(table)

# Save the new dataset to a CSV file
df_results.to_csv('new_hypothekendaten_final_with_risikogewicht.csv', sep=';', index=False)