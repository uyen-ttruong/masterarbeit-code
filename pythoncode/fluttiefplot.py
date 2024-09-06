import xml.etree.ElementTree as ET
import requests
import rasterio
import numpy as np
import tempfile
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def get_dgm_url_from_meta4(meta4_file):
    """Extrahiert die DGM-URL aus der meta4-Datei."""
    tree = ET.parse(meta4_file)
    root = tree.getroot()
    namespace = {'metalink': 'urn:ietf:params:xml:ns:metalink'}
    url = root.find('.//metalink:url', namespace).text
    return url

def download_dgm(url):
    """Lädt die DGM-Datei von der angegebenen URL herunter."""
    response = requests.get(url)
    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as tmp_file:
            tmp_file.write(response.content)
            return tmp_file.name
    else:
        raise Exception(f"Kann DGM-Datei nicht herunterladen. HTTP-Statuscode: {response.status_code}")

def meter_to_dms(meters, is_latitude):
    """Konvertiert Meter in Grad, Minuten, Sekunden Format mit Richtungsangabe."""
    if is_latitude:
        degrees = meters / 111111
        direction = "N" if degrees >= 0 else "S"
    else:
        degrees = meters / (111111 * np.cos(np.radians(48.75)))  # Ungefähre Breite von Ingolstadt
        direction = "O" if degrees >= 0 else "W"
    
    degrees = abs(degrees)
    d = int(degrees)
    m = int((degrees - d) * 60)
    s = ((degrees - d) * 60 - m) * 60
    return f"{d}°{m}′{s:.0f}″ {direction}"

def visualize_dgm_wireframe(tif_file_path, output_file=None):
    """Visualisiert das DGM als 3D-Wireframe mit reduzierter Achsenbeschriftung und Richtungsangaben."""
    with rasterio.open(tif_file_path) as src:
        elevation = src.read(1)
        bounds = src.bounds
    
    # Daten für feineres Gitter samplen
    sample_factor = 10
    elevation = elevation[::sample_factor, ::sample_factor]
    
    # Genaue Höhenwerte für Ingolstadt verwenden
    min_height = 362.00
    max_height = 410.87
    
    # Höhendaten normalisieren und auf den korrekten Bereich skalieren
    elevation = (elevation - np.min(elevation)) / (np.max(elevation) - np.min(elevation)) * (max_height - min_height) + min_height
    
    rows, cols = elevation.shape
    x = np.linspace(bounds.left, bounds.right, cols)
    y = np.linspace(bounds.bottom, bounds.top, rows)
    x, y = np.meshgrid(x, y)

    # 3D-Abbildung erstellen
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Surface mit farbiger Höhendarstellung und dichterem Gitter zeichnen
    surf = ax.plot_surface(x, y, elevation, cmap='terrain', alpha=0.7, linewidth=0.8, edgecolor='black')
    
    # Farbskala hinzufügen
    cbar = fig.colorbar(surf, ax=ax, shrink=0.6, aspect=20, pad=0.1)
    cbar.set_label('Höhe (m)', rotation=270, labelpad=15)
    
    # Blickwinkel einstellen
    ax.view_init(elev=30, azim=45)
    
    # Achsenbeschriftungen entfernen
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_zlabel('Höhe (m)', labelpad=20)
    
    # Achsenformatierung für DMS-Darstellung mit reduzierter Anzahl von Ticks
    ax.xaxis.set_major_locator(plt.MaxNLocator(3))
    ax.yaxis.set_major_locator(plt.MaxNLocator(3))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: meter_to_dms(x, False)))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: meter_to_dms(y, True)))
    
    # Etikettenrotation für bessere Lesbarkeit
    for label in ax.xaxis.get_ticklabels():
        label.set_rotation(45)
        label.set_ha('right')
        label.set_va('top')
    for label in ax.yaxis.get_ticklabels():
        label.set_rotation(45)
        label.set_ha('right')
        label.set_va('top')
    
    # Abstand anpassen
    ax.dist = 11
    
    # Titel hinzufügen
    plt.title('Digitales Geländemodell von Ingolstadt', fontsize=16, fontweight='bold', y=1.05)
    
    # Z-Achsengrenzen für genaue Höhendarstellung setzen
    ax.set_zlim(min_height, max_height)
    
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
        
        # TIF-Datei als 3D-Wireframe visualisieren
        output_file = "dgm_3d_wireframe_ingolstadt_updated.png"
        visualize_dgm_wireframe(dgm_file, output_file)
    
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {str(e)}")
    
    finally:
        # Temporäre Datei nach Verwendung löschen
        if 'dgm_file' in locals():
            os.unlink(dgm_file)
            print("Temporäre Datei wurde gelöscht")

if __name__ == "__main__":
    main()