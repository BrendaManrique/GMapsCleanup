import zipfile
import os

def create_kmz(kml_file, image_dir, output_kmz):
    with zipfile.ZipFile(output_kmz, 'w') as kmz:
        kmz.write(kml_file, os.path.basename(kml_file))
        for foldername, subfolders, filenames in os.walk(image_dir):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                kmz.write(file_path, os.path.relpath(file_path, image_dir))

create_kmz('example.kml', 'images', 'example.kmz')