import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
import matplotlib.pyplot as plt

# Load the shapefile
zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\plz-5stellig.shp.zip"
shp_name = 'plz-5stellig'
full_path = f"zip://{zip_path}!{shp_name}.shp"
plz_shape_df = gpd.read_file(full_path, dtype={'plz': str})
plt.rcParams['figure.figsize'] = [16, 11] 

# Load the regional data
plz_region_df = pd.read_csv('zuordnung_plz_ort.csv', sep=',', dtype={'plz': str})

# Prepare the data by merging the shapefile and population data
plz_region_df.drop('osm_id', axis=1, inplace=True)
germany_df = pd.merge(left=plz_shape_df, right=plz_region_df, on='plz', how='inner')
germany_df.drop(['note'], axis=1, inplace=True)

# Filter for Bayern
bayern_df = germany_df.query('bundesland == "Bayern"')

# Load the Shapefile back into a GeoDataFrame
bayern_df = gpd.read_file("flutbayern_shapefile_test.shp")

# Adjust CRS to reduce distortion
bayern_df = bayern_df.to_crs("EPSG:3035") 

# Calculate the total population
total_population = bayern_df['einwohner'].sum()

# Calculate the number of points to assign to each region based on its population
bayern_df['points'] = (bayern_df['einwohner'] / total_population * 3853).round().astype(int)

# Ensure the sum of points equals 3853
total_points = bayern_df['points'].sum()
difference = 3853 - total_points

# Adjust points to ensure the total matches exactly 3853
if difference != 0:
    # Adjust the number of points in regions with the maximum points
    adjustment_index = bayern_df['points'].nlargest(abs(difference)).index
    for idx in adjustment_index:
        if difference > 0:
            bayern_df.at[idx, 'points'] += 1
            difference -= 1
        elif difference < 0:
            bayern_df.at[idx, 'points'] -= 1
            difference += 1
        if difference == 0:
            break

# Generate random points within each region and create a DataFrame for them
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
                    'plz': row['plz'],
                    'ort': row['ort'],
                    'landkreis': row['landkreis'],
                    'latitude': random_point.y,
                    'longitude': random_point.x,
                    'fluvial': row['Fluvial'],
                    'AEP': row['AEP'],
                    'floodrisk': row['floodrisk']
                })
                break

# Convert the points to a GeoDataFrame
points_gdf = gpd.GeoDataFrame(geometry=points, crs=bayern_df.crs)

# Convert the data list to a DataFrame
points_df = pd.DataFrame(data)
print(f'Number of data points: {points_df.shape[0]}')

# Ensure that we have exactly 3853 points
assert points_df.shape[0] == 3853, "The number of points does not match the target."

# # Save the points DataFrame to a CSV file (optional)
points_df.to_csv("bayern_points_distribution.csv", index=False)

# # Display the DataFrame
# print(points_df.head())


