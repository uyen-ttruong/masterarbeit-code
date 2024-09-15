import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import locale

locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
# Daten laden
try:
    df = pd.read_csv('data/hypothekendaten_final_with_id.csv', delimiter=';')
    print("Daten erfolgreich geladen.")
except Exception as e:
    print(f"Fehler beim Laden der Daten: {e}")
    exit()

# Datenvorverarbeitung (wie zuvor)
numeric_columns = ['wohnflaeche', 'aktueller_immobilienwert', 'darlehenbetrag', 'aktuelles_LtV', 'Risikogewicht']
for col in numeric_columns:
    if col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.replace(',', '.')
        df[col] = pd.to_numeric(df[col], errors='coerce')

energieklassen = ['B', 'C', 'D', 'F', 'G', 'H']
df = df[df['Energieklasse'].isin(energieklassen)]

# Energieverbrauch für jede Klasse
energieverbrauch = {
    'B': 62.5, 'C': 87.5, 'D': 115, 'F': 180, 'G': 225, 'H': 275
}
df['E_j'] = df['Energieklasse'].map(energieverbrauch)

# Konstanten
E_Aplus = 30
r = 0.024
T = 30

# Energiepreise für verschiedene Szenarien (2020 bis 2050)
energiepreise = {
    'Netto-Null': {2020: 0.0623, 2050: 0.3389},
    'Ungeordnet': {2020: 0.0581, 2050: 0.2593},
    'Unter 2°C': {2020: 0.0598, 2050: 0.1622},
    'Aktuelle Richtlinien': {2020: 0.0581, 2050: 0.0594}
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

# Funktion zur Berechnung neuer Werte für ein bestimmtes Jahr
def neue_werte_berechnen(zeile, PE_0, PE_t, jahr):
    try:
        E_j = float(zeile['E_j'])
        wohnflaeche = float(zeile['wohnflaeche'])
        aktueller_immobilienwert = float(zeile['aktueller_immobilienwert'])
        darlehenbetrag = float(zeile['darlehenbetrag'])
        old_RWA = darlehenbetrag * float(zeile.get('Risikogewicht', 0))

        delta_EC_rel = (E_j - E_Aplus) * (PE_t - PE_0) * wohnflaeche
        delta_P = -delta_EC_rel * ((1 - (1 + r)**-(2050-jahr)) / r)
        neuer_immobilienwert = aktueller_immobilienwert + delta_P
        neuer_beleihungsauslauf = darlehenbetrag / neuer_immobilienwert
        
        neue_risikogewicht = get_neue_risikogewicht(neuer_beleihungsauslauf)
        new_RWA = darlehenbetrag * neue_risikogewicht
        
        return pd.Series({
            'Energieklasse': zeile['Energieklasse'],
            'new_RWA': new_RWA
        })
    except Exception as e:
        print(f"Fehler in neue_werte_berechnen: {e}")
        return pd.Series({
            'Energieklasse': np.nan,
            'new_RWA': np.nan
        })

print("Beginne mit der Berechnung für die Szenarien von 2020 bis 2050.")

# Ergebnisse für jedes Szenario
all_scenarios_rwa = {}

for szenario, preise in energiepreise.items():
    print(f"\nVerarbeite Szenario: {szenario}")
    
    PE_0 = preise[2020]
    PE_2050 = preise[2050]
    
    gesamt_rwa_jaehrlich = {}
    
    for jahr in range(2020, 2051):
        PE_t = PE_0 + (PE_2050 - PE_0) * (jahr - 2020) / (2050 - 2020)
        
        # Anwendung der Berechnung auf jede Zeile
        df_result = df.apply(lambda zeile: neue_werte_berechnen(zeile, PE_0, PE_t, jahr), axis=1)
        
        # Berechnung des Gesamt-RWA für das aktuelle Jahr
        gesamt_rwa = df_result['new_RWA'].sum()
        gesamt_rwa_jaehrlich[jahr] = gesamt_rwa
    
    # Ausgabe der jährlichen Gesamt-RWA-Werte
    print(f"\nJährliche Gesamt-RWA-Werte für Szenario {szenario}:")
    for jahr, rwa in gesamt_rwa_jaehrlich.items():
        print(f"{jahr}: {rwa:,.2f}")
    
    all_scenarios_rwa[szenario] = gesamt_rwa_jaehrlich


print("\nBerechnung abgeschlossen. Erstelle Plot...")

print("\nBerechnung abgeschlossen. Erstelle Plot...")

# Erstellen des Plots mit angepassten Einstellungen
plt.figure(figsize=(16, 10))  # Noch größere Abbildung

for szenario, rwa_values in all_scenarios_rwa.items():
    years = list(rwa_values.keys())
    rwa = [value / 1000 for value in rwa_values.values()]  # Umrechnung in Tausend Euro
    plt.plot(years, rwa, label=szenario, linewidth=3)  # Noch dickere Linien

plt.xlabel('Jahr', fontsize=24)  # Noch größere Schrift für x-Achsen-Beschriftung
plt.ylabel('Gesamt RWA (Tausend €)', fontsize=24)  # Noch größere Schrift für y-Achsen-Beschriftung

plt.legend(fontsize=20, loc='upper left')  # Noch größere Schrift in der Legende
plt.grid(True)

# Noch größere Schrift für Achsenbeschriftungen
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)

# Anpassen der y-Achse für bessere Lesbarkeit mit Punkt als Tausendertrennzeichen
def format_func(value, tick_number):
    return locale.format_string('%.0f', value, grouping=True)

plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(format_func))

# Vergrößern der Werte auf den Achsen
plt.tick_params(axis='both', which='major', labelsize=18)

# Anpassen der x-Achse für bessere Lesbarkeit
plt.xticks(range(2020, 2051, 5))  # Zeige nur alle 5 Jahre an

# Speichern des Plots
plt.tight_layout()  # Optimiert das Layout
plt.savefig('gesamt_rwa_plot.png', dpi=300, bbox_inches='tight')  # Höhere Auflösung und enger Rahmen
print("Plot wurde als 'gesamt_rwa_plot.png' gespeichert.")

plt.close()

print("\nBerechnung und Erstellung des Plots abgeschlossen.")