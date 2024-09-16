import pandas as pd
import numpy as np
from tabulate import tabulate
import matplotlib.pyplot as plt

print("Skript wird gestartet.")

# Daten
try:
    df = pd.read_csv('data/hypothekendaten_final_with_id.csv', delimiter=';')
    print("Daten erfolgreich geladen.")
except Exception as e:
    print(f"Fehler beim Laden der Daten: {e}")
    exit()

print(f"Anzahl der Zeilen im DataFrame: {len(df)}")
print(f"Spalten im DataFrame: {df.columns.tolist()}")

# Umwandlung der erforderlichen Spalten in numerische Typen
numeric_columns = ['wohnflaeche', 'aktueller_immobilienwert', 'darlehenbetrag', 'aktuelles_LtV']
for col in numeric_columns:
    if df[col].dtype == 'object':  # Prüfen, ob die Spalte vom Typ String (object) ist
        df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')
    else:
        df[col] = pd.to_numeric(df[col], errors='coerce')  # Für den Fall, dass die Spalte bereits numerisch ist, aber fehlerhafte Werte enthält

print("Spalten in numerische Typen umgewandelt.")

energieklassen = ['B', 'C', 'D', 'F', 'G', 'H']
df = df[df['Energieklasse'].isin(energieklassen)]

print(f"Anzahl der Zeilen nach Filterung nach Energieklasse: {len(df)}")

# Energieverbrauch für jede Klasse
energieverbrauch = {
    'B': 62.5, 'C': 87.5, 'D': 115, 'F': 180, 'G': 225, 'H': 275
}

# Spalte 'E_j' hinzufügen
df['E_j'] = df['Energieklasse'].map(energieverbrauch)

# Konstanten
E_Aplus = 30
r = 0.024
T = 30

# Energiepreise für verschiedene Szenarien
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

print("Beginn der Berechnungen für die Szenarien.")

# Ergebnisse für jedes Szenario
ergebnisse = {}
for szenario in energiepreise.keys():
    print(f"Verarbeite Szenario: {szenario}")
    szenario_ergebnisse = []
    
    for i, jahr in enumerate(jahre):
        print(f"  Verarbeite Jahr: {jahr}")
        PE_0 = energiepreise[szenario][0]
        PE_1 = energiepreise[szenario][i]

        # Anwendung der Berechnung auf jede Zeile
        df_result = df.apply(lambda zeile: neue_werte_berechnen(zeile, PE_0, PE_1), axis=1)

        # Berechnung der Durchschnittswerte nach Energieklasse
        durchschnittliche_ergebnisse = df_result.groupby(df['Energieklasse']).mean().rename(columns={
            'aktueller_immobilienwert': f'durchschnittlicher_aktueller_immobilienwert_{jahr}',
            'neuer_immobilienwert': f'durchschnittlicher_neuer_immobilienwert_{jahr}',
            'aktuelles_LtV': f'durchschnittliches_aktuelles_LtV_{jahr}',
            'neuer_beleihungsauslauf': f'durchschnittlicher_neuer_beleihungsauslauf_{jahr}',
            'wertänderung': f'durchschnittliche_wertänderung_{jahr}'
        })

        szenario_ergebnisse.append(durchschnittliche_ergebnisse)

    # Zusammenführung der Ergebnisse aller Jahre
    ergebnisse[szenario] = pd.concat(szenario_ergebnisse, axis=1)

print("Berechnungen abgeschlossen. Beginn der Ergebnisausgabe.")

# Ausgabe der Ergebnisse
for szenario, daten in ergebnisse.items():
    print(f"\nErgebnisse für das Szenario {szenario}:")
    print(daten.head())  # Überprüfung der Ergebnisdaten vor dem Speichern

    # Erstellung der Ergebnistabelle
    result_table = pd.DataFrame(index=energieklassen)
    
    for jahr in jahre:
        try:
            result_table[f'{jahr} Aktueller Wert'] = daten[f'durchschnittlicher_aktueller_immobilienwert_{jahr}'].round(2)
            result_table[f'{jahr} Neuer Wert'] = daten[f'durchschnittlicher_neuer_immobilienwert_{jahr}'].round(2)
            result_table[f'{jahr} Aktuelles LtV'] = daten[f'durchschnittliches_aktuelles_LtV_{jahr}'].round(4)
            result_table[f'{jahr} Neues LtV'] = daten[f'durchschnittlicher_neuer_beleihungsauslauf_{jahr}'].round(4)
            result_table[f'{jahr} Wertänderung'] = daten[f'durchschnittliche_wertänderung_{jahr}'].round(4)
        except KeyError as e:
            print(f"Fehler: Keine Daten für das Jahr {jahr} im Szenario {szenario} gefunden: {e}")
    
    #print("Ergebnistabelle wurde erstellt.")
    #print(result_table)  # Ausgabe des DataFrames

colors = {
    'B': 'red',
    'C': 'green',
    'D': 'blue',
    'F': 'orange',
    'G': 'purple',
    'H': 'brown'
}
plt.rcParams.update({'font.size': 11})

def plot_scenario(szenario, ergebnisse):
    plt.figure(figsize=(12, 8))

    # Schleife über die Energieklassen zum Zeichnen der Daten
    for klasse in energieklassen:
        # Prüfen, ob Daten für jede Klasse existieren
        if klasse in ergebnisse[szenario].index:
            color = colors[klasse]  # Farbe für die aktuelle Klasse

            # Nur neue Werte (neuer_immobilienwert) zeichnen
            plt.plot(jahre, ergebnisse[szenario].loc[klasse, [f'durchschnittlicher_neuer_immobilienwert_{jahr}' for jahr in jahre]] / 1000,
                     label=f'{klasse}', linestyle='-', marker='o', color=color)
        else:
            print(f"Keine Daten für Klasse {klasse} im Szenario {szenario}")

    # Diagrammparameter einstellen, Titel entfernen
    plt.xlabel('Jahr')
    plt.ylabel('Immobilienwert (in Tausend Euro)')
    plt.legend()
    plt.grid(True)

    # Diagramm anzeigen
    plt.show()

def plot_percentage_change(szenario, ergebnisse):
    plt.figure(figsize=(12, 8))

    for klasse in energieklassen:
        if klasse in ergebnisse[szenario].index:
            color = colors[klasse]
            
            # Berechnung der prozentualen Änderung
            wertänderung = [ergebnisse[szenario].loc[klasse, f'durchschnittliche_wertänderung_{jahr}'] for jahr in jahre]
            percentage_change = [change * 100 for change in wertänderung]  # Umrechnung in Prozent
            
            plt.plot(jahre, percentage_change, label=f'{klasse}', linestyle='-', marker='o', color=color)
        else:
            print(f"Keine Daten für Klasse {klasse} im Szenario {szenario}")

    plt.axhline(y=0, color='r', linestyle='--')  # 0%-Linie hinzufügen
    plt.xlabel('Jahr')
    plt.ylabel('Prozentuale Wertänderung (%)')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'{szenario}_percentage_change_plot.png')
    plt.close()

# Aufruf der Funktion zum Zeichnen des Diagramms für jedes Szenario
for szenario in energiepreise.keys():
    print(f"Erzeuge Diagramm für Szenario: {szenario}")
    plot_percentage_change(szenario, ergebnisse)