import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Đọc dữ liệu từ file CSV
df = pd.read_csv('data/hypothekendaten4.csv', delimiter=';')

# Hàm chuyển đổi linh hoạt
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

# Chuyển đổi các cột sang dạng số
numeric_columns = ['aktuelles_LtV', 'darlehenbetrag', 'aktueller_immobilienwert', 'Schadensfaktor', 'AEP', 'Risikogewicht', 'Ueberschwemmungstiefe', 'Quadratmeterpreise', 'wohnflaeche']
for col in numeric_columns:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: flexible_numeric_conversion(x))

# Loại bỏ các hàng có giá trị NaN
df = df.dropna(subset=[col for col in numeric_columns if col in df.columns])

# Hàm xác định giá trị neue Risikogewicht dựa trên Neue LtV
def get_neue_risikogewicht(ltv):
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

# Hàm tính toán các giá trị
def calculate_values(row):
    E_j = row['aktueller_immobilienwert']
    schadenfaktor = row['Schadensfaktor']
    p_I_ij = row['AEP'] if 'AEP' in row.index else 0.01
    
    # Tính Immobilienschaden (Công thức 1)
    immobilienschaden = E_j * schadenfaktor
    
    # Tính EAI (Công thức 2)
    EAI = immobilienschaden * p_I_ij
    
    # Tính giá trị mới của bất động sản (Công thức 3)
    new_immobilienwert = E_j - immobilienschaden
    
    # Tính LtV mới (Công thức 4)
    new_LtV = row['darlehenbetrag'] / new_immobilienwert if new_immobilienwert > 0 else np.inf
    
    # Xác định neue Risikogewicht dựa trên LtV mới
    neue_risikogewicht = get_neue_risikogewicht(new_LtV)
    
    # Tính Akt. RWA
    akt_RWA = row['darlehenbetrag'] * row['Risikogewicht']
    
    # Tính RWA mới dựa trên neue Risikogewicht
    new_RWA = row['darlehenbetrag'] * neue_risikogewicht
    
    # Tính % thay đổi RWA (Công thức 6)
    RWA_change = (new_RWA / akt_RWA) - 1 if akt_RWA > 0 else np.inf
    
    return pd.Series({
        'Immobilienschaden': immobilienschaden, 
        'EAI': EAI, 
        'Neuer Immobilienwert': new_immobilienwert, 
        'Neue LtV': new_LtV, 
        'Neue Risikogewicht': neue_risikogewicht, 
        'Akt. RWA': akt_RWA,
        'Neue RWA': new_RWA, 
        'RWA Änderung': RWA_change
    })

# Áp dụng tính toán cho mỗi hàng
results = df.apply(calculate_values, axis=1)

# Kết hợp kết quả với DataFrame gốc
df_results = pd.concat([df, results], axis=1)

# Lọc dữ liệu chỉ giữ lại các hàng có Schadensfaktor khác 0
df_damage = df_results[df_results['Schadensfaktor'] != 0].copy()

# Function to calculate statistics
def calculate_stats(column):
    return {
        'mean': df_damage[column].mean(),
        'median': df_damage[column].median(),
        'min': df_damage[column].min(),
        'max': df_damage[column].max(),
        'std': df_damage[column].std()
    }

# Calculate statistics for relevant columns
columns_to_analyze = ['aktuelles_LtV', 'Neue LtV', 'aktueller_immobilienwert', 'Neuer Immobilienwert', 'Akt. RWA', 'Neue RWA', 'RWA Änderung']

stats = {col: calculate_stats(col) for col in columns_to_analyze}

# Print results
for col, col_stats in stats.items():
    print(f"\nStatistics for {col}:")
    for stat, value in col_stats.items():
        print(f"{stat}: {value:.4f}")

# Calculate percentage of cases where new values increased
ltv_increased = (df_damage['Neue LtV'] > df_damage['aktuelles_LtV']).mean() * 100
immobilienwert_decreased = (df_damage['Neuer Immobilienwert'] < df_damage['aktueller_immobilienwert']).mean() * 100
rwa_increased = (df_damage['RWA Änderung'] > 0).mean() * 100

print(f"\nPercentage of cases where LtV increased: {ltv_increased:.2f}%")
print(f"Percentage of cases where Immobilienwert decreased: {immobilienwert_decreased:.2f}%")
print(f"Percentage of cases where RWA increased: {rwa_increased:.2f}%")

