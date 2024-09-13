import pandas as pd
import numpy as np

# Đọc dữ liệu
df = pd.read_csv('data\hypothekendaten_final_with_statistics.csv', delimiter=';')

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

# Lọc các hàng có 'Schadensfaktor' > 0 và loại bỏ NaN
df = df[df['Schadensfaktor'] > 0].dropna(subset=numeric_columns)

# Hàm tính toán các giá trị mới với debug chi tiết
def calculate_values_detailed(row):
    aktueller_immobilienwert = row['aktueller_immobilienwert']
    schadenfaktor = row['Schadensfaktor']
    darlehenbetrag = row['darlehenbetrag']
    
    immobilienschaden = aktueller_immobilienwert * schadenfaktor
    new_immobilienwert = aktueller_immobilienwert - immobilienschaden
    new_LtV = darlehenbetrag / new_immobilienwert if new_immobilienwert > 0 else float('inf')
    
    # Tính toán LTV cũ theo công thức đơn giản
    calculated_old_LtV = darlehenbetrag / aktueller_immobilienwert
    
    return pd.Series({
        'Neuer Immobilienwert': new_immobilienwert,
        'Neue LtV': new_LtV,
        'Berechnetes altes LtV': calculated_old_LtV
    })

# Áp dụng tính toán và kết hợp kết quả
df_results = pd.concat([df, df.apply(calculate_values_detailed, axis=1)], axis=1)

# Kiểm tra số lượng trường hợp LTV mới cao hơn LTV cũ
ltv_increased = (df_results['Neue LtV'] > df_results['aktuelles_LtV']).sum()
print(f"\nSố trường hợp LTV mới cao hơn LTV cũ: {ltv_increased} / {len(df_results)}")

# In ra chi tiết các trường hợp LTV mới cao hơn LTV cũ
print("\nChi tiết các trường hợp LTV mới cao hơn LTV cũ:")
unusual_cases = df_results[df_results['Neue LtV'] > df_results['aktuelles_LtV']]
for _, row in unusual_cases.iterrows():
    print(f"Immobilie ID: {row.name}")
    print(f"  Aktueller Immobilienwert: {row['aktueller_immobilienwert']:.2f}")
    print(f"  Neuer Immobilienwert: {row['Neuer Immobilienwert']:.2f}")
    print(f"  Darlehenbetrag: {row['darlehenbetrag']:.2f}")
    print(f"  Schadensfaktor: {row['Schadensfaktor']:.4f}")
    print(f"  Altes LtV (aus Daten): {row['aktuelles_LtV']:.4f}")
    print(f"  Berechnetes altes LtV: {row['Berechnetes altes LtV']:.4f}")
    print(f"  Neues LtV: {row['Neue LtV']:.4f}")
    print("--------------------")

# Kiểm tra sự khác biệt giữa LTV cũ trong dữ liệu và LTV cũ được tính toán
df_results['LtV Differenz'] = df_results['aktuelles_LtV'] - df_results['Berechnetes altes LtV']
print("\nStatistik der LtV-Differenz (Daten vs. Berechnet):")
print(df_results['LtV Differenz'].describe())

# Kiểm tra các trường hợp có sự khác biệt đáng kể
significant_diff = df_results[abs(df_results['LtV Differenz']) > 0.01]
print(f"\nAnzahl der Fälle mit signifikanter LtV-Differenz: {len(significant_diff)} / {len(df_results)}")

if len(significant_diff) > 0:
    print("\nBeispiele für Fälle mit signifikanter LtV-Differenz:")
    print(significant_diff[['aktuelles_LtV', 'Berechnetes altes LtV', 'LtV Differenz']].head())