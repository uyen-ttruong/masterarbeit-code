import matplotlib.pyplot as plt
import numpy as np

# Daten
jahre = [2020, 2025, 2030, 2035, 2040, 2045, 2050]

net_zero = {
    'gas': [6.22, 6.59, 7.16, 7.66, 8.21, 9.25, 9.8],
    'öl': [14.97, 15.33, 15.77, 16.07, 16.54, 17.76, 17.65],
    'co2_steuer': [0, 25.2, 117.98, 230.48, 450.58, 933.36, 1320]
}

disorderly = {
    'gas': [6.22, 6.27, 6.16, 6.66, 6.97, 7.34, 7.99],
    'öl': [14.97, 14.99, 15.01, 15.6, 15.75, 15.44, 14.89],
    'co2_steuer': [0, 0, 0, 64.35, 165.33, 392.87, 984.33]
}

below_2 = {
    'gas': [6.22, 6.56, 6.77, 7, 7.23, 7.54, 7.94],
    'öl': [14.97, 15.29, 15.54, 15.75, 15.86, 15.88, 15.62],
    'co2_steuer': [0, 4.42, 53.29, 102.24, 173.77, 287.96, 485.69]
}

current_policies = {
    'gas': [6.22, 6.27, 6.16, 6.17, 6.3, 6.3, 6.35],
    'öl': [14.97, 14.99, 15.01, 15.13, 15.35, 15.55, 15.4],
    'co2_steuer': [0, 0, 0, 0, 0, 0, 0]
}
# Funktion zum Erstellen der Diagramme
def diagramm_erstellen(daten, titel, y_achse):
    plt.figure(figsize=(12, 6))
    plt.plot(jahre, net_zero[daten], label='Net Zero 2050', marker='o')
    plt.plot(jahre, disorderly[daten], label='Disorderly', marker='s')
    plt.plot(jahre, below_2[daten], label='Below 2°', marker='^')
    plt.plot(jahre, current_policies[daten], label='Current Policies', marker='D')
    plt.title(titel)
    plt.xlabel('Jahr')
    plt.ylabel(y_achse)
    plt.legend()
    plt.grid(True)
    plt.show()

# Diagramme erstellen
diagramm_erstellen('gas', 'Gaspreis nach NGFS Szenarien', 'Preis (USD pro Gigajoule)')
diagramm_erstellen('öl', 'Ölpreis nach NGFS Szenarien', 'Preis (USD pro Gigajoule)')
diagramm_erstellen('co2_steuer', 'CO2-Steuer nach NGFS Szenarien', 'Preis (USD pro Tonne)')