import pandas as pd
import numpy as np
from tabulate import tabulate
import matplotlib.pyplot as plt

print("Bắt đầu chạy script.")

# Dữ liệu
try:
    df = pd.read_csv('data/hypothekendaten4.csv', delimiter=';')
    print("Đã tải dữ liệu thành công.")
except Exception as e:
    print(f"Lỗi khi tải dữ liệu: {e}")
    exit()

print(f"Số dòng trong DataFrame: {len(df)}")
print(f"Các cột trong DataFrame: {df.columns.tolist()}")

# Chuyển đổi các cột cần thiết sang kiểu số
numeric_columns = ['wohnflaeche', 'aktueller_immobilienwert', 'darlehenbetrag', 'aktuelles_LtV']
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')

print("Đã chuyển đổi các cột sang kiểu số.")

energieklassen = ['B', 'C', 'D', 'F', 'G', 'H']
df = df[df['Energieklasse'].isin(energieklassen)]

print(f"Số dòng sau khi lọc theo Energieklasse: {len(df)}")

# Energieverbrauch cho mỗi Klasse
energieverbrauch = {
    'B': 62.5, 'C': 87.5, 'D': 115, 'F': 180, 'G': 225, 'H': 275
}

# Thêm cột 'E_j'
df['E_j'] = df['Energieklasse'].map(energieverbrauch)

# Các hằng số
E_Aplus = 30
r = 0.024
T = 30

# Giá năng lượng cho các kịch bản
energiepreise = {
    'Netto-Null': [0.0623, 0.0652, 0.0868, 0.1117, 0.1584, 0.2606, 0.3389],
    'Ungeordnet': [0.0581, 0.0582, 0.0578, 0.0738, 0.0954, 0.1411, 0.2593],
    'Unter 2°C': [0.0598, 0.0609, 0.0720, 0.0830, 0.0983, 0.1222, 0.1622],
    'Aktuelle Richtlinien': [0.0581, 0.0582, 0.0578, 0.0581, 0.0591, 0.0596, 0.0594]
}

jahre = [2023, 2025, 2030, 2035, 2040, 2045, 2050]

def neue_werte_berechnen(zeile, PE_0, PE_1):
    try:
        E_j = float(zeile['E_j'])
        wohnflaeche = float(zeile['wohnflaeche'])
        aktueller_immobilienwert = float(zeile['aktueller_immobilienwert'])
        darlehenbetrag = float(zeile['darlehenbetrag'])

        delta_EC_rel = (E_j - E_Aplus) * (PE_1 - PE_0) * wohnflaeche
        delta_P = -delta_EC_rel * ((1 - (1 + r)**-T) / r)
        neuer_immobilienwert = aktueller_immobilienwert + delta_P
        D_t = delta_P / aktueller_immobilienwert
        neuer_beleihungsauslauf = darlehenbetrag / neuer_immobilienwert
        
        return pd.Series({
            'aktueller_immobilienwert': aktueller_immobilienwert,
            'neuer_immobilienwert': neuer_immobilienwert, 
            'aktuelles_LtV': zeile['aktuelles_LtV'],
            'neuer_beleihungsauslauf': neuer_beleihungsauslauf, 
            'wertänderung': D_t
        })
    except Exception as e:
        print(f"Fehler in neue_werte_berechnen: {e}")
        return pd.Series({
            'aktueller_immobilienwert': np.nan,
            'neuer_immobilienwert': np.nan, 
            'aktuelles_LtV': np.nan,
            'neuer_beleihungsauslauf': np.nan, 
            'wertänderung': np.nan
        })

print("Bắt đầu tính toán cho các kịch bản.")

# Kết quả cho mỗi kịch bản
ergebnisse = {}
for szenario in energiepreise.keys():
    print(f"Đang xử lý kịch bản: {szenario}")
    szenario_ergebnisse = []
    
    for i, jahr in enumerate(jahre):
        print(f"  Đang xử lý năm: {jahr}")
        PE_0 = energiepreise[szenario][0]
        PE_1 = energiepreise[szenario][i]

        # Áp dụng tính toán cho mỗi hàng
        df_result = df.apply(lambda zeile: neue_werte_berechnen(zeile, PE_0, PE_1), axis=1)

        # Tính giá trị trung bình theo Energieklasse
        durchschnittliche_ergebnisse = df_result.groupby(df['Energieklasse']).mean().rename(columns={
            'aktueller_immobilienwert': f'durchschnittlicher_aktueller_immobilienwert_{jahr}',
            'neuer_immobilienwert': f'durchschnittlicher_neuer_immobilienwert_{jahr}',
            'aktuelles_LtV': f'durchschnittliches_aktuelles_LtV_{jahr}',
            'neuer_beleihungsauslauf': f'durchschnittlicher_neuer_beleihungsauslauf_{jahr}',
            'wertänderung': f'durchschnittliche_wertänderung_{jahr}'
        })

        szenario_ergebnisse.append(durchschnittliche_ergebnisse)

    # Kết hợp kết quả của tất cả các năm
    ergebnisse[szenario] = pd.concat(szenario_ergebnisse, axis=1)

