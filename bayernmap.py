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
    edgecolor='none',  # Loại bỏ đường viền của các vùng
)

# Thiết lập tiêu đề và các thuộc tính khác
ax.set_title('Bayern: Anzahl der Einwohner pro Postleitzahl', fontsize=16)
ax.axis('off')  # Loại bỏ trục và đường lưới

# Điều chỉnh thanh màu (colorbar)
cbar = ax.get_figure().get_axes()[1]
cbar.set_ylabel('Einwohner', fontsize=12)
cbar.tick_params(labelsize=10)

# Đặt nền trắng
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

plt.tight_layout()
plt.show()
try:
    bayern_df.to_csv("bayern_df.csv", index=False)
    print("File CSV đã được tạo thành công.")
except Exception as e:
    print(f"Có lỗi khi tạo file CSV: {e}")