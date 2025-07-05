import zipfile
import os
import shutil
from lxml import etree as ET
import sys
import datetime

class PolygonCleaner:
    def __init__(self, kmz_file):
        self.kmz_file = kmz_file
        self.temp_dir = os.path.join(self.get_writable_path(), 'temp_kmz')
        self.output_dir = os.path.join(self.get_writable_path(), 'PolygonCleanerOutput')
        self.polygons = self.load_polygons()

    def get_writable_path(self):
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app 
            # path into variable _MEIPASS'.
            return os.path.expanduser('~')
        else:
            return os.path.expanduser('~')

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
        geometry_types = ['Polygon', 'LineString', 'MultiGeometry', 'LinearRing', 'Point']
        for placemark in placemarks:
            for geom_type in geometry_types:
                geometry = placemark.find(f'.//kml:{geom_type}', namespaces)
                if geometry is not None:
                    polygons.append((placemark, geometry))
                    break  # Only add the first found geometry type per placemark
        return polygons

    def remove_duplicates(self):
        """
        Remove duplicate polygons from the KML tree globally, even if they are in different folders/subfolders or under different parent structures.
        Keep only the last found polygon for each unique (name, coordinates) pair.
        Print debug info about which polygons are removed.
        """
        print("\n========== GLOBAL POLYGON DEDUPLICATION (BY NAME + COORDS) ==========")
        kml_file = [f for f in os.listdir(self.temp_dir) if f.endswith('.kml')][0]
        tree = ET.parse(os.path.join(self.temp_dir, kml_file))
        root = tree.getroot()
        namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
        key_to_placemark = {}
        placemarks = []
        san_roque_debug = []  # Collect debug info for SAN ROQUE only
        def normalize_coords(coords_str):
            coord_lines = [line.strip() for line in coords_str.strip().split() if line.strip()]
            norm_coords = []
            for line in coord_lines:
                parts = line.split(",")
                if len(parts) >= 2:
                    try:
                        lon = round(float(parts[0]), 6)
                        lat = round(float(parts[1]), 6)
                        norm_coords.append((lon, lat))
                    except Exception:
                        continue
            return tuple(norm_coords)

        def get_name(elem):
            # Try direct child with and without namespace
            name_elem = elem.find('{http://www.opengis.net/kml/2.2}name') or elem.find('name')
            if name_elem is not None and name_elem.text:
                return name_elem.text.strip()
            # Try any descendant <name> (with or without namespace)
            for child in elem.iter():
                if child.tag.endswith('name') and child.text:
                    return child.text.strip()
            return None

        def find_first_child_by_tag(elem, tag_suffix):
            # Find first child (any depth) whose tag ends with tag_suffix (e.g., 'Polygon', 'coordinates')
            for child in elem.iter():
                if child.tag.endswith(tag_suffix):
                    return child
            return None

        # Build a dict to track the last occurrence of each (name, geometry type, normalized coords)
        last_occurrence = {}
        placemarks_to_remove = set()
        removed_duplicates_report = []
        for placemark in root.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
            placemark_name = get_name(placemark)
            for geom_type in ['Polygon', 'LineString', 'MultiGeometry', 'LinearRing', 'Point']:
                geometry = find_first_child_by_tag(placemark, geom_type)
                if geometry is not None:
                    coords_elem = find_first_child_by_tag(geometry, 'coordinates')
                    if coords_elem is not None:
                        coords = coords_elem.text.strip()
                        norm_coords = normalize_coords(coords)
                        norm_key = (placemark_name, geom_type, norm_coords)
                        parent = placemark.getparent()
                        parent_folder = None
                        while parent is not None:
                            if parent.tag.endswith('Folder'):
                                folder_name_elem = parent.find('{http://www.opengis.net/kml/2.2}name') or parent.find('name')
                                if folder_name_elem is not None and folder_name_elem.text:
                                    parent_folder = folder_name_elem.text.strip()
                                    break
                            parent = parent.getparent()
                        # Mark previous occurrence for removal (generic logic for all names and types)
                        if norm_key in last_occurrence:
                            placemarks_to_remove.add(last_occurrence[norm_key])
                            removed_duplicates_report.append({
                                'name': placemark_name,
                                'geometry_type': geom_type,
                                'parent_folder': parent_folder,
                                'raw_coords': coords,
                                'norm_coords': norm_coords
                            })
                        last_occurrence[norm_key] = placemark
        # Remove all but the last occurrence of each unique geometry
        removed_count = 0
        for placemark in placemarks_to_remove:
            parent = placemark.getparent()
            if parent is not None:
                parent.remove(placemark)
                removed_count += 1
        # Write the removed duplicates report to a file in the output directory
        import datetime
        base_name = os.path.splitext(os.path.basename(self.kmz_file))[0]
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"Report_{base_name}_{timestamp}.txt"
        report_path = os.path.join(self.output_dir, report_filename)
        input_filename = os.path.basename(self.kmz_file)
        with open(report_path, 'w', encoding='utf-8') as report_file:
            report_file.write(f"Removed Duplicates Report\n========================\n\n")
            report_file.write(f"Input file: {input_filename}\n")
            report_file.write(f"Generated at: {timestamp}\n\n")
            report_file.write(f"Total duplicates removed: {removed_count}\n\n")
            report_file.write("This document lists all placemarks that were removed as duplicates during the deduplication process. For each removed placemark, the following information is provided:\n- Name\n- Geometry Type\n- Parent Folder (if any)\n- Raw Coordinates\n- Normalized Coordinates\n\n---\n")
            for entry in removed_duplicates_report:
                report_file.write(f"Name: {entry['name']}\n")
                report_file.write(f"Geometry Type: {entry['geometry_type']}\n")
                report_file.write(f"Parent Folder: {entry['parent_folder']}\n")
                report_file.write(f"Raw Coordinates: {entry['raw_coords']}\n")
                report_file.write(f"Normalized Coordinates: {entry['norm_coords']}\n")
                report_file.write("---\n")
        print(f"Total duplicates removed: {removed_count}")
        tree.write(os.path.join(self.temp_dir, kml_file), pretty_print=True)
        # Do NOT update self.polygons here to avoid reintroducing duplicates
        print("========== END OF DEDUPLICATION ==========")

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

    def get_output_filename(self, ext):
        """
        Generate output filename based on input, appending 'cleaned' and a timestamp.
        ext: file extension, e.g. '.kmz' or '.kml'
        """
        base = os.path.splitext(os.path.basename(self.kmz_file))[0]
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base}_cleaned_{timestamp}{ext}"

    def save_cleaned_kmz(self, output_file=None):
        # Create the output directory if it does not exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        if output_file is None:
            output_file = os.path.join(self.output_dir, self.get_output_filename('.kmz'))
        kml_file = [f for f in os.listdir(self.temp_dir) if f.endswith('.kml')][0]
        # Do NOT re-parse and re-add placemarks; just zip the cleaned KML as-is
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
            output_file = os.path.join(self.output_dir, self.get_output_filename('.kml'))
        
        kml_file = [f for f in os.listdir(self.temp_dir) if f.endswith('.kml')][0]
        shutil.copy(os.path.join(self.temp_dir, kml_file), output_file)

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def print_coordinates_by_name(self, name):
        """
        Print all coordinates for placemarks with the given name from the original KML file,
        including the name of their parent folder (if any), with a clear console header/footer.
        This version is robust to namespaces and prints all found names for debugging.
        """
        print(f"\n========== '{name.upper()}' COORDINATES REPORT ==========" , file=sys.stdout)
        kml_file = [f for f in os.listdir(self.temp_dir) if f.endswith('.kml')][0]
        tree = ET.parse(os.path.join(self.temp_dir, kml_file))
        root = tree.getroot()
        namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
        found = False
        for placemark in root.findall('.//kml:Placemark', namespaces):
            name_elem = placemark.find('kml:name', namespaces)
            if name_elem is None:
                # Try without namespace
                name_elem = placemark.find('name')
            # For debugging: print all found names
            if name_elem is not None and name_elem.text:
                debug_name = name_elem.text.strip()
                if debug_name.upper() == name.upper():
                    polygon = placemark.find('.//kml:Polygon', namespaces)
                    if polygon is not None:
                        coords_elem = polygon.find('.//kml:coordinates', namespaces)
                        if coords_elem is not None:
                            # Find parent Folder name if exists
                            parent = placemark.getparent()
                            folder_name = None
                            while parent is not None:
                                if parent.tag == '{http://www.opengis.net/kml/2.2}Folder' or parent.tag.endswith('Folder'):
                                    folder_name_elem = parent.find('kml:name', namespaces) or parent.find('name')
                                    if folder_name_elem is not None and folder_name_elem.text:
                                        folder_name = folder_name_elem.text.strip()
                                        break
                                parent = parent.getparent()
                            print(f"Placemark: {debug_name}\nFolder: {folder_name}\nCoordinates:\n{coords_elem.text.strip()}\n", file=sys.stdout)
                            found = True
        if not found:
            print("No placemarks found with the specified name.", file=sys.stdout)
        print("========== END OF REPORT ==========" , file=sys.stdout)

    def find_any_element_by_name(self, name, report_label=None):
        """
        Search for any KML element (Placemark, Folder, Document, etc.) with a <name> equal to the given name.
        Print the element type, its parent (if any), and for Placemarks with any geometry, print coordinates.
        If report_label is 'BEFORE', use the original extracted KML; if 'AFTER', use the cleaned output KML.
        """
        print(f"\n========== SEARCH FOR '{name.upper()}' IN ANY ELEMENT ==========" , file=sys.stdout)
        if report_label == 'AFTER':
            # Use the cleaned KML file from the output directory
            output_files = [f for f in os.listdir(self.output_dir) if f.endswith('.kml')]
            print(f"Output directory: {self.output_dir}", file=sys.stdout)
            print(f"Cleaned KML files found: {output_files}", file=sys.stdout)
            if not output_files:
                print("No cleaned KML file found in output directory.", file=sys.stdout)
                print("========== END OF SEARCH ==========" , file=sys.stdout)
                return
            kml_file = os.path.join(self.output_dir, sorted(output_files)[-1])
            print(f"Using cleaned KML file for AFTER reporting: {kml_file}", file=sys.stdout)
        else:
            # Use the extracted KML file from the temp directory
            kml_file = [os.path.join(self.temp_dir, f) for f in os.listdir(self.temp_dir) if f.endswith('.kml')][0]
        tree = ET.parse(kml_file)
        root = tree.getroot()
        found = False
        # Only print Placemark elements that are direct children of Document or Folder (not deleted or orphaned)
        for elem in root.iter():
            if not elem.tag.endswith('Placemark'):
                continue
            parent = elem.getparent() if hasattr(elem, 'getparent') else None
            if parent is None or (not parent.tag.endswith('Document') and not parent.tag.endswith('Folder')):
                continue
            name_elem = elem.find('{http://www.opengis.net/kml/2.2}name')
            if name_elem is None:
                name_elem = elem.find('name')
            if name_elem is not None and name_elem.text:
                debug_name = name_elem.text.strip()
                if debug_name.upper() == name.upper():
                    found = True
                    parent_tag = parent.tag if parent is not None else None
                    match_text = f"MATCH: <{elem.tag}> with name '{debug_name}' (parent: {parent_tag})"
                    # Print coordinates for any geometry type
                    for geom_type in ['Polygon', 'LineString', 'MultiGeometry', 'LinearRing', 'Point']:
                        geometry = None
                        for child in elem.iter():
                            if child.tag.endswith(geom_type):
                                geometry = child
                                break
                        if geometry is not None:
                            coords_elem = None
                            for child in geometry.iter():
                                if child.tag.endswith('coordinates'):
                                    coords_elem = child
                                    break
                            if coords_elem is not None:
                                coords = coords_elem.text.strip()
                                print(f"{match_text}\nGeometry: {geom_type}\nCoordinates:\n{coords}\n", file=sys.stdout)
                            else:
                                print(f"{match_text}\nGeometry: {geom_type}\nNO coordinates found\n", file=sys.stdout)
                            break
                    else:
                        print(match_text, file=sys.stdout)
        if not found:
            print("No elements found with the specified name.", file=sys.stdout)
        print("========== END OF SEARCH ==========" , file=sys.stdout)

    def test_search_and_report(self, name, label='BEFORE'):
        print(f"\n--- {label} DEDUPLICATION ---")
        self.find_any_element_by_name(name, report_label=label)

# Example usage
if __name__ == '__main__':
    cleaner = PolygonCleaner('/Users/brendamanrique/Documents/Projects/GMapsCleanup/input/My Places_RDS_Dic2024.kmz')
    cleaner.test_search_and_report('SAN ROQUE','BEFORE')
    cleaner.remove_duplicates()
    cleaner.remove_pictures()
    cleaner.save_cleaned_kmz()
    cleaner.save_kml()
    cleaner.test_search_and_report('SAN ROQUE','AFTER')
    cleaner.cleanup()