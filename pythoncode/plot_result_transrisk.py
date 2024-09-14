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

# Chuyển đổi các cột cần thiết sang kiểu số, thay dấu phẩy thành dấu chấm
numeric_columns = ['wohnflaeche', 'aktueller_immobilienwert', 'darlehenbetrag', 'aktuelles_LtV', 'Risikogewicht']
for col in numeric_columns:
    if col in df.columns:
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

# Hàm tính toán Risikogewicht dựa trên LtV
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

# Hàm tính toán giá trị mới
def neue_werte_berechnen(zeile, PE_0, PE_1):
    try:
        E_j = float(zeile['E_j'])
        wohnflaeche = float(zeile['wohnflaeche'])
        aktueller_immobilienwert = float(zeile['aktueller_immobilienwert'])
        darlehenbetrag = float(zeile['darlehenbetrag'])
        old_RWA = darlehenbetrag * float(zeile.get('Risikogewicht', 0))

        delta_EC_rel = (E_j - E_Aplus) * (PE_1 - PE_0) * wohnflaeche
        delta_P = -delta_EC_rel * ((1 - (1 + r)**-T) / r)
        neuer_immobilienwert = aktueller_immobilienwert + delta_P
        D_t = delta_P / aktueller_immobilienwert
        neuer_beleihungsauslauf = darlehenbetrag / neuer_immobilienwert
        
        neue_risikogewicht = get_neue_risikogewicht(neuer_beleihungsauslauf)
        new_RWA = darlehenbetrag * neue_risikogewicht
        
        return pd.Series({
            'aktueller_immobilienwert': aktueller_immobilienwert,
            'neuer_immobilienwert': neuer_immobilienwert, 
            'aktuelles_LtV': zeile['aktuelles_LtV'],
            'neuer_beleihungsauslauf': neuer_beleihungsauslauf, 
            'wertänderung': D_t,
            'delta_P': delta_P,  # Trả về delta_P
            'old_RWA': old_RWA,
            'new_RWA': new_RWA,
            'RWA_änderung': (new_RWA / old_RWA) - 1 if old_RWA > 0 else np.nan
        })
    except Exception as e:
        print(f"Fehler in neue_werte_berechnen: {e}")
        return pd.Series({
            'aktueller_immobilienwert': np.nan,
            'neuer_immobilienwert': np.nan, 
            'aktuelles_LtV': np.nan,
            'neuer_beleihungsauslauf': np.nan, 
            'wertänderung': np.nan,
            'delta_P': np.nan,  # Trả về NaN nếu có lỗi
            'old_RWA': np.nan,
            'new_RWA': np.nan,
            'RWA_änderung': np.nan
        })
print("Bắt đầu tính toán cho các kịch bản.")

# # Kết quả cho mỗi kịch bản
# ergebnisse = {}
# for szenario in energiepreise.keys():
#     print(f"Đang xử lý kịch bản: {szenario}")
#     szenario_ergebnisse = []
    
#     for i, jahr in enumerate(jahre):
#         print(f"  Đang xử lý năm: {jahr}")
#         PE_0 = energiepreise[szenario][0]
#         PE_1 = energiepreise[szenario][i]

#         # Áp dụng tính toán cho mỗi hàng
#         df_result = df.apply(lambda zeile: neue_werte_berechnen(zeile, PE_0, PE_1), axis=1)

#         # Tính giá trị trung bình theo Energieklasse
#         durchschnittliche_ergebnisse = df_result.groupby(df['Energieklasse']).mean().rename(columns={
#             'aktueller_immobilienwert': f'durchschnittlicher_aktueller_immobilienwert_{jahr}',
#             'neuer_immobilienwert': f'durchschnittlicher_neuer_immobilienwert_{jahr}',
#             'aktuelles_LtV': f'durchschnittliches_aktuelles_LtV_{jahr}',
#             'neuer_beleihungsauslauf': f'durchschnittlicher_neuer_beleihungsauslauf_{jahr}',
#             'wertänderung': f'durchschnittliche_wertänderung_{jahr}',
#             'RWA_änderung': f'durchschnittliche_RWA_änderung_{jahr}'
#         })

#         szenario_ergebnisse.append(durchschnittliche_ergebnisse)

#     # Kết hợp kết quả của tất cả các năm
#     ergebnisse[szenario] = pd.concat(szenario_ergebnisse, axis=1)

# print("Đã hoàn thành tính toán. Bắt đầu in kết quả.")

