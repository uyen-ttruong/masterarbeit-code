import xml.etree.ElementTree as ET
import requests
import rasterio
import numpy as np
from pyproj import Transformer, CRS
import tempfile
import os
import math
import csv

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
        # Chuyển đổi tọa độ nếu cần
        if src_crs != dst_crs:
            transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
            x, y = transformer.transform(x, y)
        
        # Kiểm tra xem tọa độ có nằm trong phạm vi DGM không
        if not (bounds.left <= x < bounds.right and bounds.bottom <= y < bounds.top):
            return None
        
        # Chuyển đổi tọa độ thực tế sang chỉ số pixel
        col, row = ~transform * (x, y)
        
        # Làm tròn chỉ số pixel
        row, col = int(round(row)), int(round(col))
        
        # Kiểm tra chỉ số pixel có nằm trong phạm vi của mảng elevation
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
    if ground_elevation is None:
        return None
    return max(water_level - ground_elevation, 0)

def convert_coordinates(latitude, longitude, from_epsg=4326, to_epsg=25832):
    """Chuyển đổi tọa độ từ hệ WGS 84 (EPSG:4326) sang UTM32 (EPSG:25832)"""
    transformer = Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)
    easting, northing = transformer.transform(longitude, latitude)
    return easting, northing

def reverse_convert_coordinates(easting, northing, from_epsg=25832, to_epsg=4326):
    """Chuyển đổi tọa độ từ UTM32 (EPSG:25832) sang WGS 84 (EPSG:4326)"""
    transformer = Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)
    longitude, latitude = transformer.transform(easting, northing)
    return latitude, longitude

def scan_flood_depths(elevation, transform, dgm_crs, bounds, pegelstand_cm, pegelnullpunkt_m, step=1):
    flood_points = []
    rows, cols = elevation.shape
    absolute_water_level = calculate_absolute_water_level(pegelstand_cm, pegelnullpunkt_m)

    for row in range(0, rows, step):
        for col in range(0, cols, step):
            x, y = transform * (col, row)
            point_elevation = elevation[row, col]
            flood_depth = calculate_flood_depth(point_elevation, absolute_water_level)
            
            if flood_depth > 0.5:  # Chỉ lấy các điểm có độ sâu nước lũ lớn hơn 0,5 mét
                lat, lon = reverse_convert_coordinates(x, y)
                flood_points.append((lat, lon, flood_depth))

    return flood_points

def write_to_csv(flood_points, filename):
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Latitude', 'Longitude', 'Flood Depth (m)'])
        for point in flood_points:
            csvwriter.writerow(point)

def main():
    try:
        meta4_file = r"C:\Users\uyen truong\Downloads\09161000.meta4"
        dgm_url = get_dgm_url_from_meta4(meta4_file)
        print(f"URL của DGM: {dgm_url}")
        
        dgm_file = download_dgm(dgm_url)
        print(f"DGM đã được tải xuống tại: {dgm_file}")
        
        elevation, transform, dgm_crs, bounds = load_dgm(dgm_file)
        print(f"DGM đã được tải. Kích thước: {elevation.shape}")
        print(f"Hệ tọa độ của DGM: {dgm_crs}")
        print(f"Phạm vi DGM: {bounds}")
        
        # Thông tin từ trạm Pegel
        pegelstand_cm = 660  # Giả sử Pegelstand là 660 cm
        pegelnullpunkt_m = 360  # Pegelnullpunkt từ thông tin đã cung cấp
        
        flood_points = scan_flood_depths(elevation, transform, dgm_crs, bounds, pegelstand_cm, pegelnullpunkt_m)
        
        csv_filename = 'flood_points_ingolstadt.csv'
        write_to_csv(flood_points, csv_filename)
        
        print(f"\nĐã xuất {len(flood_points)} điểm có độ sâu nước lũ lớn hơn 0,5 mét ra file {csv_filename}")

    except Exception as e:
        print(f"Đã xảy ra lỗi trong main: {str(e)}")
    
    finally:
        # Xóa file tạm sau khi sử dụng
        if 'dgm_file' in locals():
            os.unlink(dgm_file)
            print("File tạm đã được xóa")

if __name__ == "__main__":
    main()