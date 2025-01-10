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

if __name__ == '__main__':
    main()