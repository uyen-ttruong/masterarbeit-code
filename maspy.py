import pandas as pd
import numpy as np
from scipy.stats import lognorm

# Funktionen für die Generierung von Daten
def generate_price(mean, min_price, max_price, size):
    shape, loc, scale = lognorm.fit([min_price, mean, max_price], floc=0)
    return np.clip(lognorm.rvs(shape, loc=loc, scale=scale, size=size), min_price, max_price)

def generate_area(mean, std, size):
    return np.clip(np.random.normal(mean, std, size), 20, 500)

def generate_build_year():
    ranges = [(1900, 1950), (1950, 1980), (1980, 2000), (2000, 2016), (2016, 2023)]
    weights = [0.10, 0.20, 0.30, 0.25, 0.15]
    range_index = np.random.choice(len(ranges), p=weights)
    return np.random.randint(*ranges[range_index])

def generate_energy_class(build_year):
    classes = ['A+', 'A', 'B', 'C', 'D', 'E', 'F', 'G']
    weights = [0.05, 0.10, 0.15, 0.25, 0.20, 0.15, 0.07, 0.03]
    base_class = np.random.choice(classes, p=weights)
    
    # Adjusting for build year
    if build_year >= 2016:
        return np.random.choice(['A+', 'A', 'B'], p=[0.4, 0.4, 0.2])
    elif build_year >= 2000:
        return np.random.choice(['A', 'B', 'C'], p=[0.3, 0.4, 0.3])
    else:
        return base_class

# Hauptfunktion zur Erstellung des Portfolios
def create_portfolio(size=10000):
    portfolio = pd.DataFrame()

    # Immobilientyp
    portfolio['type'] = np.random.choice(['Wohnung', 'Haus'], size=size, p=[0.7, 0.3])

    # Preis pro Quadratmeter
    portfolio.loc[portfolio['type'] == 'Wohnung', 'price_per_sqm'] = generate_price(3433, 768, 18008, sum(portfolio['type'] == 'Wohnung'))
    portfolio.loc[portfolio['type'] == 'Haus', 'price_per_sqm'] = generate_price(3723, 1320, 19009, sum(portfolio['type'] == 'Haus'))

    # Wohnfläche
    portfolio.loc[portfolio['type'] == 'Wohnung', 'area'] = generate_area(75, 25, sum(portfolio['type'] == 'Wohnung'))
    portfolio.loc[portfolio['type'] == 'Haus', 'area'] = generate_area(150, 50, sum(portfolio['type'] == 'Haus'))

    # Gesamtpreis
    portfolio['total_price'] = portfolio['price_per_sqm'] * portfolio['area']

    # Baujahr
    portfolio['build_year'] = [generate_build_year() for _ in range(size)]

    # Energieeffizienzklasse
    portfolio['energy_class'] = [generate_energy_class(year) for year in portfolio['build_year']]

    # Kreditinformationen
    portfolio['ltv'] = np.random.normal(0.55, 0.1, size).clip(0.2, 0.8)
    portfolio['interest_rate'] = np.random.normal(0.025, 0.005, size).clip(0.01, 0.05)
    portfolio['loan_term'] = np.random.randint(10, 31, size)

    # Zusätzliche Attribute
    portfolio['rented'] = np.random.choice([True, False], size=size)
    portfolio['rooms'] = np.random.randint(1, 7, size)
    portfolio['has_balcony'] = np.random.choice([True, False], size=size)
    portfolio['has_parking'] = np.random.choice([True, False], size=size)

    return portfolio

# Portfolio erstellen
portfolio = create_portfolio()

# Erste paar Zeilen anzeigen
print(portfolio.head())

# Grundlegende statistische Informationen
print(portfolio.describe())

# Portfolio in CSV-Datei speichern
#portfolio.to_csv('bayern_immobilien_portfolio.csv', index=False)