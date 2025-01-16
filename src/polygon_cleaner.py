import zipfile
import os
import shutil
from lxml import etree as ET
import sys

class PolygonCleaner:
    def __init__(self, kmz_file):
        self.kmz_file = kmz_file
        self.temp_dir = 'temp_kmz'
        self.output_dir = os.path.join(self.get_executable_path(), 'output')
        self.polygons = self.load_polygons()

    def get_executable_path(self):
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app 
            # path into variable _MEIPASS'.
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def load_polygons(self):
        # Create the temporary directory if it does not exist
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
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
        
        # Remove GroundOverlay elements from KML
        for ground_overlay in root.findall('.//kml:GroundOverlay', namespaces):
            parent = ground_overlay.getparent()
            parent.remove(ground_overlay)
        
        tree.write(os.path.join(self.temp_dir, kml_file), pretty_print=True)
        
        # Remove image files from the temporary directory
        for root_dir, _, files in os.walk(self.temp_dir):
            for file in files:
                if file.endswith(('.jpg', '.png')):
                    os.remove(os.path.join(root_dir, file))

    def save_cleaned_kmz(self, output_file=None):
        # Create the output directory if it does not exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        if output_file is None:
            output_file = os.path.join(self.output_dir, 'output_cleaned.kmz')
        
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
                    # Skip image files
                    if not filename.endswith(('.jpg', '.png')):
                        file_path = os.path.join(foldername, filename)
                        kmz.write(file_path, os.path.relpath(file_path, self.temp_dir))

    def save_kml(self, output_file=None):
        # Create the output directory if it does not exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        if output_file is None:
            output_file = os.path.join(self.output_dir, 'output_cleaned.kml')
        
        kml_file = [f for f in os.listdir(self.temp_dir) if f.endswith('.kml')][0]
        shutil.copy(os.path.join(self.temp_dir, kml_file), output_file)

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)