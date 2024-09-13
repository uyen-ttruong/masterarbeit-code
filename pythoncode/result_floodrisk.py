import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Daten von CSV-Datei lesen
df = pd.read_csv('data\hypothekendaten_final_with_statistics.csv', delimiter=';')

# ID-Spalte hinzufügen, falls sie nicht vorhanden ist
if 'ID' not in df.columns:
    df['ID'] = range(1, len(df) + 1)

# Flexible Konvertierungsfunktion
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

# Umwandlung der numerischen Spalten
numeric_columns = ['aktueller_immobilienwert', 'Schadensfaktor', 'AEP', 'darlehenbetrag', 'Risikogewicht']
for col in numeric_columns:
    df[col] = df[col].apply(lambda x: flexible_numeric_conversion(x))

# Funktion zur Bestimmung des neuen Risikogewichts basierend auf dem neuen LtV
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

# Funktion zur Berechnung der Werte
def calculate_values(row, T=20):
    E_j = row['aktueller_immobilienwert']
    schadenfaktor = row['Schadensfaktor']
    p_I_ij = row['AEP'] if 'AEP' in row.index else 0.01

    # Berechnung des Immobilienschadens
    immobilienschaden = E_j * schadenfaktor

    # Berechnung des EAI
    EAI = immobilienschaden * p_I_ij

    # Berechnung des EI
    EI = EAI * T

    # Berechnung des neuen Immobilienwerts
    new_immobilienwert = E_j - immobilienschaden

    # Berechnung des neuen LtV
    new_LtV = row['darlehenbetrag'] / new_immobilienwert if new_immobilienwert > 0 else np.inf

    # Bestimmung des neuen Risikogewichts basierend auf dem neuen LtV
    neue_risikogewicht = get_neue_risikogewicht(new_LtV)

    # Berechnung des neuen RWA basierend auf dem neuen Risikogewicht
    new_RWA = row['darlehenbetrag'] * neue_risikogewicht

    # Berechnung der % Änderung von RWA
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

# Anwenden der Berechnungen auf jede Zeile
df_results = pd.concat([df, df.apply(calculate_values, axis=1)], axis=1)

# Filtern der Daten, um nur die Zeilen zu behalten, bei denen der Schadensfaktor ungleich 0 ist
df_damage = df_results[df_results['Schadensfaktor'] != 0].copy()

#plot hinh quat
# Tính tổng thiệt hại cho từng tài sản: immobilienschaden = immobillienwert * schadenfaktor
# Tính tổng thiệt hại cho từng tài sản: immobilienschaden = immobillienwert * schadenfaktor
df_damage['total_schadensfaktor_value'] = df_damage['aktueller_immobilienwert'] * df_damage['Schadensfaktor']

# Tổng giá trị thiệt hại từ schadenfaktor
total_schadensfaktor_value = df_damage['total_schadensfaktor_value'].sum()
total_immobilienwert = df_damage['aktueller_immobilienwert'].sum()
print(total_schadensfaktor_value)
print(total_immobilienwert)
print(df_results['aktueller_immobilienwert'].sum())

# Tạo biểu đồ hình quạt cho tổng thiệt hại dựa trên aktueller immobilienwert và schadenfaktor
plt.figure(figsize=(8, 8))

# Tạo dữ liệu cho biểu đồ
labels = ['Gesamtschadenwert', '']  # Đổi thành cụm từ học thuật hơn
sizes = [total_schadensfaktor_value, total_immobilienwert - total_schadensfaktor_value]
colors = ['#E9C46A', '#2A9D8F']  # Đổi vị trí màu vàng và xanh

# Tạo biểu đồ với đường viền đậm và điều chỉnh khoảng cách label, pctdistance
wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                   startangle=140, wedgeprops=dict(edgecolor='black', linewidth=2),
                                   pctdistance=0.85, labeldistance=1.1)

# Thiết lập font chữ và kích thước
for text in texts + autotexts:
    text.set_fontsize(12)

# Hiển thị biểu đồ
plt.axis('equal')
plt.tight_layout()
plt.show()

# Tính tổng thiệt hại trong một năm (EAI đã được tính dựa trên schadenfaktor)
total_schaden_pro_jahr = df_damage['EAI'].sum()

# Tạo biểu đồ hình quạt cho tổng thiệt hại dựa trên EAI trong 1 năm
plt.figure(figsize=(8, 8))

