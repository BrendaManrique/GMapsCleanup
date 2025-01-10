import zipfile
import os
import shutil
from lxml import etree as ET

class PolygonCleaner:
    def __init__(self, kmz_file):
        self.kmz_file = kmz_file
        self.temp_dir = 'temp_kmz'
        self.polygons = self.load_polygons()

    def load_polygons(self):
        with zipfile.ZipFile(self.kmz_file, 'r') as kmz:
            kmz.extractall(self.temp_dir)
        kml_file = [f for f in os.listdir(self.temp_dir) if f.endswith('.kml')][0]
        tree = ET.parse(os.path.join(self.temp_dir, kml_file))
        root = tree.getroot()
        namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
        placemarks = root.findall('.//kml:Placemark', namespaces)
        polygons = []
        for placemark in placemarks:
            polygon = placemark.find('.//kml:Polygon', namespaces)
            if polygon is not None:
                polygons.append((placemark, polygon))
        return polygons

    def remove_duplicates(self):
        unique_polygons = []
        seen = set()

        for placemark, polygon in self.polygons:
            polygon_id = self.get_polygon_id(polygon)
            if polygon_id not in seen:
                seen.add(polygon_id)
                unique_polygons.append((placemark, polygon))

        self.polygons = unique_polygons

    def get_polygon_id(self, polygon):
        coordinates = polygon.find('.//kml:coordinates', {'kml': 'http://www.opengis.net/kml/2.2'}).text.strip()
        return hash(coordinates)

    def remove_pictures(self):
        kml_file = [f for f in os.listdir(self.temp_dir) if f.endswith('.kml')][0]
        tree = ET.parse(os.path.join(self.temp_dir, kml_file))
        root = tree.getroot()
        namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
        for ground_overlay in root.findall('.//kml:GroundOverlay', namespaces):
            parent = ground_overlay.getparent()
            parent.remove(ground_overlay)
        tree.write(os.path.join(self.temp_dir, kml_file), pretty_print=True)

    def save_cleaned_kmz(self, output_file='./output/output_cleaned.kmz'):
        kml_file = [f for f in os.listdir(self.temp_dir) if f.endswith('.kml')][0]
        tree = ET.parse(os.path.join(self.temp_dir, kml_file))
        root = tree.getroot()
        namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
        document = root.find('.//kml:Document', namespaces)
        
        # Clear existing polygons
        for placemark in document.findall('.//kml:Placemark', namespaces):
            polygon = placemark.find('.//kml:Polygon', namespaces)
            if polygon is not None:
                placemark.getparent().remove(placemark)
        
        # Add unique placemarks with polygons
        for placemark, polygon in self.polygons:
            document.append(placemark)
        
        tree.write(os.path.join(self.temp_dir, kml_file), pretty_print=True)
        with zipfile.ZipFile(output_file, 'w') as kmz:
            for foldername, subfolders, filenames in os.walk(self.temp_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    kmz.write(file_path, os.path.relpath(file_path, self.temp_dir))
        shutil.rmtree(self.temp_dir)