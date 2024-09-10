from pyproj import Transformer, CRS

def convert_coordinates(easting, northing, from_epsg=3035, to_epsg=25832):
    # Tạo đối tượng Transformer
    transformer = Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)
    
    # Thực hiện chuyển đổi
    easting_converted, northing_converted = transformer.transform(easting, northing)
    
    return easting_converted, northing_converted

# Tọa độ đầu vào (EPSG:3035)
easting_3035 =   4425682.23 # x11.875082552281812
northing_3035 =  2850766.10  # y

# Chuyển đổi tọa độ
easting_25832, northing_25832 = convert_coordinates(easting_3035, northing_3035)

# In kết quả
print(f"Tọa độ gốc (EPSG:3035):")
print(f"Easting (x): {easting_3035}")
print(f"Northing (y): {northing_3035}")
print(f"\nTọa độ chuyển đổi (EPSG:25832):")
print(f"Easting (x): {easting_25832:.2f}")
print(f"Northing (y): {northing_25832:.2f}")

if __name__ == "__main__":
    # Kiểm tra xem script có được chạy trực tiếp không
    print("Chạy chuyển đổi tọa độ...")
    easting_25832, northing_25832 = convert_coordinates(easting_3035, northing_3035)
    print(f"Kết quả:")
    print(f"Easting (x): {easting_25832:.2f}")
    print(f"Northing (y): {northing_25832:.2f}")