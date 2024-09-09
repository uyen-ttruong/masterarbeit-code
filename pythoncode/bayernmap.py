import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from adjustText import adjust_text

# Load shapefile data for PLZ (Postleitzahl) and Landkreis boundaries
zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\data\plz-5stellig.shp.zip"
shp_name = 'plz-5stellig'
full_path = f"zip://{zip_path}!{shp_name}.shp"

plz_shape_df = gpd.read_file(full_path, dtype={'plz': str})
plt.rcParams['figure.figsize'] = [16, 11]

# Load region data
plz_region_df = pd.read_csv('data/zuordnung_plz_ort.csv', sep=',', dtype={'plz': str})
plz_region_df.drop('osm_id', axis=1, inplace=True)

# Merge shape data with region data
germany_df = pd.merge(
    left=plz_shape_df, 
    right=plz_region_df, 
    on='plz',
    how='inner'
)

germany_df.drop(['note'], axis=1, inplace=True)

# Filter for Bayern region
bayern_df = germany_df.query('bundesland == "Bayern"')

# Group by 'ort' and get the centroid for each unique Ort
ort_centers = bayern_df[bayern_df['landkreis'].isna()].groupby('ort').agg({
    'geometry': lambda x: x.union_all().centroid
}).reset_index()

# Ensure the geometry column is set correctly
ort_centers = ort_centers.set_geometry('geometry')

# Adjusted population bins and labels based on the actual data distribution
population_bins = [0, 2000, 5000, 10000, 20000, 30000, 50000, 100000]
population_labels = ['0-2000', '2001-5000', '5001-10000', '10001-20000', '20001-30000', '30001-50000', '50001+']

# Updating the population category based on the new bins
bayern_df['pop_category'] = pd.cut(bayern_df['einwohner'], bins=population_bins, labels=population_labels)

fig, ax = plt.subplots(figsize=(16, 11))

# Plotting the population distribution by PLZ in Bayern
bayern_df.plot(
    ax=ax, 
    column='pop_category', 
    categorical=True, 
    legend=False,  # Turn off the default legend
    cmap='summer',
    edgecolor='black', 
    linewidth=0.2 
)

# Plot red dots at the centroid of each Ort, slightly smaller
ax.scatter(
    ort_centers.geometry.x, 
    ort_centers.geometry.y, 
    color='darkred', 
    s=4, 
    zorder=5 
)

# Annotating only unique Orts with empty 'landkreis'
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

# Set white background
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

plt.tight_layout()
plt.show()