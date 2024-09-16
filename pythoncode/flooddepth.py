import xml.etree.ElementTree as ET
import requests
import rasterio
import numpy as np
from pyproj import Transformer, CRS
import tempfile
import os
import math
import csv
from collections import defaultdict

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
        raise Exception(f"Das DGM konnte nicht heruntergeladen werden. HTTP-Statuscode: {response.status_code}")

def load_dgm(file_path):
    with rasterio.open(file_path) as src:
        elevation = src.read(1)
        transform = src.transform
        crs = src.crs
        bounds = src.bounds
        print(f"Umfang des DGM (Bounding Box): {bounds}")
    return elevation, transform, crs, bounds

def get_elevation_at_point(x, y, elevation, transform, src_crs, dst_crs, bounds):
    try:
        if src_crs != dst_crs:
            transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
            x, y = transformer.transform(x, y)
        
        if not (bounds.left <= x < bounds.right and bounds.bottom <= y < bounds.top):
            return None
        
        col, row = ~transform * (x, y)
        row, col = int(round(row)), int(round(col))
        
        if 0 <= row < elevation.shape[0] and 0 <= col < elevation.shape[1]:
            return elevation[row, col]
        else:
            return None
    except Exception as e:
        print(f"Fehler in get_elevation_at_point: {str(e)}")
        return None

def calculate_absolute_water_level(pegelstand_cm, pegelnullpunkt_m):
    return pegelnullpunkt_m + (pegelstand_cm / 100)

def calculate_flood_depth(ground_elevation, water_level):
    if ground_elevation is None or np.isnan(ground_elevation):
        return None
    depth = water_level - ground_elevation
    return round(max(depth, 0), 2)  # Auf 2 Dezimalstellen runden

def convert_coordinates(latitude, longitude, from_epsg=4326, to_epsg=25832):
    transformer = Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)
    easting, northing = transformer.transform(longitude, latitude)
    return easting, northing

def reverse_convert_coordinates(easting, northing, from_epsg=25832, to_epsg=4326):
    transformer = Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)
    longitude, latitude = transformer.transform(easting, northing)
    return latitude, longitude

def scan_flood_depths(elevation, transform, dgm_crs, bounds, pegelstand_cm, pegelnullpunkt_m, step=10):
    flood_points = defaultdict(list)
    rows, cols = elevation.shape
    absolute_water_level = calculate_absolute_water_level(pegelstand_cm, pegelnullpunkt_m)

    for row in range(0, rows, step):
        for col in range(0, cols, step):
            x, y = transform * (col, row)
            point_elevation = elevation[row, col]
            flood_depth = calculate_flood_depth(point_elevation, absolute_water_level)
            
            if flood_depth is not None and flood_depth > 0.5:
                lat, lon = reverse_convert_coordinates(x, y)
                flood_points[flood_depth].append((lat, lon))

    return flood_points

def write_to_csv(flood_points, filename, max_unique_depths=20):
    sorted_depths = sorted(flood_points.keys(), reverse=True)
    unique_depths = sorted_depths[:max_unique_depths]

    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Breitengrad', 'Längengrad', 'Hochwassertiefe (m)'])
        
        for depth in unique_depths:
            for lat, lon in flood_points[depth]:
                csvwriter.writerow([lat, lon, depth])

def main():
    try:
        meta4_file = r"C:\Users\uyen truong\Downloads\09161000.meta4"
        dgm_url = get_dgm_url_from_meta4(meta4_file)
        print(f"URL des DGM: {dgm_url}")
        
        dgm_file = download_dgm(dgm_url)
        print(f"DGM wurde heruntergeladen: {dgm_file}")
        
        elevation, transform, dgm_crs, bounds = load_dgm(dgm_file)
        print(f"DGM wurde geladen. Größe: {elevation.shape}")
        print(f"Koordinatensystem des DGM: {dgm_crs}")
        print(f"Umfang des DGM: {bounds}")
        
        # Informationen vom Pegel
        pegelstand_cm = 660
        pegelnullpunkt_m = 360
        
        flood_points = scan_flood_depths(elevation, transform, dgm_crs, bounds, pegelstand_cm, pegelnullpunkt_m)
        
        print(f"Anzahl einzigartiger Hochwassertiefen: {len(flood_points)}")
        print("Die 5 größten Hochwassertiefen:")
        for depth in sorted(flood_points.keys(), reverse=True)[:5]:
            print(f"{depth} m: {len(flood_points[depth])} Punkte")
        
        csv_filename = 'flood_points_ingolstadt.csv'
        write_to_csv(flood_points, csv_filename)
        
        print(f"\nDie Punkte mit Hochwassertiefen wurden in die Datei {csv_filename} exportiert")

    except Exception as e:
        print(f"Fehler im Hauptprogramm: {str(e)}")
    
    finally:
        if 'dgm_file' in locals():
            os.unlink(dgm_file)
            print("Temporäre Datei wurde gelöscht")

if __name__ == "__main__":
    main()
