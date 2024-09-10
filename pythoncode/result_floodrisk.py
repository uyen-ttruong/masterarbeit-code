import pandas as pd
import numpy as np

# Đọc dữ liệu
df = pd.read_csv('data/hypothekendaten2.csv', delimiter=';')

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
numeric_columns = ['aktuelles_LtV', 'darlehenbetrag', 'aktueller_immobilienwert', 'Schadensfaktor', 'AEP']
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

# Hàm tính toán các giá trị
def calculate_values(row, T=30):
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
    
    # Tính RWA (Công thức 6)
    risk_weight = 0.5 if new_LtV < 0.8 else 1.0
    new_RWA = row['darlehenbetrag'] * risk_weight
    
    # Tính % thay đổi RWA (Công thức 7)
    old_risk_weight = 0.5 if row['aktuelles_LtV'] < 0.8 else 1.0
    old_RWA = row['darlehenbetrag'] * old_risk_weight
    RWA_change = (new_RWA / old_RWA) - 1 if old_RWA > 0 else np.inf
    
    return pd.Series({
        'Immobilienschaden': immobilienschaden,
        'EAI': EAI,
        'EI': EI,
        'Neuer Immobilienwert': new_immobilienwert,
        'Neue LtV': new_LtV,
        'Neue RWA': new_RWA,
        'RWA Änderung': RWA_change
    })

# Áp dụng tính toán cho mỗi hàng
results = df.apply(calculate_values, axis=1)

# Kết hợp kết quả với DataFrame gốc
df_results = pd.concat([df, results], axis=1)

# In thông tin thống kê về kết quả tính toán
print("\nThông tin về kết quả tính toán:")
for col in ['Immobilienschaden', 'EAI', 'EI', 'Neuer Immobilienwert', 'Neue LtV', 'Neue RWA', 'RWA Änderung']:
    print(f"\nThông tin về cột '{col}':")
    print(df_results[col].describe())

# # In một số hàng đầu tiên của kết quả để kiểm tra
# print("\nNăm hàng đầu tiên của kết quả:")
# print(df_results.head())
df_results.to_csv('immobilien_analyse_ergebnisse.csv', index=False, decimal=',')
print("\nĐã lưu kết quả vào file 'immobilien_analyse_ergebnisse.csv'")