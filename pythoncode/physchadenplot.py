import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Đọc dữ liệu từ file CSV
df = pd.read_csv('data/hypothekendaten4.csv', delimiter=';')

# In ra tên các cột trong dữ liệu
print("Các cột trong dữ liệu:")
print(df.columns)

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

# Lọc dữ liệu chỉ giữ lại các hàng có Schadensfaktor khác 0
df_damage = df_results[df_results['Schadensfaktor'] != 0].copy()

# Diagramm zeichnen
plt.figure(figsize=(10,6))
sns.histplot(df_damage['Immobilienschaden'], kde=True, bins=10, color='skyblue')

# Thêm mean và median vào biểu đồ
mean_value = df_damage['Immobilienschaden'].mean()
median_value = df_damage['Immobilienschaden'].median()

plt.axvline(mean_value, color='red', linestyle='--', label=f'Mean: {mean_value:.2f} €')
plt.axvline(median_value, color='green', linestyle='-.', label=f'Median: {median_value:.2f} €')

# Đặt nhãn cho trục X và Y
plt.xlabel('Immobilienschaden (€)')
plt.ylabel('Häufigkeit')
plt.title('Verteilung des Immobilienschadens')

# Định dạng các giá trị trục X để thêm ký hiệu €
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels([f'{int(val):,} €' for val in x_values])

plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
