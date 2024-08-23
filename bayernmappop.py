import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point

# Load the shapefile
zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\plz-5stellig.shp.zip"
shp_name = 'plz-5stellig'
full_path = f"zip://{zip_path}!{shp_name}.shp"
plz_shape_df = gpd.read_file(full_path, dtype={'plz': str})
plt.rcParams['figure.figsize'] = [16, 11]

# Load the regional data
plz_region_df = pd.read_csv(
    'zuordnung_plz_ort.csv',
    sep=',',
    dtype={'plz': str}
)

# Prepare the data by merging the shapefile and population data
plz_region_df.drop('osm_id', axis=1, inplace=True)
germany_df = pd.merge(
    left=plz_shape_df, 
    right=plz_region_df, 
    on='plz',
    how='inner'
)
germany_df.drop(['note'], axis=1, inplace=True)

# Filter for Bayern
bayern_df = germany_df.query('bundesland == "Bayern"')

# Calculate the total population
total_population = bayern_df['einwohner'].sum()

# Calculate the number of points to assign to each region based on its population
bayern_df['points'] = (bayern_df['einwohner'] / total_population * 3853).round().astype(int)

# Ensure the sum of points equals 3853 (due to rounding)
difference = 3853 - bayern_df['points'].sum()
if difference != 0:
    max_index = bayern_df['points'].idxmax()
    bayern_df.at[max_index, 'points'] += difference

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
                    'ort': row['ort'],
                    'landkreis': row['landkreis'],
                    'latitude': random_point.y,
                    'longitude': random_point.x
                })
                break

# Convert the points to a GeoDataFrame
points_gdf = gpd.GeoDataFrame(geometry=points)

# Convert the data list to a DataFrame
points_df = pd.DataFrame(data)

# Plot the map
fig, ax = plt.subplots()

bayern_df.plot(
    ax=ax, 
    column='einwohner', 
    categorical=False, 
    legend=True, 
    cmap='summer',
    edgecolor='none',  # Remove the borders
)

# Overlay the points on the map in red
points_gdf.plot(ax=ax, marker='o', color='red', markersize=2, alpha=0.5)

# Set the title and other plot attributes
ax.set_title('Verteilung der Hypothekendatenpunkte Bayerns', fontsize=16)
ax.axis('off')  # Remove axes

# Adjust the colorbar
cbar = ax.get_figure().get_axes()[1]
cbar.set_ylabel('Bevölkerung', fontsize=12)
cbar.tick_params(labelsize=10)

# Set the background color to white
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

plt.tight_layout()
plt.show()

# Save the points DataFrame to a CSV file (optional)
points_df.to_csv("bayern_points_distribution.csv", index=False)

# Display the DataFrame
print(points_df.head())