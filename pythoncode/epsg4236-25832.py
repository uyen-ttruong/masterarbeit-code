from pyproj import Transformer

def convert_coordinates(latitude, longitude):
    # Khởi tạo Transformer từ EPSG:4326 (WGS 84) sang EPSG:25832 (UTM Zone 32N)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
    
    # Chuyển đổi tọa độ
    easting, northing = transformer.transform(longitude, latitude)
    
    return easting, northing

if __name__ == "__main__":
    # Tọa độ đầu vào (EPSG:4326)
    latitude = 48.703833
    longitude = 11.423718
    
    # Chuyển đổi sang EPSG:25832
    easting, northing = convert_coordinates(latitude, longitude)
    
    # In kết quả
    print(f"Tọa độ đầu vào (EPSG:4326): Latitude: {latitude}, Longitude: {longitude}")
    print(f"Tọa độ chuyển đổi (EPSG:25832): Easting: {easting:.2f}, Northing: {northing:.2f}")
