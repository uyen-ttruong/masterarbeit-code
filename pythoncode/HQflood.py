import geopandas as gpd
import pandas as pd

# Shapefile lesen
gdf = gpd.read_file("data/highmediumriskgeo.shp")

# Aktuelles Koordinatensystem ausgeben
print(f"Aktuelles Koordinatensystem: {gdf.crs}")

# Koordinatensystem in EPSG:3035 umwandeln
gdf = gdf.to_crs("EPSG:3035")

# Liste zum Speichern der Daten erstellen
data = []

# Durch jede Zeile im GeoDataFrame iterieren
for idx, row in gdf.iterrows():
    # Geometrie abrufen
    geom = row['geometry']
    
    # Kopie der Zeilendaten erstellen, Spalte 'geometry' entfernen
    row_data = row.drop('geometry').to_dict()
    
    # Geometrietyp prüfen
    if geom.geom_type == 'Polygon':
        # Wenn es sich um ein Polygon handelt, Koordinaten der Punkte abrufen
        for point in geom.exterior.coords:
            point_data = row_data.copy()
            point_data['longitude'] = point[0]
            point_data['latitude'] = point[1]
            data.append(point_data)
    elif geom.geom_type == 'MultiPolygon':
        # Wenn es sich um ein MultiPolygon handelt, durch jedes Polygon iterieren
        for polygon in geom.geoms:
            for point in polygon.exterior.coords:
                point_data = row_data.copy()
                point_data['longitude'] = point[0]
                point_data['latitude'] = point[1]
                data.append(point_data)

# DataFrame aus der Datenliste erstellen
df = pd.DataFrame(data)

# DataFrame als CSV-Datei speichern
#output_file = "highmediumriskgeo_all_columns_latlon_epsg3035.csv"
#df.to_csv(output_file, index=False)

#print(f"Daten wurden in der Datei '{output_file}' gespeichert")

# Erste fünf Zeilen des DataFrames anzeigen
print("\nDie ersten fünf Zeilen der Daten:")
print(df.head())

# Informationen zu den Spalten anzeigen
print("\nInformationen zu den Spalten:")
print(df.info())