# # In kết quả
# for szenario, daten in ergebnisse.items():
#     print(f"\nErgebnisse für das Szenario {szenario}:")
#     print(daten.head())  # Kiểm tra dữ liệu kết quả trước khi lưu

#     # Tạo bảng kết quả
#     result_table = pd.DataFrame(index=energieklassen)
    
#     for jahr in jahre:
#         try:
#             result_table[f'{jahr} Aktueller Wert'] = daten[f'durchschnittlicher_aktueller_immobilienwert_{jahr}'].round(2)
#             result_table[f'{jahr} Neuer Wert'] = daten[f'durchschnittlicher_neuer_immobilienwert_{jahr}'].round(2)
#             result_table[f'{jahr} Aktuelles LtV'] = daten[f'durchschnittliches_aktuelles_LtV_{jahr}'].round(4)
#             result_table[f'{jahr} Neues LtV'] = daten[f'durchschnittlicher_neuer_beleihungsauslauf_{jahr}'].round(4)
#             result_table[f'{jahr} Wertänderung'] = daten[f'durchschnittliche_wertänderung_{jahr}'].round(4)
#             result_table[f'{jahr} RWA Änderung'] = daten[f'durchschnittliche_RWA_änderung_{jahr}'].round(4)
#         except KeyError as e:
#             print(f"Lỗi: Không tìm thấy dữ liệu cho năm {jahr} trong kịch bản {szenario}: {e}")
    
#     print("Bảng kết quả đã được tạo.")
# Cập nhật hàm tính toán để trả về delta_P
def neue_werte_berechnen(zeile, PE_0, PE_1):
    try:
        E_j = float(zeile['E_j'])
        wohnflaeche = float(zeile['wohnflaeche'])
        aktueller_immobilienwert = float(zeile['aktueller_immobilienwert'])
        darlehenbetrag = float(zeile['darlehenbetrag'])
        old_RWA = darlehenbetrag * float(zeile.get('Risikogewicht', 0))

        delta_EC_rel = (E_j - E_Aplus) * (PE_1 - PE_0) * wohnflaeche
        delta_P = -delta_EC_rel * ((1 - (1 + r)**-T) / r)
        neuer_immobilienwert = aktueller_immobilienwert + delta_P
        D_t = delta_P / aktueller_immobilienwert
        neuer_beleihungsauslauf = darlehenbetrag / neuer_immobilienwert
        
        neue_risikogewicht = get_neue_risikogewicht(neuer_beleihungsauslauf)
        new_RWA = darlehenbetrag * neue_risikogewicht
        
        return pd.Series({
            'Energieklasse': zeile['Energieklasse'],
            'delta_P': delta_P  # Trả về delta_P
        })
    except Exception as e:
        print(f"Fehler in neue_werte_berechnen: {e}")
        return pd.Series({
            'Energieklasse': np.nan,
            'delta_P': np.nan
        })

print("Bắt đầu tính toán cho các kịch bản.")

# Kết quả cho mỗi kịch bản
ergebnisse = {}
for szenario in energiepreise.keys():
    print(f"Đang xử lý kịch bản: {szenario}")
    
    for i, jahr in enumerate(jahre):
        print(f"  Đang xử lý năm: {jahr}")
        PE_0 = energiepreise[szenario][0]
        PE_1 = energiepreise[szenario][i]

        # Áp dụng tính toán cho mỗi hàng
        df_result = df.apply(lambda zeile: neue_werte_berechnen(zeile, PE_0, PE_1), axis=1)

        # In ra bảng giá trị delta_P cho mỗi kịch bản và từng loại nhà
        print(f"\nBảng giá trị delta_P cho kịch bản {szenario} trong năm {jahr}:")
        print(df_result[['Energieklasse', 'delta_P']])

        # Kiểm tra xem trong từng loại nhà có giá trị delta_P dương không
        for klasse in energieklassen:
            klasse_df = df_result[df_result['Energieklasse'] == klasse]
            positive_delta_P = klasse_df[klasse_df['delta_P'] > 0]
            
            if not positive_delta_P.empty:
                print(f"\nTrong kịch bản {szenario}, năm {jahr}, loại nhà {klasse} có giá trị delta_P dương:")
                print(positive_delta_P[['Energieklasse', 'delta_P']])
            else:
                print(f"\nTrong kịch bản {szenario}, năm {jahr}, loại nhà {klasse} không có giá trị delta_P dương.")

