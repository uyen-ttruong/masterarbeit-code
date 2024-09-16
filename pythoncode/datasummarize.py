import pandas as pd
import numpy as np

# Daten von CSV-Datei lesen
df = pd.read_csv('data/hypothekendaten_final_with_statistics.csv', delimiter=';')

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
numeric_columns = ['Quadratmeterpreise', 'wohnflaeche','aktueller_immobilienwert', 'aktuelles_LtV', 'darlehenbetrag']
for col in numeric_columns:
    df[col] = df[col].apply(lambda x: flexible_numeric_conversion(x))

# Speichern der aktualisierten Daten in eine neue CSV-Datei
df.to_csv('data/hypothekendaten_final_with_id.csv', index=False, sep=';')

# Ausgabe aller Spaltennamen
print("Spaltennamen:")
print(df.columns.tolist())

# Statistiken für numerische Spalten
print("\nStatistiken für numerische Spalten:")
numeric_stats = df[numeric_columns].describe()
print(numeric_stats)