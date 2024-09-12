import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

# Đọc dữ liệu từ file CSV
df = pd.read_csv('hypothekendaten_converted.csv', delimiter=';')

# In ra tên các cột trong dữ liệu
print("Các cột trong dữ liệu:")
print(df.columns)

# Hàm chuyển đổi số với 2 chữ số thập phân và dấu phẩy
def flexible_numeric_conversion(series, decimals=2):
    if pd.api.types.is_numeric_dtype(series):
        return series.round(decimals)
    else:
        return pd.to_numeric(series.str.replace(',', '.'), errors='coerce').round(decimals)

# Chuyển đổi các cột sang dạng số với định dạng 2 chữ số thập phân
numeric_columns = ['aktuelles_LtV', 'darlehenbetrag', 'aktueller_immobilienwert', 'Schadensfaktor', 'AEP', 'Risikogewicht', 'Überschwemmungstiefe']
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

# Lưu file CSV với dấu ; phân cách và dấu thập phân là dấu ,
#df_results.to_csv('immobilien_analyse_ergebnisse.csv', index=False, decimal=',', sep=';')
#print("\nĐã lưu kết quả vào file 'immobilien_analyse_ergebnisse.csv'")
# Thiết lập style cho seaborn
sns.set_style("whitegrid")
plt.figure(figsize=(20, 25))

# Funktion zum Setzen der deutschen Schriftart
def set_german_font():
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['font.family'] = 'sans-serif'

set_german_font()

# 1. Histogram: Verteilung der Immobilienschäden
plt.subplot(3, 2, 1)
sns.histplot(data=df_results, x='Immobilienschaden', kde=True)
plt.title('Verteilung der Immobilienschäden')
plt.xlabel('Immobilienschaden')
plt.ylabel('Häufigkeit')

# 2. Scatter Plot: Aktueller Immobilienwert vs. Neuer Immobilienwert
plt.subplot(3, 2, 2)
plt.scatter(df_results['aktueller_immobilienwert'], df_results['Neuer Immobilienwert'])
plt.plot([df_results['aktueller_immobilienwert'].min(), df_results['aktueller_immobilienwert'].max()], 
         [df_results['aktueller_immobilienwert'].min(), df_results['aktueller_immobilienwert'].max()], 
         'r--', lw=2)
plt.title('Aktueller vs. Neuer Immobilienwert')
plt.xlabel('Aktueller Immobilienwert')
plt.ylabel('Neuer Immobilienwert')

# 3. Box Plot: RWA Änderung nach Flood Risk
plt.subplot(3, 2, 3)
sns.boxplot(x='flood_risk', y='RWA Änderung', data=df_results)
plt.title('RWA Änderung nach Flood Risk')
plt.xlabel('Flood Risk')
plt.ylabel('RWA Änderung')

# 4. Heatmap: Korrelationsmatrix
plt.subplot(3, 2, 4)
corr_matrix = df_results[['aktuelles_LtV', 'Neue LtV', 'Schadensfaktor', 'AEP', 'Risikogewicht', 'Neue Risikogewicht', 'RWA Änderung']].corr()
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0)
plt.title('Korrelationsmatrix')

# 5. Scatter Plot: Schadensfaktor vs. Überschwemmungstiefe
plt.subplot(3, 2, 5)
plt.scatter(df_results['Überschwemmungstiefe'], df_results['Schadensfaktor'])
plt.title('Schadensfaktor vs. Überschwemmungstiefe')
plt.xlabel('Überschwemmungstiefe')
plt.ylabel('Schadensfaktor')

# 6. Bar Plot: Durchschnittliche RWA Änderung nach Energieklasse
plt.subplot(3, 2, 6)
df_results.groupby('Energieklasse')['RWA Änderung'].mean().plot(kind='bar')
plt.title('Durchschnittliche RWA Änderung nach Energieklasse')
plt.xlabel('Energieklasse')
plt.ylabel('Durchschnittliche RWA Änderung')

plt.tight_layout()
plt.show()



# 8. Durchschnittliche Wertminderung nach Flood Risk
avg_value_decrease = df_results.groupby('flood_risk').apply(lambda x: (x['aktueller_immobilienwert'] - x['Neuer Immobilienwert']).mean())
print("\nDurchschnittliche Wertminderung nach Flood Risk:")
print(avg_value_decrease)

# 9. Prozentsatz der Immobilien mit erhöhtem Risikogewicht
increased_risk = (df_results['Neue Risikogewicht'] > df_results['Risikogewicht']).mean() * 100
print(f"\nProzentsatz der Immobilien mit erhöhtem Risikogewicht: {increased_risk:.2f}%")

# 10. Durchschnittliche EAI nach Landkreis
avg_eai_by_county = df_results.groupby('landkreis')['EAI'].mean().nlargest(10)
print("\nTop 10 Landkreise mit den höchsten durchschnittlichen EAI:")
print(avg_eai_by_county)

