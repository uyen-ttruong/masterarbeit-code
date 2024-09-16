import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Daten von CSV-Datei lesen
df = pd.read_csv('data/hypothekendaten_final_with_statistics.csv', delimiter=';')

# # Zähle die Anzahl in der Spalte 'flood_risk'
# flood_risk_counts = df['flood_risk'].value_counts().sort_index()

# # Farben für jede Risikostufe
# colors = ['red', 'orange', 'yellow', 'green']

# # Erstelle das Diagramm
# plt.figure(figsize=(10, 6))
# bars = plt.bar(flood_risk_counts.index, flood_risk_counts.values, color=colors)

# # Zeige Zahlen über jeder Säule an
# for bar in bars:
#     height = bar.get_height()
#     plt.text(bar.get_x() + bar.get_width() / 2, height, f'{int(height):,}', ha='center', va='bottom', fontsize=12, fontweight='bold')

# # Setze Beschriftungen für x- und y-Achse mit Schriftgröße 12
# plt.xlabel('Risikostufen', fontsize=12)
# plt.ylabel('Anzahl', fontsize=12)

# # Setze logarithmische Skala für y-Achse, um große Unterschiede zwischen den Säulen besser darzustellen
# plt.yscale('log')

# # Setze Schriftgröße für Achsenwerte
# plt.xticks(fontsize=12)
# plt.yticks(fontsize=12)

# # Zeige das Diagramm an
# plt.tight_layout()
# plt.show()

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

# #Kreisdiagramm plotten
# # Berechne den Gesamtschaden für jede Immobilie: immobilienschaden = immobillienwert * schadenfaktor
# df_damage['total_schadensfaktor_value'] = df_damage['aktueller_immobilienwert'] * df_damage['Schadensfaktor']

# # Gesamtwert des Schadens durch Schadensfaktor
# total_schadensfaktor_value = df_damage['total_schadensfaktor_value'].sum()
# total_immobilienwert = df_damage['aktueller_immobilienwert'].sum()
# print(total_schadensfaktor_value)
# print(total_immobilienwert)
# print(df_results['aktueller_immobilienwert'].sum())

# # Erstelle ein Kreisdiagramm für den Gesamtschaden basierend auf aktuellem Immobilienwert und Schadenwert
# plt.figure(figsize=(8, 8))

# # Erstelle Daten für das Diagramm
# labels = ['Gesamtschadenwert', '']
# sizes = [total_schadensfaktor_value, total_immobilienwert - total_schadensfaktor_value]
# colors = ['#E9C46A', '#2A9D8F']  # Tausche die Positionen von Gelb und Grün

# # Erstelle das Diagramm mit dickem Rand und angepasstem Abstand für Label und Prozentsätze
# wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
#                                    startangle=140, wedgeprops=dict(edgecolor='black', linewidth=2),
#                                    pctdistance=0.85, labeldistance=1.1)

# # Setze Schriftart und -größe
# for text in texts + autotexts:
#     text.set_fontsize(12)

# # Zeige das Diagramm
# plt.axis('equal')
# plt.tight_layout()
# plt.show()

# # Berechne den Gesamtschaden in einem Jahr (EAI wurde basierend auf Schadensfaktor berechnet)
# total_schaden_pro_jahr = df_damage['EAI'].sum()

# # Erstelle ein Kreisdiagramm für den Gesamtschaden basierend auf EAI in einem Jahr
# plt.figure(figsize=(8, 8))

# # Erstelle Daten für das Diagramm
# labels = ['Gesamtschadenwert (1 Jahr)', '']
# sizes = [total_schaden_pro_jahr, total_immobilienwert - total_schaden_pro_jahr]
# colors = ['#E9C46A', '#2A9D8F']  # Verwende die gleichen Farben wie im ersten Diagramm

# # Erstelle das Diagramm mit dickem Rand und angepasstem Abstand für Label und Prozentsätze
# wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
#                                    startangle=140, wedgeprops=dict(edgecolor='black', linewidth=2),
#                                    pctdistance=1.1, labeldistance=1.5)

