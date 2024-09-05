import xml.etree.ElementTree as ET
import requests
import rasterio
import numpy as np
import tempfile
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

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
        raise Exception(f"Kann DGM-Datei nicht herunterladen. HTTP-Statuscode: {response.status_code}")

def visualize_dgm_wireframe(tif_file_path, output_file=None):
    with rasterio.open(tif_file_path) as src:
        elevation = src.read(1)
        bounds = src.bounds
    
    # Lấy mẫu dữ liệu để giảm thời gian xử lý và tạo hiệu ứng lưới thưa hơn
    sample_factor = 15
    elevation = elevation[::sample_factor, ::sample_factor]
    
    rows, cols = elevation.shape
    x = np.linspace(bounds.left, bounds.right, cols)
    y = np.linspace(bounds.bottom, bounds.top, rows)
    x, y = np.meshgrid(x, y)

    # Tạo hình 3D
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Vẽ lưới wireframe
    wire = ax.plot_wireframe(x, y, elevation, rstride=1, cstride=1, color='black', linewidth=0.5)
    
    # Điều chỉnh góc nhìn
    ax.view_init(elev=30, azim=45)
    
    # Đặt nhãn cho các trục
    ax.set_xlabel('Ost-West (m)', labelpad=15)
    ax.set_ylabel('Nord-Süd (m)', labelpad=15)
    ax.set_zlabel('Höhe (m)', labelpad=15)
    
    # Điều chỉnh khoảng cách
    ax.dist = 11
    
    # Thêm tiêu đề
    plt.title('Digitales Geländemodell von Ingolstadt', fontsize=16, fontweight='bold')
    
    # Thêm thông tin về mô hình
    info_text = (
        f"Auflösung: {sample_factor}m\n"
        f"Bereich: {bounds.left:.0f}m - {bounds.right:.0f}m (O-W),\n"
        f"{bounds.bottom:.0f}m - {bounds.top:.0f}m (N-S)"
    )
    ax.text2D(0.05, 0.95, info_text, transform=ax.transAxes, fontsize=10, 
              verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7))
    
    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"3D-Wireframe-Bild wurde gespeichert unter: {output_file}")
    else:
        plt.show()

def main():
    meta4_file = r"C:\Users\uyen truong\Downloads\ingolstadt.meta4"
    
    try:
        dgm_url = get_dgm_url_from_meta4(meta4_file)
        print(f"DGM-URL: {dgm_url}")
        
        dgm_file = download_dgm(dgm_url)
        print(f"DGM wurde heruntergeladen nach: {dgm_file}")
        
        # Visualisiere die TIF-Datei als 3D-Wireframe
        output_file = "dgm_3d_wireframe_ingolstadt.png"
        visualize_dgm_wireframe(dgm_file, output_file)
    
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {str(e)}")
    
    finally:
        # Lösche die temporäre Datei nach der Verwendung
        if 'dgm_file' in locals():
            os.unlink(dgm_file)
            print("Temporäre Datei wurde gelöscht")

if __name__ == "__main__":
    main()