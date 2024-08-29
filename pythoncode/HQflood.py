import geopandas as gpd
import pandas as pd

# Đọc file shapefile
gdf = gpd.read_file("highmediumriskgeo.shp")

# In hệ tọa độ hiện tại
print(f"Hệ tọa độ hiện tại: {gdf.crs}")

# Chuyển đổi hệ tọa độ sang EPSG:3035
gdf = gdf.to_crs("EPSG:3035")

# Tạo danh sách để lưu trữ dữ liệu
data = []

# Lặp qua từng hàng trong GeoDataFrame
for idx, row in gdf.iterrows():
    # Lấy geometry
    geom = row['geometry']
    
    # Tạo một bản sao của dữ liệu hàng, loại bỏ cột 'geometry'
    row_data = row.drop('geometry').to_dict()
    
    # Kiểm tra loại geometry
    if geom.geom_type == 'Polygon':
        # Nếu là Polygon, lấy tọa độ của các điểm
        for point in geom.exterior.coords:
            point_data = row_data.copy()
            point_data['longitude'] = point[0]
            point_data['latitude'] = point[1]
            data.append(point_data)
    elif geom.geom_type == 'MultiPolygon':
        # Nếu là MultiPolygon, lặp qua từng polygon
        for polygon in geom.geoms:
            for point in polygon.exterior.coords:
                point_data = row_data.copy()
                point_data['longitude'] = point[0]
                point_data['latitude'] = point[1]
                data.append(point_data)

# Tạo DataFrame từ danh sách dữ liệu
df = pd.DataFrame(data)

# Lưu DataFrame thành file CSV
output_file = "highmediumriskgeo_all_columns_latlon_epsg3035.csv"
df.to_csv(output_file, index=False)

print(f"Đã lưu dữ liệu vào file '{output_file}'")

# Hiển thị vài dòng đầu tiên của DataFrame
print("\nNăm dòng đầu tiên của dữ liệu:")
print(df.head())

# Hiển thị thông tin về các cột
print("\nThông tin về các cột:")
print(df.info())