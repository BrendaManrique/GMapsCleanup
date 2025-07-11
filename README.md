# Polygon Cleaner

Polygon Cleaner is a Python application designed to clean duplicate polygons from KMZ files and remove outdated picture references. This tool is useful for users who frequently work with geographic data and need to maintain clean datasets. Developed by Brenda Manrique. 

## Features

- Remove duplicate polygons from KMZ files.
- Remove outdated picture references based on updated directory names.

## Project Structure

```
polygon-cleaner
├── src
│   ├── main.py          # Entry point of the application
│   ├── polygon_cleaner.py # Contains the main logic for cleaning polygons
│   └── utils
│       └── file_utils.py  # Utility functions for file operations
├── requirements.txt     # Lists the dependencies required for the project
└── README.md            # Documentation for the project
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd polygon-cleaner
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run and trigger the application, use the following command:

```
python src/app.py
```

Replace `<path_to_kmz_file>` with the path to your KMZ file.

To run locally:

```
python ./src/polygon_cleaner.py
```
And replace the file path inside the __main__, in the line cleaner = PolygonCleaner().

## Build the Executable

Run PyInstaller with the spec file to create the standalone executable:

```pyinstaller polygon_cleaner.spec```

```pyinstaller --onefile --windowed --name "PolygonCleaner" src/app.py```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.