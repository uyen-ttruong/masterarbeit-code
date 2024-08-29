import pandas as pd
import geopandas as gpd
from shapely.wkt import loads
import numpy as np

# Step 1: Load the CSV file, treating the 'geometry' column as a single string value
df = pd.read_csv('data/highmediumriskgeo.csv', delimiter=';', dtype={'geometry': str}, low_memory=False)

# Clean and convert the geometry column
def safe_loads(wkt):
    try:
        if pd.isna(wkt) or wkt == '':
            return None
        return loads(str(wkt))
    except Exception as e:
        print(f"Error processing WKT: {wkt}")
        print(f"Error message: {str(e)}")
        return None

df['geometry'] = df['geometry'].apply(safe_loads)

# Remove rows with invalid geometry
df = df.dropna(subset=['geometry'])

# Convert the DataFrame to a GeoDataFrame
gdf = gpd.GeoDataFrame(df, geometry='geometry')

# Set the CRS to EPSG:3035
gdf.set_crs(epsg=3035, inplace=True)

# Save the GeoDataFrame to a Shapefile
try:
    gdf.to_file('highmediumriskgeo.shp')
    print("Conversion completed. Shapefile saved as 'flutbayern_AEP.shp'")
except Exception as e:
    print(f"Error saving Shapefile: {str(e)}")
    raise
