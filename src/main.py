from app import App
import tkinter as tk

def main():
    import argparse
    from polygon_cleaner import PolygonCleaner

    parser = argparse.ArgumentParser(description='Clean duplicate polygons and remove outdated picture references from KMZ files.')
    parser.add_argument('input_file', type=str, help='Path to the input KMZ file')

    args = parser.parse_args()

    cleaner = PolygonCleaner(args.input_file)
    cleaner.remove_duplicates()
    cleaner.remove_pictures()
    cleaner.save_cleaned_kmz()
    cleaner.save_kml()
    cleaner.cleanup()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        main()
    else:
        root = tk.Tk()
        app = App(root)
        root.mainloop()