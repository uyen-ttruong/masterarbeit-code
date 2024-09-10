import xml.etree.ElementTree as ET
import requests
import rasterio
import numpy as np
from pyproj import Transformer, CRS
import tempfile
import os
import math

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
        print(f"Tọa độ sử dụng: x={x}, y={y}")
        
        # Kiểm tra xem tọa độ có nằm trong phạm vi DGM không
        if not (bounds.left <= x < bounds.right and bounds.bottom <= y < bounds.top):
            print(f"Lỗi: Tọa độ nằm ngoài phạm vi DGM.")
            print(f"Tọa độ: ({x}, {y})")
            print(f"Phạm vi DGM: {bounds}")
            return None
        
        # Chuyển đổi tọa độ thực tế sang chỉ số pixel
        col, row = ~transform * (x, y)
        
        # Làm tròn chỉ số pixel
        row, col = int(round(row)), int(round(col))
        print(f"Chỉ số pixel: row={row}, col={col}")
        
        # Kiểm tra chỉ số pixel có nằm trong phạm vi của mảng elevation
        if 0 <= row < elevation.shape[0] and 0 <= col < elevation.shape[1]:
            return elevation[row, col]
        else:
            print(f"Cảnh báo: Chỉ số nằm ngoài phạm vi DGM. row={row}, col={col}")
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

def main(input_string):
    try:
        # Parse input string
        parts = input_string.split(';')
        if len(parts) != 3 or parts[0] != 'latitude' or parts[1] != 'longitude':
            raise ValueError("Invalid input format. Expected 'latitude;longitude;lat,lon'")
        
        latitude, longitude = map(float, parts[2].split(','))
        
        # Convert coordinates from WGS 84 to UTM32
        x, y = convert_coordinates(latitude, longitude)
        print(f"Tọa độ đầu vào (EPSG:4326): Latitude: {latitude}, Longitude: {longitude}")
        print(f"Tọa độ chuyển đổi (EPSG:25832): Easting (x): {x:.2f}, Northing (y): {y:.2f}")
        
        # DGM processing
        meta4_file = r"C:\Users\uyen truong\Downloads\landshut.meta4"
        dgm_url = get_dgm_url_from_meta4(meta4_file)
        print(f"URL của DGM: {dgm_url}")
        
        dgm_file = download_dgm(dgm_url)
        print(f"DGM đã được tải xuống tại: {dgm_file}")
        
        elevation, transform, dgm_crs, bounds = load_dgm(dgm_file)
        print(f"DGM đã được tải. Kích thước: {elevation.shape}")
        print(f"Hệ tọa độ của DGM: {dgm_crs}")
        print(f"Phạm vi DGM: {bounds}")
        
        # Thông tin từ trạm Pegel
        pegelstand_cm = 380  # Giả sử Pegelstand là 660 cm
        pegelnullpunkt_m = 389 # Pegelnullpunkt từ thông tin đã cung cấp
        
        # Tính toán mực nước tuyệt đối
        absolute_water_level = calculate_absolute_water_level(pegelstand_cm, pegelnullpunkt_m)
        
        point_elevation = get_elevation_at_point(x, y, elevation, transform, dgm_crs, dgm_crs, bounds)
        
        if point_elevation is not None:
            flood_depth = calculate_flood_depth(point_elevation, absolute_water_level)
            print(f"Độ cao địa hình: {point_elevation:.2f} m NHN")
            print(f"Pegelstand: {pegelstand_cm} cm")
            print(f"Pegelnullpunkt: {pegelnullpunkt_m:.2f} m NHN")
            print(f"Mực nước tuyệt đối: {absolute_water_level:.2f} m NHN")
            print(f"Độ sâu nước lũ: {flood_depth:.2f} m")
        else:
            print("Không thể xác định độ cao tại điểm này.")
    
    except Exception as e:
        print(f"Đã xảy ra lỗi trong main: {str(e)}")
    
    finally:
        # Xóa file tạm sau khi sử dụng
        if 'dgm_file' in locals():
            os.unlink(dgm_file)
            print("File tạm đã được xóa")

if __name__ == "__main__":
    input_string = "latitude;longitude;48.58722639452854,12.271763451420263"
    main(input_string)