# # Setze Schriftart und -größe
# for text in texts + autotexts:
#     text.set_fontsize(12)

# # Zeige das Diagramm
# plt.axis('equal')
# plt.tight_layout()
# plt.show()

# # Formatierungsfunktion für Euro
# def format_euro(x, p):
#     return f"{x:,.0f} €".replace(",", ".")

# # Plot 1: Verteilung des Immobilienschadens
# def format_euro(x, pos):
#     """ Formatiere Zahl als Euro mit Punkt als Tausendertrennzeichen und €-Symbol"""
#     return f"{x:,.0f} €".replace(",", ".")

# plt.figure(figsize=(16, 8))
# sns.histplot(df_damage['Immobilienschaden'], kde=True, bins=20, color='skyblue')

# mean_value = df_damage['Immobilienschaden'].mean()
# median_value = df_damage['Immobilienschaden'].median()

# # Zeichne Linien für Mittelwert und Median mit leuchtenden Farben
# plt.axvline(mean_value, color='green', linestyle='--', label=f'Mittelwert: {mean_value:,.2f} €'.replace(",", "."))
# plt.axvline(median_value, color='red', linestyle='-.', label=f'Median: {median_value:,.2f} €'.replace(",", "."))

# # Zeige Legende an
# plt.legend(fontsize=12)

# # Setze Beschriftungen für x- und y-Achse mit Schriftgröße 12
# plt.xlabel('Immobilienschaden (in Euro)', fontsize=12, labelpad=10)
# plt.ylabel('Häufigkeit', fontsize=12)

# # Formatiere x-Achse als Euro
# plt.gca().xaxis.set_major_formatter(FuncFormatter(format_euro))

# # Zeige Gitter und passe x-Achsenbeschriftungen an
# plt.grid(True)
# plt.xticks(rotation=45, ha='right', fontsize=12)
# plt.yticks(fontsize=12)
# plt.gca().xaxis.set_major_locator(plt.MaxNLocator(10))

# # Optimiere Layout
# plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# # Zeige das Diagramm
# plt.show()

# # Plot 2: Vergleich von RWA
# plt.figure(figsize=(16, 8))

# bar_width = 0.4
# index = np.arange(len(df_damage))

# plt.bar(index, df_damage['darlehenbetrag'] * df_damage['Risikogewicht'], bar_width, label='Altes RWA', color='#6495ED')
# plt.bar(index + bar_width, df_damage['Neue RWA'], bar_width, label='Neues RWA', color='#FFB6C1')

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
# # Daten sortiert nach 'Neue LtV' von niedrig zu hoch
# df_damage_sorted = df_damage.sort_values(by='Neue LtV')

# # Erstelle Balkendiagramm zum Vergleich von altem und neuem LtV
# plt.figure(figsize=(16, 8))

# bar_width = 0.4
# index = np.arange(len(df_damage_sorted))

# # Zeichne Balken für alten LtV
# plt.bar(index, df_damage_sorted['aktuelles_LtV'], bar_width, label='Aktueller LtV', color='lightblue')

# # Zeichne Balken für neuen LtV mit Versatz
# plt.bar(index + bar_width, df_damage_sorted['Neue LtV'], bar_width, label='Neuer LtV', color='darkblue')

# # Benenne die Balken mit Immobilien ID basierend auf der ID-Spalte und sortiere entsprechend
# plt.xticks(index + bar_width / 2, [f'ID: {id_}' for id_ in df_damage_sorted['ID']], rotation=45, ha='right')

# # Füge Titel und Beschriftungen hinzu
# plt.xlabel('Immobilien ID', labelpad=10)
# plt.ylabel('LtV (%)', labelpad=10)

# # Formatiere y-Achse als Prozentsatz
# plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.0%}'))

# # Füge Legende und Gitter hinzu
# plt.legend()
# plt.grid(True, axis='y')

# # Optimiere Layout
# plt.tight_layout()

# # Zeige das Diagramm
# #plt.show()