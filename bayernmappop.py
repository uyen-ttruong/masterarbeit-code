import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point
from matplotlib.patches import Patch  # Import Patch for the legend
from adjustText import adjust_text

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

# Adjust CRS to reduce distortion
bayern_df = bayern_df.to_crs("EPSG:3035") 

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

# Group by 'ort' and get the centroid for each unique Ort
ort_centers = bayern_df[bayern_df['landkreis'].isna()].groupby('ort').agg({
    'geometry': lambda x: x.union_all().centroid
}).reset_index()

# Ensure the geometry column is set correctly
ort_centers = ort_centers.set_geometry('geometry')

# Plot the map
fig, ax = plt.subplots(figsize=(16, 11))

# Adjusted population bins and labels based on the actual data distribution
population_bins = [0, 2000, 5000, 10000, 20000, 30000, 50000, 100000]
population_labels = ['0-2000', '2001-5000', '5001-10000', '10001-20000', '20001-30000', '30001-50000', '50001+']

# Updating the population category based on the new bins
bayern_df['pop_category'] = pd.cut(bayern_df['einwohner'], bins=population_bins, labels=population_labels)

bayern_df.plot(
    ax=ax, 
    column='pop_category', 
    categorical=True, 
    legend=False,  # Turn off the default legend
    cmap='summer',
    edgecolor='black',
    linewidth=0.2
)

# Overlay the points on the map in dark red
points_gdf.plot(ax=ax, marker='o', color='darkred', markersize=1, alpha=0.5)

# Plot red dots at the centroid of each Ort, slightly smaller
ax.scatter(
    ort_centers.geometry.x, 
    ort_centers.geometry.y, 
    color='darkred', 
    s=4,
    zorder=5
)

# Annotating only unique Orts with empty 'landkreis' 
# with white color and a semi-transparent black background for better readability
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

# Use adjust_text to avoid overlapping
adjust_text(texts, arrowprops=dict(arrowstyle='->', color='darkred', lw=0.5))

# Manually create a legend with colored patches
legend_handles = [
    Patch(color=plt.cm.summer(i/len(population_labels)), label=label) 
    for i, label in enumerate(population_labels)
]

# Position legend in the bottom right corner, outside the map area
ax.legend(handles=legend_handles, title='Einwohnerzahl nach PLZ', loc='lower right', fontsize=10, title_fontsize=12, bbox_to_anchor=(1.2, 0))

# Remove the title
ax.axis('off')

# Set the background color to white
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# Adjust layout to remove any unnecessary padding
plt.tight_layout()

# Save the figure with high resolution
plt.savefig('bayern_map.png', dpi=300, bbox_inches='tight')

plt.show()

# Save the points DataFrame to a CSV file (optional)
points_df.to_csv("bayern_points_distribution.csv", index=False)

# Display the DataFrame
print(points_df.head())
