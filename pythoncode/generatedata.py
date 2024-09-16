import pandas as pd
import numpy as np

# CSV-Datei lesen
df = pd.read_csv("C:\Users\uyen truong\Downloads\hypothekendatenroh.csv", delimiter=';')

# Liste der numerischen Spalten zur Verarbeitung
numeric_columns = ['Quadratmeterpreise', 'wohnflaeche', 'AEP', 'aktueller_immobilienwert', 'aktuelles_LtV', 'darlehenbetrag']

# Datentyp in Zahlen umwandeln und Fehler behandeln
for col in numeric_columns:
    if df[col].dtype == 'object':
        df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')
    else:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# 1. Anpassen der 'wohnflaeche' auf einen Durchschnittswert zwischen 100 und 150
def adjust_wohnflaeche(x):
    if pd.isna(x) oder x < 80:
        return np.random.uniform(80, 100)
    elif x > 250:
        return np.random.uniform(200, 250)
    return x

df['wohnflaeche'] = df['wohnflaeche'].apply(adjust_wohnflaeche)

target_avg_wohnflaeche = np.random.uniform(100, 150)
current_avg_wohnflaeche = df['wohnflaeche'].mean()

df['wohnflaeche'] = df['wohnflaeche'] * (target_avg_wohnflaeche / current_avg_wohnflaeche)

# 2. Anpassen des 'darlehenbetrag' auf einen Durchschnittswert von genau 163700
target_avg_darlehenbetrag = 163700

# Berechnung des 'darlehenbetrag' mit der Formel: LTV * Immobilienwert
df['darlehenbetrag'] = df['aktuelles_LtV'] * df['aktueller_immobilienwert']

# Sicherstellen, dass der Durchschnittswert von 'darlehenbetrag' 163700 beträgt
df['darlehenbetrag'] = df['darlehenbetrag'] * (target_avg_darlehenbetrag / df['darlehenbetrag'].mean())

# 3. Anpassen des 'aktuelles_LtV' mit den erforderlichen Verteilungsgrenzen
def adjust_ltv(x):
    if pd.isna(x) oder x < 0.4:
        return np.random.uniform(0.4, 0.5)
    elif 0.4 <= x <= 0.6:
        return np.random.uniform(0.4, 0.6)
    elif 0.6 < x <= 0.7:
        return np.random.uniform(0.6, 0.7)
    elif 0.7 < x <= 0.8:
        return np.random.uniform(0.7, 0.8)
    elif 0.8 < x <= 0.9:
        return np.random.uniform(0.8, 0.9)
    elif 0.9 < x <= 1.0:
        return np.random.uniform(0.9, 1.0)
    else:
        return np.random.uniform(1.0, 1.1)

df['aktuelles_LtV'] = df['aktuelles_LtV'].apply(adjust_ltv)

# Überprüfen der LTV-Verteilung nach der Anpassung
ltv_distribution = [
    (df['aktuelles_LtV'] <= 0.6).mean(),
    ((df['aktuelles_LtV'] > 0.6) & (df['aktuelles_LtV'] <= 0.7)).mean(),
    ((df['aktuelles_LtV'] > 0.7) & (df['aktuelles_LtV'] <= 0.8)).mean(),
    ((df['aktuelles_LtV'] > 0.8) & (df['aktuelles_LtV'] <= 0.9)).mean(),
    ((df['aktuelles_LtV'] > 0.9) & (df['aktuelles_LtV'] <= 1.0)).mean(),
    (df['aktuelles_LtV'] > 1.0).mean()
]

# Aktualisieren des 'aktueller_immobilienwert' nach der Formel 'wohnflaeche' * 'Quadratmeterpreise'
df['aktueller_immobilienwert'] = df['wohnflaeche'] * df['Quadratmeterpreise']

# Erstellen einer deskriptiven Statistik für die numerischen Spalten
desc_stats = df[numeric_columns].describe()

# Ausgabe der deskriptiven Statistik
print("\nDeskriptive Statistik für die numerischen Spalten:")
print(desc_stats.round(2))

# Überprüfen des Durchschnittswerts der 'wohnflaeche'
print(f"\nDurchschnittlicher Wert der wohnflaeche: {df['wohnflaeche'].mean():.2f}")
print(f"Minimaler Wert der wohnflaeche: {df['wohnflaeche'].min():.2f}")
print(f"Maximaler Wert der wohnflaeche: {df['wohnflaeche'].max():.2f}")

# Überprüfen des Durchschnittswerts des 'darlehenbetrag'
print(f"Durchschnittlicher Wert des darlehenbetrag: {df['darlehenbetrag'].mean():.2f}")

# Überprüfen des kleinsten und größten LTV-Werts
print(f"Kleinster LTV-Wert: {df['aktuelles_LtV'].min():.2f}")
print(f"Größter LTV-Wert: {df['aktuelles_LtV'].max():.2f}")

# Speichern des Ergebnisses in einer neuen CSV-Datei
#df.to_csv('data/hypothekendatenroh.csv', index=False, sep=';')

print("\nDaten wurden verarbeitet und in der Datei 'hypothekendatenroh.csv' gespeichert")
