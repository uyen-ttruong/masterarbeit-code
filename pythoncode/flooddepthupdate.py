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
        raise Exception(f"DGM-Datei konnte nicht heruntergeladen werden. HTTP-Statuscode: {response.status_code}")

def load_dgm(file_path):
    with rasterio.open(file_path) as src:
        elevation = src.read(1)
        transform = src.transform
        crs = src.crs
        bounds = src.bounds
        print(f"DGM-Bereich (Bounding Box): {bounds}")
    return elevation, transform, crs, bounds

def get_elevation_at_point(x, y, elevation, transform, src_crs, dst_crs, bounds):
    try:
        # Koordinaten umwandeln, falls erforderlich
        if src_crs != dst_crs:
            transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
            x, y = transformer.transform(x, y)
        print(f"Verwendete Koordinaten: x={x}, y={y}")
        
        # Prüfen, ob die Koordinaten innerhalb des DGM-Bereichs liegen
        if not (bounds.left <= x < bounds.right and bounds.bottom <= y < bounds.top):
            print(f"Fehler: Koordinaten liegen außerhalb des DGM-Bereichs.")
            print(f"Koordinaten: ({x}, {y})")
            print(f"DGM-Bereich: {bounds}")
            return None
        
        # Umwandlung von realen Koordinaten in Pixel-Indizes
        col, row = ~transform * (x, y)
        
        # Pixel-Indizes runden
        row, col = int(round(row)), int(round(col))
        print(f"Pixel-Indizes: row={row}, col={col}")
        
        # Prüfen, ob die Pixel-Indizes innerhalb des Höhenarray-Bereichs liegen
        if 0 <= row < elevation.shape[0] and 0 <= col < elevation.shape[1]:
            return elevation[row, col]
        else:
            print(f"Warnung: Index liegt außerhalb des DGM-Bereichs. row={row}, col={col}")
            return None
    except Exception as e:
        print(f"Fehler in get_elevation_at_point: {str(e)}")
        return None

def calculate_absolute_water_level(pegelstand_cm, pegelnullpunkt_m):
    return pegelnullpunkt_m + (pegelstand_cm / 100)

def calculate_flood_depth(ground_elevation, water_level):
    if ground_elevation is None:
        return None
    return max(water_level - ground_elevation, 0)

def convert_coordinates(latitude, longitude, from_epsg=4326, to_epsg=25832):
    """Konvertiert Koordinaten von WGS 84 (EPSG:4326) zu UTM32 (EPSG:25832)"""
    transformer = Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)
    easting, northing = transformer.transform(longitude, latitude)
    return easting, northing

def reverse_convert_coordinates(easting, northing, from_epsg=25832, to_epsg=4326):
    """Konvertiert Koordinaten von UTM32 (EPSG:25832) zu WGS 84 (EPSG:4326)"""
    transformer = Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)
    longitude, latitude = transformer.transform(easting, northing)
    return latitude, longitude

def main(input_string):
    try:
        # Eingabestring parsen
        parts = input_string.split(';')
        if len(parts) != 3 or parts[0] != 'latitude' or parts[1] != 'longitude':
            raise ValueError("Ungültiges Eingabeformat. Erwartet: 'latitude;longitude;lat,lon'")
        
        latitude, longitude = map(float, parts[2].split(','))
        
        # Koordinaten von WGS 84 zu UTM32 konvertieren
        x, y = convert_coordinates(latitude, longitude)
        print(f"Eingabekoordinaten (EPSG:4326): Breitengrad: {latitude}, Längengrad: {longitude}")
        print(f"Konvertierte Koordinaten (EPSG:25832): Easting (x): {x:.2f}, Northing (y): {y:.2f}")
        
        # DGM-Verarbeitung
        meta4_file = r"C:\Users\uyen truong\Downloads\landshut.meta4"
        dgm_url = get_dgm_url_from_meta4(meta4_file)
        print(f"DGM-URL: {dgm_url}")
        
        dgm_file = download_dgm(dgm_url)
        print(f"DGM wurde heruntergeladen nach: {dgm_file}")
        
        elevation, transform, dgm_crs, bounds = load_dgm(dgm_file)
        print(f"DGM wurde geladen. Größe: {elevation.shape}")
        print(f"DGM-Koordinatensystem: {dgm_crs}")
        print(f"DGM-Bereich: {bounds}")
        
        # Informationen vom Pegel
        pegelstand_cm = 380  # Angenommen, der Pegelstand beträgt 660 cm
        pegelnullpunkt_m = 389 # Pegelnullpunkt aus den bereitgestellten Informationen
        
        # Berechnung des absoluten Wasserstands
        absolute_water_level = calculate_absolute_water_level(pegelstand_cm, pegelnullpunkt_m)
        
        point_elevation = get_elevation_at_point(x, y, elevation, transform, dgm_crs, dgm_crs, bounds)
        
        if point_elevation is not None:
            flood_depth = calculate_flood_depth(point_elevation, absolute_water_level)
            print(f"Geländehöhe: {point_elevation:.2f} m NHN")
            print(f"Pegelstand: {pegelstand_cm} cm")
            print(f"Pegelnullpunkt: {pegelnullpunkt_m:.2f} m NHN")
            print(f"Absoluter Wasserstand: {absolute_water_level:.2f} m NHN")
            print(f"Überschwemmungstiefe: {flood_depth:.2f} m")
        else:
            print("Die Höhe an diesem Punkt konnte nicht ermittelt werden.")
    
    except Exception as e:
        print(f"Ein Fehler ist in main aufgetreten: {str(e)}")
    
    finally:
        # Temporäre Datei nach Gebrauch löschen
        if 'dgm_file' in locals():
            os.unlink(dgm_file)
            print("Temporäre Datei wurde gelöscht")

if __name__ == "__main__":
    input_string = "latitude;longitude;48.58722639452854,12.271763451420263"
    main(input_string)