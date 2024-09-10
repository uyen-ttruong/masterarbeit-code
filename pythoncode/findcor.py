import xml.etree.ElementTree as ET
import requests
import rasterio
import numpy as np
from pyproj import Transformer, CRS
import tempfile
import os
import math
import csv
from collections import defaultdict

def get_dgm_url_from_meta4(meta4_file):
    tree = ET.parse(meta4_file)
    root = tree.getroot()
    namespace = {'metalink': 'urn:ietf:params:xml:ns:metalink'}
    url = root.find('.//metalink:url', namespace).text
    return url

def download_dgm(url):
    response = requests.get(url)
    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as tmp_file:
            tmp_file.write(response.content)
            return tmp_file.name
    else:
        raise Exception(f"Không thể tải xuống file DGM. Mã trạng thái HTTP: {response.status_code}")

def load_dgm(file_path):
    with rasterio.open(file_path) as src:
        elevation = src.read(1)
        transform = src.transform
        crs = src.crs
        bounds = src.bounds
        print(f"Phạm vi DGM (bounding box): {bounds}")
    return elevation, transform, crs, bounds

def get_elevation_at_point(x, y, elevation, transform, src_crs, dst_crs, bounds):
    try:
        if src_crs != dst_crs:
            transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
            x, y = transformer.transform(x, y)
        
        if not (bounds.left <= x < bounds.right and bounds.bottom <= y < bounds.top):
            return None
        
        col, row = ~transform * (x, y)
        row, col = int(round(row)), int(round(col))
        
        if 0 <= row < elevation.shape[0] and 0 <= col < elevation.shape[1]:
            return elevation[row, col]
        else:
            return None
    except Exception as e:
        print(f"Lỗi trong get_elevation_at_point: {str(e)}")
        return None

def calculate_absolute_water_level(pegelstand_cm, pegelnullpunkt_m):
    return pegelnullpunkt_m + (pegelstand_cm / 100)

def calculate_flood_depth(ground_elevation, water_level):
    if ground_elevation is None or np.isnan(ground_elevation):
        return None
    depth = water_level - ground_elevation
    return round(max(depth, 0), 2)  # Làm tròn đến 2 chữ số thập phân

def convert_coordinates(latitude, longitude, from_epsg=4326, to_epsg=25832):
    transformer = Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)
    easting, northing = transformer.transform(longitude, latitude)
    return easting, northing

def reverse_convert_coordinates(easting, northing, from_epsg=25832, to_epsg=4326):
    transformer = Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)
    longitude, latitude = transformer.transform(easting, northing)
    return latitude, longitude

def scan_flood_depths(elevation, transform, dgm_crs, bounds, pegelstand_cm, pegelnullpunkt_m, step=10):
    flood_points = defaultdict(list)
    rows, cols = elevation.shape
    absolute_water_level = calculate_absolute_water_level(pegelstand_cm, pegelnullpunkt_m)

    for row in range(0, rows, step):
        for col in range(0, cols, step):
            x, y = transform * (col, row)
            point_elevation = elevation[row, col]
            flood_depth = calculate_flood_depth(point_elevation, absolute_water_level)
            
            if flood_depth is not None and flood_depth > 0.5:
                lat, lon = reverse_convert_coordinates(x, y)
                flood_points[flood_depth].append((lat, lon))

    return flood_points

def write_to_csv(flood_points, filename, min_depth=0.1, max_depth=4.0, num_values=5):
    # Lọc các điểm nằm trong khoảng độ sâu cho phép
    valid_depths = [depth for depth in flood_points.keys() if min_depth <= depth <= max_depth]
    
    if len(valid_depths) < num_values:
        print(f"Cảnh báo: Chỉ có {len(valid_depths)} giá trị độ sâu trong khoảng {min_depth}m - {max_depth}m")
        selected_depths = valid_depths
    else:
        # Chọn num_values giá trị đều nhau trong khoảng độ sâu
        step = (len(valid_depths) - 1) / (num_values - 1)
        indices = [int(round(i * step)) for i in range(num_values)]
        selected_depths = [valid_depths[i] for i in indices]

    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Latitude', 'Longitude', 'Flood Depth (m)'])
        
        for depth in selected_depths:
            for lat, lon in flood_points[depth]:
                csvwriter.writerow([lat, lon, depth])

    return selected_depths

def main():
    try:
        meta4_file = r"C:\Users\uyen truong\Downloads\neulm.meta4"
        dgm_url = get_dgm_url_from_meta4(meta4_file)
        print(f"URL của DGM: {dgm_url}")
        
        dgm_file = download_dgm(dgm_url)
        print(f"DGM đã được tải xuống tại: {dgm_file}")
        
        elevation, transform, dgm_crs, bounds = load_dgm(dgm_file)
        print(f"DGM đã được tải. Kích thước: {elevation.shape}")
        print(f"Hệ tọa độ của DGM: {dgm_crs}")
        print(f"Phạm vi DGM: {bounds}")
        
        # Thông tin từ trạm Pegel
        pegelstand_cm = 800
        pegelnullpunkt_m = 372
        
        flood_points = scan_flood_depths(elevation, transform, dgm_crs, bounds, pegelstand_cm, pegelnullpunkt_m)
        
        print(f"Số lượng độ sâu nước lũ duy nhất: {len(flood_points)}")
        
        csv_filename = 'flood_points_MuehldorfaInncsv'
        selected_depths = write_to_csv(flood_points, csv_filename, min_depth=0.5, max_depth=4.0, num_values=5)
        
        print("\nCác giá trị độ sâu nước lũ được chọn:")
        for depth in selected_depths:
            print(f"{depth} m: {len(flood_points[depth])} điểm")
        
        print(f"\nĐã xuất các điểm có độ sâu nước lũ ra file {csv_filename}")

    except Exception as e:
        print(f"Đã xảy ra lỗi trong main: {str(e)}")
    
    finally:
        if 'dgm_file' in locals():
            os.unlink(dgm_file)
            print("File tạm đã được xóa")

if __name__ == "__main__":
    main()