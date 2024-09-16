from pyproj import Transformer

def convert_coordinates(latitude, longitude):
    # Initialisierung des Transformers von EPSG:4326 (WGS 84) zu EPSG:25832 (UTM Zone 32N)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
    
    # Koordinatenumwandlung
    easting, northing = transformer.transform(longitude, latitude)
    
    return easting, northing

if __name__ == "__main__":
    # Eingabekoordinaten (EPSG:4326)
    latitude = 48.703833
    longitude = 11.423718
    
    # Umwandlung nach EPSG:25832
    easting, northing = convert_coordinates(latitude, longitude)
    
    # Ergebnis ausgeben
    print(f"Eingabekoordinaten (EPSG:4326): Breite: {latitude}, Länge: {longitude}")
    print(f"Umgewandelte Koordinaten (EPSG:25832): Easting: {easting:.2f}, Northing: {northing:.2f}")
