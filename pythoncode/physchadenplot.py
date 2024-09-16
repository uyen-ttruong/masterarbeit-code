import pandas as pd
import numpy as np
from tabulate import tabulate

# CSV-Datei lesen
df = pd.read_csv('data/hypothekendaten_final_with_id.csv', delimiter=';')

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

# Spalten in numerische Werte umwandeln
numeric_columns = ['aktuelles_LtV', 'darlehenbetrag', 'aktueller_immobilienwert', 'Schadensfaktor', 'AEP', 'Risikogewicht', 'Ueberschwemmungstiefe', 'Quadratmeterpreise', 'wohnflaeche']
for col in numeric_columns:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: flexible_numeric_conversion(x))

# Zeilen mit NaN-Werten entfernen
df = df.dropna(subset=[col for col in numeric_columns if col in df.columns])

# Funktion zur Bestimmung des Risikogewichts basierend auf LtV
def get_risikogewicht(ltv):
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

# Risikogewicht basierend auf aktuelles_LtV neu berechnen
df['Risikogewicht'] = df['aktuelles_LtV'].apply(get_risikogewicht)

# Funktion zur Berechnung der Werte
def calculate_values(row):
    E_j = row['aktueller_immobilienwert']
    schadenfaktor = row['Schadensfaktor']
    p_I_ij = row['AEP'] if 'AEP' in row.index else 0.01
    
    immobilienschaden = E_j * schadenfaktor
    EAI = immobilienschaden * p_I_ij
    neuer_immobilienwert = E_j - immobilienschaden
    
    # Neues LtV basierend auf dem neuen Immobilienwert berechnen
    neue_LtV = row['darlehenbetrag'] / neuer_immobilienwert if neuer_immobilienwert > 0 else np.inf
    
    # Neuberechnetes Risikogewicht verwenden
    risikogewicht = row['Risikogewicht']
    neue_risikogewicht = get_risikogewicht(neue_LtV)
    
    # RWA berechnen
    akt_RWA = row['darlehenbetrag'] * risikogewicht
    neue_RWA = row['darlehenbetrag'] * neue_risikogewicht
    RWA_Änderung = (neue_RWA / akt_RWA) - 1 if akt_RWA > 0 else np.inf
    
    return pd.Series({
        'Immobilienschaden': immobilienschaden, 
        'EAI': EAI, 
        'Neuer Immobilienwert': neuer_immobilienwert, 
        'Neue LtV': neue_LtV, 
        'Risikogewicht': risikogewicht,
        'Neue Risikogewicht': neue_risikogewicht,  
        'Akt. RWA': akt_RWA,
        'Neue RWA': neue_RWA, 
        'RWA Änderung': RWA_Änderung
    })

# Berechnungen auf jede Zeile anwenden
results = df.apply(calculate_values, axis=1)

# Ergebnisse mit dem ursprünglichen DataFrame kombinieren
df_results = pd.concat([df, results], axis=1)

# Daten filtern, um nur Zeilen mit nicht null Schadensfaktor zu behalten
df_damage = df_results[df_results['Schadensfaktor'] != 0].copy()

# Summen für Akt. RWA und Neue RWA berechnen
akt_rwa_sum = df_damage['Akt. RWA'].sum()
neue_rwa_sum = df_damage['Neue RWA'].sum()

# Relevante Spalten auswählen und nach absoluter RWA Änderung sortieren
table_data = df_damage[['ID', 'aktuelles_LtV', 'Neue LtV', 'Risikogewicht', 'Neue Risikogewicht', 'Akt. RWA', 'Neue RWA', 'RWA Änderung']].copy()
table_data['Abs RWA Änderung'] = table_data['RWA Änderung'].abs()
table_data = table_data.sort_values('Abs RWA Änderung', ascending=False).head(13)

# Daten für bessere Lesbarkeit formatieren
table_data['aktuelles_LtV'] = table_data['aktuelles_LtV'].map(lambda x: f"{x:.2f}")
table_data['Neue LtV'] = table_data['Neue LtV'].map(lambda x: f"{x:.2f}")
table_data['Risikogewicht'] = table_data['Risikogewicht'].map(lambda x: f"{x:.2f}")
table_data['Neue Risikogewicht'] = table_data['Neue Risikogewicht'].map(lambda x: f"{x:.2f}")
table_data['Akt. RWA'] = table_data['Akt. RWA'].map(lambda x: f"{x:,.2f}")
table_data['Neue RWA'] = table_data['Neue RWA'].map(lambda x: f"{x:,.2f}")
table_data['RWA Änderung'] = table_data['RWA Änderung'].map(lambda x: f"{x:.2f}")

# Temporäre Spalte für Sortierung entfernen
table_data = table_data.drop('Abs RWA Änderung', axis=1)

# Überprüfen und Entfernen doppelter Spalten
table_data = table_data.loc[:, ~table_data.columns.duplicated()]

# Erstellen einer Zusammenfassungszeile mit der richtigen Spaltenanzahl
sum_row = pd.DataFrame([['Sum', '', '', '', '', f"{akt_rwa_sum:,.2f}", f"{neue_rwa_sum:,.2f}", '']], 
                       columns=table_data.columns)

# Zusammenfassungszeile mit der Tabelle kombinieren
table_data = pd.concat([table_data, sum_row], ignore_index=True)

# Tabelle erstellen und drucken
table = tabulate(table_data, headers='keys', tablefmt='pipe', showindex=False)
print("\nDie Top 13 Zeilen der relevanten Spalten mit RWA-Summen:")
print(table)


