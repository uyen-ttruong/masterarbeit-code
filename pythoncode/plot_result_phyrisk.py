import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Lesen der Daten aus der CSV-Datei
df = pd.read_csv('data\hypothekendaten_final_with_statistics.csv', delimiter=';')

# Spaltennamen der Daten anzeigen
print("Die Spalten in den Daten:")
print(df.columns)
print(df.describe().to_string())

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

# Umwandlung der Spalten in numerische Werte
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
results = df.apply(calculate_values, axis=1)

# Zusammenfügen der Ergebnisse mit dem ursprünglichen DataFrame
df_results = pd.concat([df, results], axis=1)

# Filtern der Daten, um nur die Zeilen zu behalten, bei denen der Schadensfaktor ungleich 0 ist
df_damage = df_results[df_results['Schadensfaktor'] != 0].copy()

def format_euro(x, p):
    return f"{x:,.0f} €".replace(",", ".")
print(df_damage['Immobilienschaden'].describe())

# Diagramm zeichnen
def format_euro(x, p):
    return f"{x:,.0f} €".replace(",", ".")

# Verteilung des Immobilienschadens
plt.figure(figsize=(16, 8))
sns.histplot(df_damage['Immobilienschaden'], kde=True, bins=20, color='skyblue')

# Durchschnitts- und Medianwerte formatieren
mean_value = df_damage['Immobilienschaden'].mean()
median_value = df_damage['Immobilienschaden'].median()

plt.axvline(mean_value, color='red', linestyle='--', label=f'Mean: {mean_value:,.2f} €'.replace(",", "."))
plt.axvline(median_value, color='green', linestyle='-.', label=f'Median: {median_value:,.2f} €'.replace(",", "."))

plt.legend()
plt.title('Verteilung des Immobilienschadens')
plt.xlabel('Immobilienschaden (in Euro)', labelpad=10)
plt.ylabel('Häufigkeit')

# X-Achse formatieren
plt.gca().xaxis.set_major_formatter(FuncFormatter(format_euro))

plt.grid(True)
plt.xticks(rotation=45, ha='right')
plt.gca().xaxis.set_major_locator(plt.MaxNLocator(10))  # Begrenzung der X-Achsen-Tick-Limits

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()

# Vergleich zwischen altem und neuem RWA mit Verbindungslinien der Balkenspitzen
plt.figure(figsize=(16, 8))

# Balkendiagramm für altes RWA
bar_width = 0.4
index = np.arange(len(df_damage))

plt.bar(index, df_damage['darlehenbetrag'] * df_damage['Risikogewicht'], 
        bar_width, label='Altes RWA', color='blue')

# Balkendiagramm für neues RWA mit Verschiebung
plt.bar(index + bar_width, df_damage['Neue RWA'], 
        bar_width, label='Neues RWA', color='orange')

# Verbindungslinien der Balkenspitzen zeichnen
plt.plot(index + bar_width / 2, df_damage['darlehenbetrag'] * df_damage['Risikogewicht'], 
         '-o', color='blue', markersize=5, label='Linie altes RWA')
plt.plot(index + bar_width / 2, df_damage['Neue RWA'], 
         '-o', color='orange', markersize=5, label='Linie neues RWA')

# X-Achsenbeschriftungen
plt.xticks(index + bar_width / 2, df_damage.index, rotation=45, ha='right')

# Titel und Achsenbeschriftungen
plt.title('Vergleich zwischen altem und neuem RWA')
plt.xlabel('Immobilien ID', labelpad=10)
plt.ylabel('RWA (in Euro)', labelpad=10)

# Y-Achse im Euro-Format
plt.gca().yaxis.set_major_formatter(FuncFormatter(format_euro))

# Legende und Raster
plt.legend()
plt.grid(True, axis='y')

# Layout-Anpassung
plt.tight_layout()

# Diagramm anzeigen
plt.show()