print("Đã hoàn thành tính toán. Bắt đầu in kết quả.")

# In kết quả
for szenario, daten in ergebnisse.items():
    print(f"\nErgebnisse für das Szenario {szenario}:")
    print(daten.head())  # Kiểm tra dữ liệu kết quả trước khi lưu

    # Tạo bảng kết quả
    result_table = pd.DataFrame(index=energieklassen)
    
    for jahr in jahre:
        try:
            result_table[f'{jahr} Aktueller Wert'] = daten[f'durchschnittlicher_aktueller_immobilienwert_{jahr}'].round(2)
            result_table[f'{jahr} Neuer Wert'] = daten[f'durchschnittlicher_neuer_immobilienwert_{jahr}'].round(2)
            result_table[f'{jahr} Aktuelles LtV'] = daten[f'durchschnittliches_aktuelles_LtV_{jahr}'].round(4)
            result_table[f'{jahr} Neues LtV'] = daten[f'durchschnittlicher_neuer_beleihungsauslauf_{jahr}'].round(4)
            result_table[f'{jahr} Wertänderung'] = daten[f'durchschnittliche_wertänderung_{jahr}'].round(4)
        except KeyError as e:
            print(f"Lỗi: Không tìm thấy dữ liệu cho năm {jahr} trong kịch bản {szenario}: {e}")
    
    print("Bảng kết quả đã được tạo.")
    print(result_table)  # In DataFrame
colors = {
    'B': 'red',
    'C': 'green',
    'D': 'blue',
    'F': 'orange',
    'G': 'purple',
    'H': 'brown'
}
def plot_scenario(szenario, ergebnisse):
    plt.figure(figsize=(12, 8))

    # Lặp qua các lớp năng lượng để vẽ dữ liệu
    for klasse in energieklassen:
        # Kiểm tra nếu dữ liệu tồn tại cho từng lớp
        if klasse in ergebnisse[szenario].index:
            color = colors[klasse]  # Màu cho lớp hiện tại

            # Chỉ vẽ giá trị mới (neuer_immobilienwert)
            plt.plot(jahre, ergebnisse[szenario].loc[klasse, [f'durchschnittlicher_neuer_immobilienwert_{jahr}' for jahr in jahre]] / 1000,
                     label=f'{klasse}', linestyle='-', marker='o', color=color)
        else:
            print(f"Keine Daten für Klasse {klasse} im Szenario {szenario}")

    # Cài đặt các tham số biểu đồ
    plt.xlabel('Jahr')
    plt.ylabel('Immobilienwert (in Tausend Euro)')
    plt.title(f'Immobilienwertentwicklung für Szenario {szenario}')
    plt.legend()
    plt.grid(True)

    # Hiển thị biểu đồ
    plt.show()
def plot_percentage_change(szenario, ergebnisse):
    plt.figure(figsize=(12, 8))

    for klasse in energieklassen:
        if klasse in ergebnisse[szenario].index:
            color = colors[klasse]
            
            # Tính phần trăm thay đổi
            wertänderung = [ergebnisse[szenario].loc[klasse, f'durchschnittliche_wertänderung_{jahr}'] for jahr in jahre]
            percentage_change = [change * 100 for change in wertänderung]  # Chuyển đổi sang phần trăm
            
            plt.plot(jahre, percentage_change, label=f'{klasse}', linestyle='-', marker='o', color=color)
        else:
            print(f"Keine Daten für Klasse {klasse} im Szenario {szenario}")

    plt.axhline(y=0, color='r', linestyle='--')  # Thêm đường 0%
    plt.xlabel('Jahr')
    plt.ylabel('Prozentuale Wertänderung (%)')
    plt.title(f'Prozentuale Wertänderung der Immobilien für Szenario {szenario}')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'{szenario}_percentage_change_plot.png')
    plt.close()
# Gọi hàm để vẽ biểu đồ cho từng kịch bản
for szenario in energiepreise.keys():
    print(f"Erzeuge Diagramm für Szenario: {szenario}")
    #plot_scenario(szenario, ergebnisse)
    plot_percentage_change(szenario, ergebnisse)