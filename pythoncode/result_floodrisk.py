import pandas as pd
import numpy as np

# Đọc dữ liệu
df = pd.read_csv('data/hypothekendaten4.csv', delimiter=';')

# In ra tên các cột trong dữ liệu
print("Các cột trong dữ liệu:")
print(df.columns)

# Hàm chuyển đổi linh hoạt
def flexible_numeric_conversion(series):
    if pd.api.types.is_numeric_dtype(series):
        return series
    else:
        return pd.to_numeric(series.str.replace(',', '.'), errors='coerce')

# Chuyển đổi các cột sang dạng số
numeric_columns = ['aktuelles_LtV', 'darlehenbetrag', 'aktueller_immobilienwert', 'Schadensfaktor', 'AEP', 'Risikogewicht']
for col in numeric_columns:
    if col in df.columns:
        df[col] = flexible_numeric_conversion(df[col])

# In thông tin về các cột số sau khi chuyển đổi
for col in numeric_columns:
    if col in df.columns:
        print(f"\nThông tin về cột '{col}':")
        print(df[col].describe())

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
def calculate_values(row, T=20):
    E_j = row['aktueller_immobilienwert']
    schadenfaktor = row['Schadensfaktor']
    p_I_ij = row['AEP'] if 'AEP' in row.index else 0.01
    
    # Tính Immobilienschaden (Công thức 1)
    immobilienschaden = E_j * schadenfaktor
    
    # Tính EAI (Công thức 2)
    EAI = immobilienschaden * p_I_ij
    
    # Tính EI (Công thức 3)
    EI = EAI * T
    
    # Tính giá trị mới của bất động sản (Công thức 4)
    new_immobilienwert = E_j - immobilienschaden
    
    # Tính LtV mới (Công thức 5)
    new_LtV = row['darlehenbetrag'] / new_immobilienwert if new_immobilienwert > 0 else np.inf
    
    # Xác định neue Risikogewicht dựa trên LtV mới
    neue_risikogewicht = get_neue_risikogewicht(new_LtV)
    
    # Tính RWA mới dựa trên neue Risikogewicht
    new_RWA = row['darlehenbetrag'] * neue_risikogewicht
    
    # Tính % thay đổi RWA (Công thức 7)
    old_RWA = row['darlehenbetrag'] * row['Risikogewicht']
    RWA_change = (new_RWA / old_RWA) - 1 if old_RWA > 0 else np.inf
    
    return pd.Series({
        'Immobilienschaden': immobilienschaden,
        'EAI': EAI,
        'EI': EI,
        'Neuer Immobilienwert': new_immobilienwert,
        'Neue LtV': new_LtV,
        'Neue Risikogewicht': neue_risikogewicht,
        'Neue RWA': new_RWA,
        'RWA Änderung': RWA_change
    })

# Áp dụng tính toán cho mỗi hàng
results = df.apply(calculate_values, axis=1)

# Kết hợp kết quả với DataFrame gốc
df_results = pd.concat([df, results], axis=1)

# In thông tin thống kê về kết quả tính toán
print("\nThông tin về kết quả tính toán:")
for col in ['Immobilienschaden', 'EAI', 'EI', 'Neuer Immobilienwert', 'Neue LtV', 'Neue Risikogewicht', 'Neue RWA', 'RWA Änderung']:
    print(f"\nThông tin về cột '{col}':")
    print(df_results[col].describe())


df_results.to_csv('immobilien_analyse_ergebnisse.csv', index=False, decimal=',')
print("\nĐã lưu kết quả vào file 'immobilien_analyse_ergebnisse.csv'")