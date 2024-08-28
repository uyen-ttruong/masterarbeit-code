import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point
from matplotlib.patches import Patch
from adjustText import adjust_text
from zipfile import ZipFile
import tempfile
import os

# Đường dẫn đến file zip chứa dữ liệu lũ lụt
flood_zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\hochwasserereignisse_epsg4258_shp.zip"

# Đọc dữ liệu PLZ (Postleitzahl) từ shapefile
zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\plz-5stellig.shp.zip"
shp_name = 'plz-5stellig'
full_path = f"zip://{zip_path}!{shp_name}.shp"
plz_shape_df = gpd.read_file(full_path, dtype={'plz': str})

# Đọc dữ liệu vùng từ CSV
plz_region_df = pd.read_csv('zuordnung_plz_ort.csv', sep=',', dtype={'plz': str})
plz_region_df.drop('osm_id', axis=1, inplace=True)

# Ghép dữ liệu shapefile và dữ liệu vùng
germany_df = pd.merge(left=plz_shape_df, right=plz_region_df, on='plz', how='inner')
germany_df.drop(['note'], axis=1, inplace=True)

# Lọc dữ liệu cho Bayern
bayern_df = germany_df.query('bundesland == "Bayern"')

# Đọc dữ liệu lũ lụt từ file zip
with tempfile.TemporaryDirectory() as tmpdir:
    with ZipFile(flood_zip_path, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)
    shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
    if not shp_files:
        raise FileNotFoundError("Không tìm thấy file .shp trong zip")
    flood_data = gpd.read_file(os.path.join(tmpdir, shp_files[0]))

# Chuyển đổi CRS sang hệ tọa độ chiếu (EPSG:3035) trước khi tính toán centroid
bayern_df = bayern_df.to_crs("EPSG:3035")
flood_data = flood_data.to_crs("EPSG:3035")

# Tính toán tổng dân số
total_population = bayern_df['einwohner'].sum()

# Tính số điểm cần phân bổ cho mỗi vùng dựa trên dân số của nó
bayern_df['points'] = (bayern_df['einwohner'] / total_population * 3853).round().astype(int)

# Đảm bảo tổng số điểm bằng 3853 (do làm tròn)
difference = 3853 - bayern_df['points'].sum()
if difference != 0:
    max_index = bayern_df['points'].idxmax()
    bayern_df.at[max_index, 'points'] += difference

# Tạo các điểm ngẫu nhiên trong mỗi vùng và tạo DataFrame cho chúng
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

# Chuyển các điểm thành GeoDataFrame
points_gdf = gpd.GeoDataFrame(geometry=points)

# Chuyển danh sách dữ liệu thành DataFrame
points_df = pd.DataFrame(data)

# Tạo bản đồ với và không có dữ liệu lũ lụt
for plot_with_flood in [True, False]:
    fig, ax = plt.subplots(figsize=(16, 11))

    # Vẽ bản đồ phân bố dân số
    population_bins = [0, 2000, 5000, 10000, 20000, 30000, 50000, 100000]
    population_labels = ['0-2000', '2001-5000', '5001-10000', '10001-20000', '20001-30000', '30001-50000', '50001+']
    bayern_df['pop_category'] = pd.cut(bayern_df['einwohner'], bins=population_bins, labels=population_labels)

    bayern_df.plot(
        ax=ax,
        column='pop_category',
        categorical=True,
        legend=False,
        cmap='summer',
        edgecolor='black',
        linewidth=0.2
    )

    # Vẽ các điểm phân bố lên bản đồ
    points_gdf.plot(ax=ax, marker='o', color='darkred', markersize=1, alpha=0.5)

    # Vẽ dữ liệu lũ lụt nếu plot_with_flood là True
    if plot_with_flood:
        flood_data.plot(ax=ax, color='blue', alpha=0.5, edgecolor='darkblue', label='Vùng ngập lụt')

    # Vẽ các điểm trung tâm cho từng Ort
    ort_centers = bayern_df[bayern_df['landkreis'].isna()].groupby('ort').agg({
        'geometry': lambda x: x.unary_union.centroid
    }).reset_index()

    ort_centers = ort_centers.set_geometry('geometry')

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
    try:
        adjust_text(texts, arrowprops=dict(arrowstyle='->', color='darkred', lw=0.5))
    except MemoryError:
        print("MemoryError: Unable to adjust text. Reducing number of labels or simplifying the layout might help.")

    # Tạo chú thích cho phân loại dân số
    legend_handles = [
        Patch(color=plt.cm.summer(i / len(population_labels)), label=label)
        for i, label in enumerate(population_labels)
    ]
    ax.legend(handles=legend_handles, title='Einwohnerzahl nach PLZ', loc='lower right', fontsize=10, title_fontsize=12, bbox_to_anchor=(1.2, 0))

    # Xóa tiêu đề và đặt nền trắng
    ax.axis('off')
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    plt.tight_layout()

    # Hiển thị biểu đồ
    plt.show()

# Lưu DataFrame điểm phân bố ra file CSV (tùy chọn)
#points_df.to_csv("bayern_points_distribution.csv", index=False)

# Hiển thị DataFrame
#print(points_df.head())
