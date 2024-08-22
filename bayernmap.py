import geopandas as gpd
import matplotlib.pyplot as plt

# Load Bavaria GeoJSON file
bavaria = gpd.read_file('bavaria.geojson')

# Create the plot
fig, ax = plt.subplots(figsize=(10, 10))

# Plot Bavaria
bavaria.plot(ax=ax, color='lightblue', edgecolor='black')

# Add title
plt.title('Map of Bavaria', fontsize=16)

# Remove axis
ax.axis('off')

# Save the map as an image
plt.savefig('bavaria_map.png', dpi=300, bbox_inches='tight')

# Display the plot (optional)
plt.show()