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

# Funktion zur Berechnung des Endenergie-Preises
def endenergie_preis_berechnen(ölpreis, gaspreis, co2_steuer, wechselkurs):
    kO = 0.287  # kg CO2/kWh für Öl (κ^O)
    kG = 0.238  # kg CO2/kWh für Gas (κ^G)
    gamma = 1700  # kWh/BOE (γ)
    omega_O = 0.35  # Gewichtung für Öl (ω^O)
    tau = 0.19  # Mehrwert- und Energiesteuer (τ_t)

    # Berechnung der Komponenten nach der gegebenen Formel:
    PO_t = (kO * co2_steuer / 1000) + (ölpreis / (wechselkurs * gamma))  # P^O_t
    PG_t = (kG * co2_steuer / 1000) + (gaspreis / (wechselkurs * gamma))  # P^G_t
    
    P_t = (1 + tau) * (omega_O * PO_t + (1 - omega_O) * PG_t)  # Endpreis P_t
    
    return P_t

# Angenommener Wechselkurs (USD/EUR)
wechselkurs = 0.65

# Berechnung der Endenergie-Preise
endpreise = {szenario: [] for szenario in ['net_zero', 'disorderly', 'below_2', 'current_policies']}

for szenario in endpreise.keys():
    for jahr in range(len(jahre)):
        ölpreis = eval(f"{szenario}['öl'][{jahr}]") * 5.8  # Umrechnung von GJ auf BOE
        gaspreis = eval(f"{szenario}['gas'][{jahr}]") * 5.8  # Umrechnung von GJ auf BOE
        co2_steuer = eval(f"{szenario}['co2_steuer'][{jahr}]") * wechselkurs
        
        preis = endenergie_preis_berechnen(ölpreis, gaspreis, co2_steuer, wechselkurs)
        endpreise[szenario].append(preis)

#print(endpreise)
# Diagramm erstellen
plt.figure(figsize=(10, 6))
plt.plot(jahre, endpreise['current_policies'], label='Current policies', color='blue', linewidth=2)
plt.plot(jahre, endpreise['below_2'], label='2 Degrees', color='red', linestyle='--', linewidth=2)
plt.plot(jahre, endpreise['disorderly'], label='Disorderly', color='black', linestyle='-.', linewidth=2)
plt.plot(jahre, endpreise['net_zero'], label='Net Zero', color='blue', linestyle=':', linewidth=2)

# Xóa tiêu đề biểu đồ, điều chỉnh kích thước phông chữ và thêm lưới
plt.xlabel('Jahr', fontsize=12)
plt.ylabel('Euro/kWh', fontsize=12)
plt.legend(fontsize=12)
plt.grid(True, linestyle=':', alpha=0.7)
plt.ylim(0, max(max(preise) for preise in endpreise.values()) * 1.1)  # Anpassung der y-Achse

# Điều chỉnh phông chữ cho các giá trị trên trục
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

plt.show()

# # Werte ausgeben
# szenarien = ['Current policies', '2 Degrees', 'Disorderly', 'Net Zero']
# for i, szenario in enumerate(['current_policies', 'below_2', 'disorderly', 'net_zero']):
#     print(f"\n{szenarien[i]}:")
#     for j, jahr in enumerate(jahre):
#         print(f"{jahr}: {endpreise[szenario][j]:.3f}")
