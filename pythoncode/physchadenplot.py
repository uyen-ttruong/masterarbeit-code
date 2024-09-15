import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate

# Đọc dữ liệu từ file CSV
df = pd.read_csv('data/hypothekendaten_final_with_id.csv', delimiter=';')

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

# Convert columns to numeric
numeric_columns = ['aktuelles_LtV', 'darlehenbetrag', 'aktueller_immobilienwert', 'Schadensfaktor', 'AEP', 'Risikogewicht', 'Ueberschwemmungstiefe', 'Quadratmeterpreise', 'wohnflaeche']
for col in numeric_columns:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: flexible_numeric_conversion(x))

# Remove rows with NaN values
df = df.dropna(subset=[col for col in numeric_columns if col in df.columns])

# Function to determine Risikogewicht based on LtV
def get_risikogewicht(ltv):
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

# Function to calculate values
def calculate_values(row):
    E_j = row['aktueller_immobilienwert']
    schadenfaktor = row['Schadensfaktor']
    p_I_ij = row['AEP'] if 'AEP' in row.index else 0.01
    
    immobilienschaden = E_j * schadenfaktor
    EAI = immobilienschaden * p_I_ij
    new_immobilienwert = E_j - immobilienschaden
    new_LtV = row['darlehenbetrag'] / new_immobilienwert if new_immobilienwert > 0 else np.inf
    
    risikogewicht = get_risikogewicht(row['aktuelles_LtV'])
    neue_risikogewicht = get_risikogewicht(new_LtV)
    
    akt_RWA = row['darlehenbetrag'] * risikogewicht
    new_RWA = row['darlehenbetrag'] * neue_risikogewicht
    RWA_change = (new_RWA / akt_RWA) - 1 if akt_RWA > 0 else np.inf
    
    return pd.Series({
        'Immobilienschaden': immobilienschaden, 
        'EAI': EAI, 
        'Neuer Immobilienwert': new_immobilienwert, 
        'Neue LtV': new_LtV, 
        'Risikogewicht': risikogewicht,
        'Neue Risikogewicht': neue_risikogewicht, 
        'Akt. RWA': akt_RWA,
        'Neue RWA': new_RWA, 
        'RWA Änderung': RWA_change
    })

# Apply calculations to each row
results = df.apply(calculate_values, axis=1)

# Combine results with original DataFrame
df_results = pd.concat([df, results], axis=1)

# Filter data to keep only rows with non-zero Schadensfaktor
df_damage = df_results[df_results['Schadensfaktor'] != 0].copy()

# Function to calculate statistics
def calculate_stats(column):
    return {
        'mean': df_damage[column].mean(),
        'median': df_damage[column].median(),
        'min': df_damage[column].min(),
        'max': df_damage[column].max(),
        'std': df_damage[column].std()
    }

# Calculate statistics for relevant columns
columns_to_analyze = ['aktuelles_LtV', 'Neue LtV', 'aktueller_immobilienwert', 'Neuer Immobilienwert', 'Akt. RWA', 'Neue RWA', 'RWA Änderung']

stats = {col: calculate_stats(col) for col in columns_to_analyze}

# Print results
for col, col_stats in stats.items():
    print(f"\nStatistics for {col}:")
    for stat, value in col_stats.items():
        print(f"{stat}: {value:.4f}")

# Calculate percentage of cases where new values increased
ltv_increased = (df_damage['Neue LtV'] > df_damage['aktuelles_LtV']).mean() * 100
immobilienwert_decreased = (df_damage['Neuer Immobilienwert'] < df_damage['aktueller_immobilienwert']).mean() * 100
rwa_increased = (df_damage['RWA Änderung'] > 0).mean() * 100

print(f"\nPercentage of cases where LtV increased: {ltv_increased:.2f}%")
print(f"Percentage of cases where Immobilienwert decreased: {immobilienwert_decreased:.2f}%")
print(f"Percentage of cases where RWA increased: {rwa_increased:.2f}%")

print("\nTop 13 rows of relevant columns:")

# Select the relevant columns and sort by absolute RWA Änderung
table_data = df_damage[['ID', 'aktuelles_LtV', 'Neue LtV', 'Risikogewicht', 'Neue Risikogewicht', 'Akt. RWA', 'Neue RWA', 'RWA Änderung']].copy()
table_data['Abs RWA Änderung'] = table_data['RWA Änderung'].abs()
table_data = table_data.sort_values('Abs RWA Änderung', ascending=False).head(13)

# Format the data for better readability
table_data['aktuelles_LtV'] = table_data['aktuelles_LtV'].map(lambda x: f"{x:.2f}")
table_data['Neue LtV'] = table_data['Neue LtV'].map(lambda x: f"{x:.2f}")
table_data['Risikogewicht'] = table_data['Risikogewicht'].map(lambda x: f"{x:.2f}")
table_data['Neue Risikogewicht'] = table_data['Neue Risikogewicht'].map(lambda x: f"{x:.2f}")
table_data['Akt. RWA'] = table_data['Akt. RWA'].map(lambda x: f"{x:,.2f}")
table_data['Neue RWA'] = table_data['Neue RWA'].map(lambda x: f"{x:,.2f}")
table_data['RWA Änderung'] = table_data['RWA Änderung'].map(lambda x: f"{x:.2%}")

# Remove the temporary column used for sorting
table_data = table_data.drop('Abs RWA Änderung', axis=1)

# Create and print the table
table = tabulate(table_data, headers='keys', tablefmt='pipe', showindex=False)
print(table)

