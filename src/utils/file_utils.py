import zipfile
import os
import shutil

def read_kmz(file_path):
    temp_dir = 'temp_kmz'
    with zipfile.ZipFile(file_path, 'r') as kmz:
        kmz.extractall(temp_dir)
    return temp_dir

def write_kmz(file_path, data_dir):
    with zipfile.ZipFile(file_path, 'w') as kmz:
        for foldername, subfolders, filenames in os.walk(data_dir):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                kmz.write(file_path, os.path.relpath(file_path, data_dir))
    shutil.rmtree(data_dir)

def get_picture_paths(directory):
    picture_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.jpg', '.png')):
                picture_paths.append(os.path.join(root, file))
    return picture_paths