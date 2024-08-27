import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from zipfile import ZipFile
import tempfile
import os

# Đường dẫn đến file zip chứa dữ liệu lũ lụt
flood_zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\hochwasserereignisse_epsg4258_shp.zip"

# Đọc dữ liệu Bayern
zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\plz-5stellig.shp.zip"
shp_name = 'plz-5stellig'
full_path = f"zip://{zip_path}!{shp_name}.shp"
plz_shape_df = gpd.read_file(full_path, dtype={'plz': str})

plz_region_df = pd.read_csv('zuordnung_plz_ort.csv', sep=',', dtype={'plz': str})
plz_region_df.drop('osm_id', axis=1, inplace=True)

germany_df = pd.merge(left=plz_shape_df, right=plz_region_df, on='plz', how='inner')
germany_df.drop(['note'], axis=1, inplace=True)
bayern_df = germany_df.query('bundesland == "Bayern"')

# Đọc dữ liệu lũ lụt từ file zip
with tempfile.TemporaryDirectory() as tmpdir:
    with ZipFile(flood_zip_path, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)
    
    # Tìm file .shp trong thư mục tạm thời
    shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
    
    if not shp_files:
        raise FileNotFoundError("Không tìm thấy file .shp trong zip")
    
    # Đọc file shapefile đầu tiên (giả sử đây là file chứa dữ liệu vùng ngập)
    flood_data = gpd.read_file(os.path.join(tmpdir, shp_files[0]))

# Đảm bảo cùng hệ tọa độ
bayern_df = bayern_df.to_crs(flood_data.crs)

# Tạo bản đồ
fig, ax = plt.subplots(figsize=(16, 11))

# Vẽ bản đồ Bayern với cmap='summer'
bayern_df.plot(
    ax=ax, 
    column='einwohner', 
    categorical=False, 
    legend=True, 
    cmap='summer',
    edgecolor='none',
    alpha=0.7
)

# Vẽ vùng ngập
flood_data.plot(ax=ax, color='blue', alpha=0.5, edgecolor='darkblue', label='Vùng ngập')

# Thêm tiêu đề và chú thích
ax.set_title('Vùng ngập lụt và phân bố dân số ở Bayern', fontsize=16)
ax.axis('off')

# Điều chỉnh thanh màu (colorbar)
cbar = ax.get_figure().get_axes()[1]
cbar.set_ylabel('Dân số', fontsize=12)
cbar.tick_params(labelsize=10)

# Thêm chú thích cho vùng ngập
ax.legend(fontsize=10, loc='lower left')

# Đặt nền trắng
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

plt.tight_layout()
plt.show()

# In thông tin về dữ liệu lũ lụt
print(flood_data.info())
print(flood_data.head())
flood_data.to_csv("bayernflooddata.csv", index=False)