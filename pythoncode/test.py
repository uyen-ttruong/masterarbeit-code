import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from zipfile import ZipFile
import tempfile
import os

# Đường dẫn đến file zip chứa dữ liệu lũ lụt
flood_zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\data\hochwasserereignisse_epsg4258_shp.zip"

# Đọc dữ liệu PLZ (Postleitzahl) từ shapefile
zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\data\plz-5stellig.shp.zip"
shp_name = 'plz-5stellig'
full_path = f"zip://{zip_path}!{shp_name}.shp"
plz_shape_df = gpd.read_file(full_path, dtype={'plz': str})

# Đọc dữ liệu vùng từ CSV
plz_region_df = pd.read_csv('data\zuordnung_plz_ort.csv', sep=',', dtype={'plz': str})
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

# Hàm để xác định mức độ rủi ro lũ lụt
def determine_flood_risk(hq_value):
    if pd.isnull(hq_value):
        return 'very low'
    elif hq_value in ['HQ 20', 'HQ 30']:
        return 'high'
    elif hq_value in ['HQ 40', 'HQ 50', 'HQ 80']:
        return 'medium'
    elif hq_value in ['HQ 100', 'HQ 200']:
        return 'low'
    else:
        return 'very low'

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
                # Tạo GeoSeries từ điểm để thực hiện chuyển đổi hệ tọa độ
                point_gdf = gpd.GeoDataFrame(geometry=[random_point], crs="EPSG:3035")
                point_wgs84 = point_gdf.to_crs("EPSG:4326")
                lon, lat = point_wgs84.geometry.x[0], point_wgs84.geometry.y[0]
                data.append({
                    'ort': row['ort'],
                    'landkreis': row['landkreis'],
                    'latitude': lat,
                    'longitude': lon
                })
                break

# Chuyển các điểm thành GeoDataFrame
points_gdf = gpd.GeoDataFrame(data, geometry=points, crs="EPSG:3035")

# Thêm cột GEB_HQ vào points_gdf và kiểm tra xem điểm có nằm trong vùng ngập lụt không
points_gdf['GEB_HQ'] = None

for idx, point in points_gdf.iterrows():
    # Kiểm tra xem điểm có nằm trong bất kỳ vùng ngập lụt nào không
    in_flood_area = flood_data[flood_data.contains(point.geometry)]
    if not in_flood_area.empty:
        # Nếu điểm nằm trong vùng ngập lụt, lấy giá trị GEB_HQ (bao gồm cả None)
        points_gdf.at[idx, 'GEB_HQ'] = in_flood_area.iloc[0]['GEB_HQ']

# Thêm cột flood_risk dựa trên giá trị GEB_HQ
points_gdf['flood_risk'] = points_gdf['GEB_HQ'].apply(determine_flood_risk)

# Hiển thị DataFrame
print(points_gdf.head())
print(f"Số điểm nằm trong vùng ngập lụt (bao gồm None): {points_gdf['GEB_HQ'].notnull().sum()}")
print(f"Tổng số điểm: {len(points_gdf)}")

# Liệt kê các giá trị HQ duy nhất
unique_hq_values = points_gdf['GEB_HQ'].unique()
print("\nCác giá trị HQ duy nhất trong points_gdf:")
for hq in sorted(unique_hq_values, key=lambda x: (x is None, x)):
    print(f"- {hq}")

# Đếm số lượng điểm cho mỗi giá trị HQ
hq_counts = points_gdf['GEB_HQ'].value_counts(dropna=False).sort_index()
print("\nSố lượng điểm cho mỗi giá trị HQ:")
for hq, count in hq_counts.items():
    if pd.isnull(hq):
        print(f"Không có giá trị HQ (None): {count}")
    else:
        print(f"HQ {hq}: {count}")

# Đếm số lượng điểm cho mỗi mức độ rủi ro lũ lụt
risk_counts = points_gdf['flood_risk'].value_counts().sort_index()
print("\nSố lượng điểm cho mỗi mức độ rủi ro lũ lụt:")
for risk, count in risk_counts.items():
    print(f"{risk.capitalize()}: {count}")

# Tính phần trăm điểm nằm trong vùng ngập lụt (bao gồm None)
percent_in_flood = (points_gdf['GEB_HQ'].notnull().sum() / len(points_gdf)) * 100
print(f"\nPhần trăm điểm nằm trong vùng ngập lụt (bao gồm None): {percent_in_flood:.2f}%")

# Tính phần trăm điểm cho mỗi mức độ rủi ro lũ lụt
risk_percentages = (risk_counts / len(points_gdf) * 100).round(2)
print("\nPhần trăm điểm cho mỗi mức độ rủi ro lũ lụt:")
for risk, percentage in risk_percentages.items():
    print(f"{risk.capitalize()}: {percentage:.2f}%")

# Lưu DataFrame điểm phân bố ra file CSV với tên "test.csv"
# Chỉ lưu các cột cần thiết, bao gồm latitude và longitude đã được chuyển đổi
points_gdf[['ort', 'landkreis', 'latitude', 'longitude', 'GEB_HQ', 'flood_risk']].to_csv("test.csv", index=False)

print("\nĐã lưu dữ liệu vào file 'test.csv'")