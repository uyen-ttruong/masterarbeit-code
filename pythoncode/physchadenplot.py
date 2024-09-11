import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def csv_datei_lesen(dateipfad):
    try:
        df = pd.read_csv(dateipfad)
    except pd.errors.ParserError:
        try:
            df = pd.read_csv(dateipfad, sep=';')
        except pd.errors.ParserError:
            df = pd.read_csv(dateipfad, error_bad_lines=False, warn_bad_lines=True)
    return df

def hochwasserrisiko_analysieren(df):
    hochwasserrisiko_zaehlung = df['flood_risk'].value_counts()
    
    print("\nAnalyse des Hochwasserrisikos:")
    for risiko, anzahl in hochwasserrisiko_zaehlung.items():
        print(f"   Anzahl flood_risk = {risiko}: {anzahl}")
    
    return hochwasserrisiko_zaehlung

def hochwasserrisiko_plotten(hochwasserrisiko_zaehlung):
    # Sortiere die Daten in der gewünschten Reihenfolge
    sortierte_daten = hochwasserrisiko_zaehlung.reindex(['high', 'medium', 'low', 'very low'])
    
    plt.figure(figsize=(12, 8))
    
    # Erstelle einen Balkendiagramm mit logarithmischer y-Achse
    ax = sortierte_daten.plot(kind='bar', log=True, color=['red', 'orange', 'yellow', 'green'], edgecolor='black')
    
    plt.title('Verteilung des Hochwasserrisikos im Hypothekenportfolio', fontsize=16)
    plt.xlabel('Risikostufen', fontsize=14)
    plt.ylabel('Anzahl', fontsize=14)
    plt.xticks(rotation=0, fontsize=12)
    
    # Setze die y-Achse auf einen minimalen Wert von 1 (10^0)
    plt.ylim(bottom=1, top=sortierte_daten.max()*1.1)
    
    # Anpassen der y-Achsen-Beschriftungen
    y_ticks = [1, 10, 100, 1000, 10000]
    plt.yticks(y_ticks, [f'{y:,}' for y in y_ticks], fontsize=12)
    
    # Füge Werte über den Balken hinzu
    for i, v in enumerate(sortierte_daten):
        ax.text(i, v, f'{v:,}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Füge ein Gitternetz hinzu
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('hochwasserrisiko_verteilung_optimiert.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    dateipfad = 'data/hypothekendaten4.csv'
    
    try:
        df = csv_datei_lesen(dateipfad)
        hochwasserrisiko_zaehlung = hochwasserrisiko_analysieren(df)
        hochwasserrisiko_plotten(hochwasserrisiko_zaehlung)
        print("\nDas optimierte Diagramm der Hochwasserrisikoverteilung wurde unter dem Namen 'hochwasserrisiko_verteilung_optimiert.png' gespeichert.")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {str(e)}")

if __name__ == "__main__":
    main()