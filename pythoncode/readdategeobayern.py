import geopandas as gpd
import pandas as pd
from zipfile import ZipFile
import os
import tempfile

# Đường dẫn tới file zip
zip_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\data\hochwasserereignisse_epsg4258_shp.zip"

# Tạo thư mục tạm thời để giải nén
with tempfile.TemporaryDirectory() as tmpdir:
    with ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)
    
    # Tìm file .shp trong thư mục tạm thời
    shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
    
    if not shp_files:
        raise FileNotFoundError("Không tìm thấy file .shp trong zip")
    
    # Đọc file shapefile đầu tiên (giả sử đây là file chứa dữ liệu vùng ngập)
    shapefile_path = os.path.join(tmpdir, shp_files[0])
    gdf = gpd.read_file(shapefile_path)
    gdf.to_file('flutbayern_shapefile.shp')
    
    # Chuyển đổi GeoDataFrame thành DataFrame, bỏ cột geometry
    #df = pd.DataFrame(gdf.drop(columns='geometry'))
    
    # Đường dẫn lưu file CSV
    #csv_output_path = r"C:\Users\uyen truong\Desktop\Hochschule-Muenchen-LaTeX-Template\UeFlaecheEreignis_epsg4258.csv"
    
    # Lưu DataFrame thành CSV
    #df.to_csv(csv_output_path, index=False)


