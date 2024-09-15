import pandas as pd
import numpy as np
from tabulate import tabulate
import matplotlib.pyplot as plt

print("Skript wird gestartet.")

# Daten
try:
    df = pd.read_csv('data/hypothekendaten4.csv', delimiter=';')
    print("Daten erfolgreich geladen.")
except Exception as e:
    print(f"Fehler beim Laden der Daten: {e}")
    exit()

print(f"Anzahl der Zeilen im DataFrame: {len(df)}")
print(f"Spalten im DataFrame: {df.columns.tolist()}")

# Konvertierung der erforderlichen Spalten in numerische Werte, Ersetzen von Komma durch Punkt
numeric_columns = ['wohnflaeche', 'aktueller_immobilienwert', 'darlehenbetrag', 'aktuelles_LtV', 'Risikogewicht']
for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')

print("Spalten in numerische Werte konvertiert.")

energieklassen = ['B', 'C', 'D', 'F', 'G', 'H']
df = df[df['Energieklasse'].isin(energieklassen)]

print(f"Anzahl der Zeilen nach Filterung nach Energieklasse: {len(df)}")

# Ausgabe der Anzahl für jede Energieklasse
print("\nAnzahl für jede Energieklasse:")
energieklasse_counts = df['Energieklasse'].value_counts().sort_index()
for klasse in energieklassen:
    count = energieklasse_counts.get(klasse, 0)
    print(f"Energieklasse {klasse}: {count}")

# Energieverbrauch für jede Klasse
energieverbrauch = {
    'B': 62.5, 'C': 87.5, 'D': 115, 'F': 180, 'G': 225, 'H': 275
}

# Hinzufügen der Spalte 'E_j'
df['E_j'] = df['Energieklasse'].map(energieverbrauch)

# Konstanten
E_Aplus = 30
r = 0.024
T = 30

# Energiepreise für verschiedene Szenarien (nur für 2050)
energiepreise = {
    'Netto-Null': [0.0623, 0.3389],
    'Ungeordnet': [0.0581, 0.2593],
    'Unter 2°C': [0.0598, 0.1622],
    'Aktuelle Richtlinien': [0.0581, 0.0594]
}

# Funktion zur Berechnung des Risikogewichts basierend auf LtV
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

# Funktion zur Berechnung neuer Werte
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
            'delta_P': delta_P,
            'old_RWA': old_RWA,
            'new_RWA': new_RWA,
            'RWA_change': (new_RWA / old_RWA) - 1 if old_RWA > 0 else np.nan
        })
    except Exception as e:
        print(f"Fehler in neue_werte_berechnen: {e}")
        return pd.Series({
            'Energieklasse': np.nan,
            'delta_P': np.nan,
            'old_RWA': np.nan,
            'new_RWA': np.nan,
            'RWA_change': np.nan
        })

print("Beginne mit der Berechnung für die Szenarien im Jahr 2050.")

# Ergebnisse für jedes Szenario
for szenario, preise in energiepreise.items():
    print(f"\nVerarbeite Szenario: {szenario}")
    
    PE_0 = preise[0]
    PE_1 = preise[1]

    # Anwendung der Berechnung auf jede Zeile
    df_result = df.apply(lambda zeile: neue_werte_berechnen(zeile, PE_0, PE_1), axis=1)

    # Ausgabe der Tabelle mit Werten für delta_P, old_RWA, new_RWA und RWA_change für jedes Szenario und jede Hausart
    print(f"\nWertetabelle für Szenario {szenario} im Jahr 2050:")
    summary = df_result.groupby('Energieklasse').agg({
        'delta_P': 'mean',
        'old_RWA': 'mean',
        'new_RWA': 'mean',
        'RWA_change': 'mean'
    }).round(2)
    print(summary)

    # Überprüfung, ob es in jeder Hausart einen Anstieg des RWA-Werts gibt
    for klasse in energieklassen:
        klasse_df = df_result[df_result['Energieklasse'] == klasse]
        increased_RWA = klasse_df[klasse_df['RWA_change'] > 0]
        
        if not increased_RWA.empty:
            print(f"\nIm Szenario {szenario}, Jahr 2050, Haustyp {klasse} mit RWA-Anstieg:")
            print(f"Anzahl: {len(increased_RWA)}")
            print(f"Durchschnittlicher Anstieg: {increased_RWA['RWA_change'].mean():.2%}")
            print(f"Maximaler Anstieg: {increased_RWA['RWA_change'].max():.2%}")
        else:
            print(f"\nIm Szenario {szenario}, Jahr 2050, Haustyp {klasse} ohne RWA-Anstieg.")

    # Berechnung und Ausgabe des Gesamt-RWA (alt und neu) für jedes Szenario
    total_old_RWA = df_result['old_RWA'].sum()
    total_new_RWA = df_result['new_RWA'].sum()
    total_RWA_change = (total_new_RWA / total_old_RWA) - 1 if total_old_RWA > 0 else np.nan
    
    print(f"\nGesamt-RWA für Szenario {szenario} im Jahr 2050:")
    print(f"Gesamt-RWA alt: {total_old_RWA:,.2f}")
    print(f"Gesamt-RWA neu: {total_new_RWA:,.2f}")
    print(f"Änderung Gesamt-RWA: {total_RWA_change:.2%}")

print("\nBerechnung und Ausgabe der Ergebnisse abgeschlossen.")