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
        if not (bounds.left <= x <= bounds.right and bounds.bottom <= y <= bounds.top):
            print(f"Lỗi: Tọa độ nằm ngoài phạm vi DGM.")
            print(f"Tọa độ: ({x}, {y})")
            print(f"Phạm vi DGM: {bounds}")
            print(f"Vui lòng chọn tọa độ trong phạm vi: X({bounds.left} đến {bounds.right}), Y({bounds.bottom} đến {bounds.top})")
            return None
        
        # Chuyển đổi tọa độ thực tế sang chỉ số pixel
        row, col = ~transform * (x, y)
        
        # Kiểm tra NaN hoặc inf trước khi chuyển đổi sang int
        if math.isnan(row) or math.isnan(col) or math.isinf(row) or math.isinf(col):
            print(f"Cảnh báo: Tọa độ chuyển đổi không hợp lệ. row={row}, col={col}")
            return None
        
        row, col = int(row), int(col)
        print(f"Chỉ số pixel: row={row}, col={col}")
        
        # Lấy giá trị độ cao
        if 0 <= row < elevation.shape[0] and 0 <= col < elevation.shape[1]:
            return elevation[row, col]
        else:
            print(f"Cảnh báo: Chỉ số nằm ngoài phạm vi DGM. row={row}, col={col}")
            return None
    except Exception as e:
        print(f"Lỗi trong get_elevation_at_point: {str(e)}")
        return None

def calculate_absolute_water_level(pegelstand_cm, pegelnullpunkt_m):
    """
    Tính toán mực nước tuyệt đối dựa trên Pegelstand và Pegelnullpunkt.
    
    :param pegelstand_cm: Pegelstand (cm)
    :param pegelnullpunkt_m: Pegelnullpunkt (m NHN)
    :return: Mực nước tuyệt đối (m NHN)
    """
    return pegelnullpunkt_m + (pegelstand_cm / 100)

def calculate_flood_depth(ground_elevation, water_level):
    if ground_elevation is None:
        return None
    return max(water_level - ground_elevation, 0)

def main():
    meta4_file = r"C:\Users\uyen truong\Downloads\ingolstadt.meta4"
    
    try:
        dgm_url = get_dgm_url_from_meta4(meta4_file)
        print(f"URL của DGM: {dgm_url}")
        
        dgm_file = download_dgm(dgm_url)
        print(f"DGM đã được tải xuống tại: {dgm_file}")
        
        elevation, transform, dgm_crs, bounds = load_dgm(dgm_file)
        print(f"DGM đã được tải. Kích thước: {elevation.shape}")
        print(f"Hệ tọa độ của DGM: {dgm_crs}")
        
        # Sử dụng tọa độ nằm trong phạm vi DGM (EPSG:25832)
        x, y = 678501.30, 5397001.66  # Tọa độ đã được tính toán
        print(f"Tọa độ đầu vào (EPSG:25832): x={x}, y={y}")
        
        # Thông tin từ trạm Pegel
        pegelstand_cm = 600  # Giả sử Pegelstand là 150 cm
        pegelnullpunkt_m = 360.30  # Pegelnullpunkt từ thông tin đã cung cấp (360,30 m NHN)
        
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
    main()