import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from adjustText import adjust_text

# Load shapefile data for PLZ (Postleitzahl) and Landkreis boundaries
zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\plz-5stellig.shp.zip"
shp_name = 'plz-5stellig'
full_path = f"zip://{zip_path}!{shp_name}.shp"

plz_shape_df = gpd.read_file(full_path, dtype={'plz': str})
plt.rcParams['figure.figsize'] = [16, 11]

# Load region data
plz_region_df = pd.read_csv('zuordnung_plz_ort.csv', sep=',', dtype={'plz': str})
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
    'geometry': lambda x: x.unary_union.centroid
}).reset_index()

fig, ax = plt.subplots(figsize=(16, 11))

# Plotting the population distribution by PLZ in Bayern
bayern_df.plot(
    ax=ax, 
    column='einwohner', 
    categorical=False, 
    legend=True, 
    cmap='summer',
    edgecolor='black',  # Add borders to the PLZ areas
)

# Annotating only unique Orts with empty 'landkreis' with bold orange color
texts = []
for idx, row in ort_centers.iterrows():
    texts.append(ax.text(
        row.geometry.x, 
        row.geometry.y, 
        row['ort'],
        ha='center', 
        va='center',
        fontsize=10, 
        color='darkorange',
        fontweight='bold'
    ))

# Use adjust_text to avoid overlapping
adjust_text(texts, arrowprops=dict(arrowstyle='->', color='red', lw=0.5))

# Set the title and other attributes
ax.set_title('Verteilung der Bevölkerungsdichte Bayerns nach Postleitzahlenbereichen', fontsize=16)
ax.axis('off')  # Remove axis and grid

# Adjusting the colorbar
cbar = ax.get_figure().get_axes()[1]
cbar.set_ylabel('Bevölkerung', fontsize=12)
cbar.tick_params(labelsize=10)

# Set white background
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

plt.tight_layout()
plt.show()