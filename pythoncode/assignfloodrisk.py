import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from zipfile import ZipFile
import tempfile
import os

# Pfad zur ZIP-Datei mit den Hochwasserdaten
flood_zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\data\hochwasserereignisse_epsg4258_shp.zip"

# Lesen der PLZ-Daten (Postleitzahl) aus der Shapefile
zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\data\plz-5stellig.shp.zip"
shp_name = 'plz-5stellig'
full_path = f"zip://{zip_path}!{shp_name}.shp"
plz_shape_df = gpd.read_file(full_path, dtype={'plz': str})

# Lesen der Regionsdaten aus der CSV-Datei
plz_region_df = pd.read_csv('data\zuordnung_plz_ort.csv', sep=',', dtype={'plz': str})
plz_region_df.drop('osm_id', axis=1, inplace=True)

# Zusammenführen der Shapefile-Daten mit den Regionsdaten
germany_df = pd.merge(left=plz_shape_df, right=plz_region_df, on='plz', how='inner')
germany_df.drop(['note'], axis=1, inplace=True)

# Daten für Bayern filtern
bayern_df = germany_df.query('bundesland == "Bayern"')

# Hochwasserdaten aus der ZIP-Datei lesen
with tempfile.TemporaryDirectory() as tmpdir:
    with ZipFile(flood_zip_path, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)
    shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
    if not shp_files:
        raise FileNotFoundError("Keine .shp-Datei in der ZIP gefunden")
    flood_data = gpd.read_file(os.path.join(tmpdir, shp_files[0]))

# Koordinatensystem in ein projiziertes System (EPSG:3035) umwandeln, bevor der Centroid berechnet wird
bayern_df = bayern_df.to_crs("EPSG:3035")
flood_data = flood_data.to_crs("EPSG:3035")

# Berechnung der Gesamtbevölkerung
total_population = bayern_df['einwohner'].sum()

# Berechnung der Anzahl der zu verteilenden Punkte basierend auf der Bevölkerungszahl jeder Region
bayern_df['points'] = (bayern_df['einwohner'] / total_population * 3853).round().astype(int)

# Sicherstellen, dass die Gesamtpunktzahl 3853 beträgt (aufgrund von Rundungen)
difference = 3853 - bayern_df['points'].sum()
if difference != 0:
    max_index = bayern_df['points'].idxmax()
    bayern_df.at[max_index, 'points'] += difference

# Funktion zur Bestimmung des Hochwasserrisikos (überarbeitet)
def determine_flood_risk(hq_value):
    if pd.isnull(hq_value):
        return 'very low'
    elif hq_value in ['HQ 20', 'HQ 30']:
        return 'high'
    elif hq_value in ['HQ 40', 'HQ 50', 'HQ 80']:
        return 'medium'
    elif hq_value in ['HQ 100', 'HQ 200']:
        return 'low'
    else:
        return 'very low'

# Erstellen von zufälligen Punkten in jeder Region und Erstellen eines DataFrames dafür
points = []
data = []
for idx, row in bayern_df.iterrows():
    num_points = row['points']
    polygon = row['geometry']
    minx, miny, maxx, maxy = polygon.bounds
    for _ in range(num_points):
        while True:
            random_point = Point(np.random.uniform(minx, maxx), np.random.uniform(miny, maxy))
            if polygon.contains(random_point):
                points.append(random_point)
                data.append({
                    'ort': row['ort'],
                    'landkreis': row['landkreis'],
                    'latitude': random_point.y,
                    'longitude': random_point.x
                })
                break

# Punkte in ein GeoDataFrame umwandeln
points_gdf = gpd.GeoDataFrame(data, geometry=points, crs="EPSG:3035")

# Hinzufügen der Spalte GEB_HQ zu points_gdf und Überprüfung, ob sich der Punkt im Hochwassergebiet befindet
points_gdf['GEB_HQ'] = None

for idx, point in points_gdf.iterrows():
    # Überprüfen, ob der Punkt in einem Hochwassergebiet liegt
    in_flood_area = flood_data[flood_data.contains(point.geometry)]
    if not in_flood_area.empty:
        # Wenn der Punkt in einem Hochwassergebiet liegt, wird der Wert GEB_HQ übernommen (einschließlich None)
        points_gdf.at[idx, 'GEB_HQ'] = in_flood_area.iloc[0]['GEB_HQ']

# Hinzufügen der Spalte flood_risk basierend auf dem Wert GEB_HQ
points_gdf['flood_risk'] = points_gdf['GEB_HQ'].apply(determine_flood_risk)

# Anzeige des DataFrames
print(points_gdf.head())
print(f"Anzahl der Punkte im Hochwassergebiet (einschließlich None): {points_gdf['GEB_HQ'].notnull().sum()}")
print(f"Gesamtanzahl der Punkte: {len(points_gdf)}")

# Auflisten der eindeutigen HQ-Werte
unique_hq_values = points_gdf['GEB_HQ'].unique()
print("\nEinzigartige HQ-Werte in points_gdf:")
for hq in sorted(unique_hq_values, key=lambda x: (x is None, x)):
    print(f"- {hq}")

# Zählen der Punkte für jeden HQ-Wert
hq_counts = points_gdf['GEB_HQ'].value_counts(dropna=False).sort_index()
print("\nAnzahl der Punkte für jeden HQ-Wert:")
for hq, count in hq_counts.items():
    if pd.isnull(hq):
        print(f"Kein HQ-Wert (None): {count}")
    else:
        print(f"HQ {hq}: {count}")

# Zählen der Punkte für jedes Hochwasserrisiko
risk_counts = points_gdf['flood_risk'].value_counts().sort_index()
print("\nAnzahl der Punkte für jedes Hochwasserrisiko:")
for risk, count in risk_counts.items():
    print(f"{risk.capitalize()}: {count}")

# Berechnung des Prozentsatzes der Punkte im Hochwassergebiet (einschließlich None)
percent_in_flood = (points_gdf['GEB_HQ'].notnull().sum() / len(points_gdf)) * 100
print(f"\nProzentsatz der Punkte im Hochwassergebiet (einschließlich None): {percent_in_flood:.2f}%")

# Berechnung des Prozentsatzes der Punkte für jedes Hochwasserrisiko
risk_percentages = (risk_counts / len(points_gdf) * 100).round(2)
print("\nProzentsatz der Punkte für jedes Hochwasserrisiko:")
for risk, percentage in risk_percentages.items():
    print(f"{risk.capitalize()}: {percentage:.2f}%")

# Speichern des DataFrames mit den verteilten Punkten als CSV-Datei (optional)
points_gdf.to_csv("bayern_points_distribution_with_flood_risk.csv", index=False)
