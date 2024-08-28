import folium

# Tọa độ
latitude = 4876559517843039
longitude = 11445235253603848

# Tạo bản đồ
my_map = folium.Map(location=[latitude, longitude], zoom_start=12)

# Đánh dấu tọa độ trên bản đồ
folium.Marker([latitude, longitude], popup="Vị trí của bạn").add_to(my_map)

# Hiển thị bản đồ
my_map.save("my_map.html")