import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point
from matplotlib.patches import Patch
from adjustText import adjust_text
from zipfile import ZipFile
import tempfile
import os

# Pfad zur Zip-Datei mit Hochwasserdaten
flood_zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\data\hochwasserereignisse_epsg4258_shp.zip"

# PLZ-Daten (Postleitzahl) aus Shapefile lesen
zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\data\plz-5stellig.shp.zip"
shp_name = 'plz-5stellig'
full_path = f"zip://{zip_path}!{shp_name}.shp"
plz_shape_df = gpd.read_file(full_path, dtype={'plz': str})

# Regionsdaten aus CSV lesen
plz_region_df = pd.read_csv('data/zuordnung_plz_ort.csv', sep=',', dtype={'plz': str})
plz_region_df.drop('osm_id', axis=1, inplace=True)

# Shapefile-Daten mit Regionsdaten zusammenführen
germany_df = pd.merge(left=plz_shape_df, right=plz_region_df, on='plz', how='inner')
germany_df.drop(['note'], axis=1, inplace=True)

# Daten für Bayern filtern
bayern_df = germany_df.query('bundesland == "Bayern"')

# Hochwasserdaten aus Zip-Datei lesen
with tempfile.TemporaryDirectory() as tmpdir:
    with ZipFile(flood_zip_path, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)
    shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
    if not shp_files:
        raise FileNotFoundError("Keine .shp-Datei im Zip gefunden")
    flood_data = gpd.read_file(os.path.join(tmpdir, shp_files[0]))

# Koordinatenreferenzsystem in EPSG:3035 umwandeln, bevor der Schwerpunkt berechnet wird
bayern_df = bayern_df.to_crs("EPSG:3035")
flood_data = flood_data.to_crs("EPSG:3035")

# Gesamtbevölkerung berechnen
total_population = bayern_df['einwohner'].sum()

# Berechnung der Anzahl der zu verteilenden Punkte pro Region basierend auf ihrer Bevölkerung
bayern_df['points'] = (bayern_df['einwohner'] / total_population * 3853).round().astype(int)

# Sicherstellen, dass die Gesamtanzahl der Punkte 3853 beträgt (aufgrund von Rundungen)
difference = 3853 - bayern_df['points'].sum()
if difference != 0:
    max_index = bayern_df['points'].idxmax()
    bayern_df.at[max_index, 'points'] += difference

# Zufällige Punkte in jeder Region generieren und in einem DataFrame speichern
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
points_gdf = gpd.GeoDataFrame(geometry=points)

# Daten in ein DataFrame umwandeln
points_df = pd.DataFrame(data)

# Karte mit und ohne Hochwasserdaten erstellen
for plot_with_flood in [True, False]:
    fig, ax = plt.subplots(figsize=(16, 11))

    # Bevölkerungskarte zeichnen
    population_bins = [0, 2000, 5000, 10000, 20000, 30000, 50000, 100000]
    population_labels = ['0-2000', '2001-5000', '5001-10000', '10001-20000', '20001-30000', '30001-50000', '50001+']
    bayern_df['pop_category'] = pd.cut(bayern_df['einwohner'], bins=population_bins, labels=population_labels)

    bayern_df.plot(
        ax=ax,
        column='pop_category',
        categorical=True,
        legend=False,
        cmap='summer',
        edgecolor='black',
        linewidth=0.2
    )

    # Verteilungspunkte auf der Karte zeichnen
    points_gdf.plot(ax=ax, marker='o', color='darkred', markersize=1, alpha=0.5)

    # Hochwasserdaten zeichnen, wenn plot_with_flood True ist
    if plot_with_flood:
        flood_data.plot(ax=ax, color='blue', alpha=0.5, edgecolor='darkblue', label='Überflutungsgebiete')

    # Zentren für jeden Ort zeichnen
    ort_centers = bayern_df[bayern_df['landkreis'].isna()].groupby('ort').agg({
        'geometry': lambda x: x.unary_union.centroid
    }).reset_index()

    ort_centers = ort_centers.set_geometry('geometry')

    ax.scatter(
        ort_centers.geometry.x,
        ort_centers.geometry.y,
        color='darkred',
        s=4,
        zorder=5
    )

    # Beschriftung der einzigartigen Orte ohne Landkreis
    texts = []
    for idx, row in ort_centers.iterrows():
        texts.append(ax.text(
            row.geometry.x + 0.005,
            row.geometry.y + 0.005,
            row['ort'],
            ha='center',
            va='center',
            fontsize=9,
            color='white',
            bbox=dict(facecolor='black', alpha=0.5, edgecolor='none', pad=1)
        ))

    # adjust_text verwenden, um Überlappungen zu vermeiden
    try:
        adjust_text(texts, arrowprops=dict(arrowstyle='->', color='darkred', lw=0.5))
    except MemoryError:
        print("MemoryError: Textanpassung nicht möglich. Reduzieren Sie die Anzahl der Beschriftungen oder vereinfachen Sie das Layout.")

    # Legende für Bevölkerungskategorien erstellen
    legend_handles = [
        Patch(color=plt.cm.summer(i / len(population_labels)), label=label)
        for i, label in enumerate(population_labels)
    ]
    ax.legend(handles=legend_handles, title='Einwohnerzahl nach PLZ', loc='lower right', fontsize=10, title_fontsize=12, bbox_to_anchor=(1.2, 0))

    # Achsen ausblenden und weißen Hintergrund setzen
    ax.axis('off')
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    plt.tight_layout()

    # Karte anzeigen
    plt.show()

# DataFrame der Verteilungspunkte als CSV speichern (optional)
#points_df.to_csv("bayern_points_distribution.csv", index=False)

# DataFrame anzeigen
#print(points_df.head())
