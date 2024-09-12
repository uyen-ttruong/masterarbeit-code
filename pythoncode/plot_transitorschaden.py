import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Đọc dữ liệu
df = pd.read_csv('data/hypothekendaten4.csv', delimiter=';')

# Chuyển đổi các cột cần thiết sang kiểu số
numeric_columns = ['wohnflaeche', 'aktueller_immobilienwert', 'darlehenbetrag', 'aktuelles_LtV']
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')

energieklassen = ['B', 'C', 'D', 'F', 'G', 'H']
df = df[df['Energieklasse'].isin(energieklassen)]

# Định nghĩa các hằng số và biến
energieverbrauch = {'B': 62.5, 'C': 87.5, 'D': 115, 'F': 180, 'G': 225, 'H': 275}
df['E_j'] = df['Energieklasse'].map(energieverbrauch)

E_Aplus = 30
r = 0.024
T = 30

energiepreise = {
    'Netto-Null': [0.0422, 0.0473, 0.0684, 0.0938, 0.1341, 0.2200, 0.2821],
    'Ungeordnet': [0.0422, 0.0424, 0.0417, 0.0519, 0.0679, 0.1068, 0.2028],
    'Unter 2°C': [0.0422, 0.0437, 0.0502, 0.0584, 0.0686, 0.0847, 0.1126],
    'Aktuelle Richtlinien': [0.0422, 0.0424, 0.0417, 0.0416, 0.0425, 0.0425, 0.0428]
}

jahre = [2020, 2025, 2030, 2035, 2040, 2045, 2050]

def neue_werte_berechnen(zeile, PE_0, PE_1):
    try:
        E_j = float(zeile['E_j'])
        wohnflaeche = float(zeile['wohnflaeche'])
        aktueller_immobilienwert = float(zeile['aktueller_immobilienwert'])
        darlehenbetrag = float(zeile['darlehenbetrag'])

        delta_EC_rel = (E_j - E_Aplus) * (PE_1 - PE_0) * wohnflaeche
        delta_P = -delta_EC_rel * ((1 - (1 + r)**-T) / r) * aktueller_immobilienwert
        D_t = delta_P / aktueller_immobilienwert
        neuer_immobilienwert = aktueller_immobilienwert * (1 + D_t)
        neuer_beleihungsauslauf = darlehenbetrag / neuer_immobilienwert
        return pd.Series({
            'neuer_immobilienwert': neuer_immobilienwert, 
            'neuer_beleihungsauslauf': neuer_beleihungsauslauf, 
            'wertänderung': D_t
        })
    except Exception as e:
        print(f"Fehler in neue_werte_berechnen: {e}")
        print(f"Problematische Zeile: {zeile}")
        return pd.Series({
            'neuer_immobilienwert': np.nan, 
            'neuer_beleihungsauslauf': np.nan, 
            'wertänderung': np.nan
        })

# Tính toán kết quả
ergebnisse = {}
for szenario in energiepreise.keys():
    szenario_ergebnisse = []
    for i, jahr in enumerate(jahre):
        if i == 0:
            continue
        PE_0 = energiepreise[szenario][0]
        PE_1 = energiepreise[szenario][i]
        
        df[['neuer_immobilienwert', 'neuer_beleihungsauslauf', 'wertänderung']] = df.apply(
            lambda zeile: neue_werte_berechnen(zeile, PE_0, PE_1), axis=1)
        
        durchschnittliche_ergebnisse = df.groupby('Energieklasse').agg({
            'wertänderung': 'mean',
            'neuer_beleihungsauslauf': 'mean',
            'aktuelles_LtV': 'mean'
        }).rename(columns={
            'wertänderung': f'Wertänderung_{jahr}',
            'neuer_beleihungsauslauf': f'Neuer_LTV_{jahr}',
            'aktuelles_LtV': 'Alter_LTV'
        })
        
        durchschnittliche_ergebnisse['Jahr'] = jahr
        szenario_ergebnisse.append(durchschnittliche_ergebnisse)
    
    ergebnisse[szenario] = pd.concat(szenario_ergebnisse)

# Vẽ biểu đồ
plt.figure(figsize=(20, 15))

for i, (szenario, daten) in enumerate(ergebnisse.items(), 1):
    plt.subplot(2, 2, i)
    for ec in energieklassen:
        values = daten[daten.index == ec][[f'Wertänderung_{year}' for year in jahre[1:]]].values.flatten()
        plt.plot(jahre[1:], values, marker='o', label=f'Klasse {ec}')
    
    plt.title(f'Wertänderung im {szenario} Szenario')
    plt.xlabel('Jahr')
    plt.ylabel('Durchschnittliche Wertänderung')
    plt.legend()
    plt.grid(True)

plt.tight_layout()
plt.savefig('wertaenderung_ueber_zeit.png')
plt.close()

# Biểu đồ cột so sánh tác động giữa các kịch bản (cho năm 2050)
plt.figure(figsize=(12, 6))

x = np.arange(len(energieklassen))
width = 0.2

for i, (szenario, daten) in enumerate(ergebnisse.items()):
    values = daten[daten['Jahr'] == 2050]['Wertänderung_2050'].values
    plt.bar(x + i*width, values, width, label=szenario)

plt.xlabel('Energieeffizienzklasse')
plt.ylabel('Wertänderung im Jahr 2050')
plt.title('Vergleich der Szenarien im Jahr 2050')
plt.xticks(x + width * 1.5, energieklassen)
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig('szenario_vergleich_2050.png')
plt.close()

# Biểu đồ nhiệt (heatmap) cho LTV
plt.figure(figsize=(20, 15))

for i, (szenario, daten) in enumerate(ergebnisse.items(), 1):
    plt.subplot(2, 2, i)
    
    ltv_data = daten.pivot(index='Energieklasse', columns='Jahr', values=[f'Neuer_LTV_{year}' for year in jahre[1:]])
    sns.heatmap(ltv_data, annot=True, fmt='.4f', cmap='YlOrRd')
    
    plt.title(f'LTV im {szenario} Szenario')
    plt.xlabel('Jahr')
    plt.ylabel('Energieeffizienzklasse')

plt.tight_layout()
plt.savefig('ltv_heatmap.png')
plt.close()

print("Alle Berechnungen wurden durchgeführt und Diagramme erstellt.")