# Tạo dữ liệu cho biểu đồ
labels = ['Gesamtschadenwert (1 Jahr)', '']  # Đổi thành cụm từ học thuật hơn
sizes = [total_schaden_pro_jahr, total_immobilienwert - total_schaden_pro_jahr]
colors = ['#E9C46A', '#2A9D8F']  # Sử dụng màu sắc giống biểu đồ 1

# Tạo biểu đồ với đường viền đậm và điều chỉnh khoảng cách label, pctdistance
wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                   startangle=140, wedgeprops=dict(edgecolor='black', linewidth=2),
                                   pctdistance=1.1, labeldistance=1.5)

# Thiết lập font chữ và kích thước
for text in texts + autotexts:
    text.set_fontsize(12)

# Hiển thị biểu đồ
plt.axis('equal')
plt.tight_layout()
plt.show()
# # Formatierungsfunktion für Euro
# def format_euro(x, p):
#     return f"{x:,.0f} €".replace(",", ".")

# # Plot 1: Verteilung des Immobilienschadens
# plt.figure(figsize=(16, 8))
# sns.histplot(df_damage['Immobilienschaden'], kde=True, bins=20, color='skyblue')

# mean_value = df_damage['Immobilienschaden'].mean()
# median_value = df_damage['Immobilienschaden'].median()

# plt.axvline(mean_value, color='green', linestyle='--', label=f'Mean: {mean_value:,.2f} €'.replace(",", "."))
# plt.axvline(median_value, color='red', linestyle='-.', label=f'Median: {median_value:,.2f} €'.replace(",", "."))

# plt.legend()
# plt.title('Verteilung des Immobilienschadens')
# plt.xlabel('Immobilienschaden (in Euro)', labelpad=10)
# plt.ylabel('Häufigkeit')

# plt.gca().xaxis.set_major_formatter(FuncFormatter(format_euro))
# plt.grid(True)
# plt.xticks(rotation=45, ha='right')
# plt.gca().xaxis.set_major_locator(plt.MaxNLocator(10))

# plt.tight_layout(rect=[0, 0.03, 1, 0.95])
# #plt.show()

# # Plot 2: Vergleich von RWA
# plt.figure(figsize=(16, 8))

# bar_width = 0.4
# index = np.arange(len(df_damage))

# plt.bar(index, df_damage['darlehenbetrag'] * df_damage['Risikogewicht'], bar_width, label='RWA cũ', color='#6495ED')
# plt.bar(index + bar_width, df_damage['Neue RWA'], bar_width, label='RWA mới', color='#FFB6C1')

# plt.xticks(index + bar_width / 2, df_damage['ID'].astype(str), rotation=45, ha='right')

# plt.title('Vergleich zwischen altem und neuem RWA')
# plt.xlabel('Immobilien ID', labelpad=10)
# plt.ylabel('RWA (in Euro)', labelpad=10)

# plt.gca().yaxis.set_major_formatter(FuncFormatter(format_euro))

# plt.legend()
# plt.grid(True, axis='y')

# plt.tight_layout()
# #plt.show()

# # Plot 3: Vergleich von LtV
# # Dữ liệu được sắp xếp theo 'Neue LtV' từ thấp đến cao
# df_damage_sorted = df_damage.sort_values(by='Neue LtV')

# # Tạo biểu đồ cột so sánh LtV cũ và LtV mới
# plt.figure(figsize=(16, 8))

# bar_width = 0.4
# index = np.arange(len(df_damage_sorted))

# # Vẽ biểu đồ cột cho LtV cũ
# plt.bar(index, df_damage_sorted['aktuelles_LtV'], bar_width, label='aktueller LtV', color='lightblue')

# # Vẽ biểu đồ cột cho LtV mới với độ lệch
# plt.bar(index + bar_width, df_damage_sorted['Neue LtV'], bar_width, label='neuer LtV', color='darkblue')

# # Đặt tên cho các cột là Immobilien ID dựa trên cột ID và sắp xếp theo thứ tự đã sắp xếp
# plt.xticks(index + bar_width / 2, [f'ID: {id_}' for id_ in df_damage_sorted['ID']], rotation=45, ha='right')

# # Thêm tiêu đề và nhãn
# plt.xlabel('Immobilien ID', labelpad=10)
# plt.ylabel('LtV (%)', labelpad=10)

# # Định dạng trục y theo dạng phần trăm
# plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.0%}'))

# # Thêm chú thích và lưới
# plt.legend()
# plt.grid(True, axis='y')

# # Tinh chỉnh bố cục
# plt.tight_layout()

# # Hiển thị biểu đồ
# #plt.show()