import geopandas as gpd
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

print(plt.style.available)
plt.style.use('seaborn-v0_8')


zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\plz-5stellig.shp.zip"

shp_name = 'plz-5stellig'

full_path = f"zip://{zip_path}!{shp_name}.shp"

plz_shape_df = gpd.read_file(full_path, dtype={'plz': str})
plt.rcParams['figure.figsize'] = [16, 11]


plz_region_df = pd.read_csv(
    'zuordnung_plz_ort.csv',
    sep=',',
    dtype={'plz': str}
)

plz_region_df.drop('osm_id', axis=1, inplace=True)
#print(plz_region_df.head())
# Merge data.
germany_df = pd.merge(
    left=plz_shape_df, 
    right=plz_region_df, 
    on='plz',
    how='inner'
)

germany_df.drop(['note'], axis=1, inplace=True)

bayern_df = germany_df.query('bundesland == "Bayern"')

fig, ax = plt.subplots()

bayern_df.plot(
    ax=ax, 
    column='einwohner', 
    categorical=False, 
    legend=True, 
    cmap='autumn_r',
)

ax.set(
    title='Bayern: Anzahl der Einwohner pro Postleitzahl', 
    aspect=1.3, 
    facecolor='lightblue'
);
plt.show()
#germany_df.to_csv('germany_df.csv', index=False)