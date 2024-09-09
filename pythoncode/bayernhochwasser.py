import geopandas as gpd
import pandas as pd
from zipfile import ZipFile
import os
import tempfile

# Pfad zur Zip-Datei
zip_path = r"C:\Users\uyen truong\Downloads\hochwasserereignisse_epsg4258_shp (3).zip"

# Temporäres Verzeichnis erstellen, um die Datei zu entpacken
with tempfile.TemporaryDirectory() as tmpdir:
    with ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)
    
    # Die .shp-Datei im temporären Verzeichnis suchen
    shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
    
    if not shp_files:
        raise FileNotFoundError("Keine .shp-Datei im Zip gefunden")
    
    # Die erste Shapefile-Datei lesen (angenommen, es handelt sich um die Datei mit den Hochwasserdaten)
    shapefile_path = os.path.join(tmpdir, shp_files[0])
    gdf = gpd.read_file(shapefile_path)
    unique_geb_hq = gdf['GEB_HQ'].unique()

# Alle Spaltennamen ausgeben
for col in gdf.columns:
        print(col)
        
# Einzigartige Werte in der Spalte GEB_HQ ausgeben
print("Einzigartige Werte in der Spalte GEB_HQ:")
for value in unique_geb_hq:
    print(value)
    
    # GeoDataFrame in DataFrame umwandeln und die Spalte 'geometry' entfernen
    #df = pd.DataFrame(gdf.drop(columns='geometry'))
    
    # Pfad zur CSV-Ausgabedatei
    #csv_output_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\UeFlaecheEreignis_epsg4258.csv"
    
    # DataFrame als CSV speichern
    #df.to_csv(csv_output_path, index=False)

#print(f"Daten wurden konvertiert und gespeichert unter: {csv_output_path}")
