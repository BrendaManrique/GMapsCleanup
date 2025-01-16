import tkinter as tk
from tkinter import filedialog, messagebox
from polygon_cleaner import PolygonCleaner

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Polygon Cleaner")

        self.label = tk.Label(root, text="Select a KMZ file:")
        self.label.pack(pady=10)

        self.select_button = tk.Button(root, text="Browse", command=self.browse_file)
        self.select_button.pack(pady=5)

        self.run_button = tk.Button(root, text="Run", command=self.run_cleaner, state=tk.DISABLED)
        self.run_button.pack(pady=20)

        self.file_path = None

    def browse_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("KMZ files", "*.kmz")])
        if self.file_path:
            self.run_button.config(state=tk.NORMAL)

    def run_cleaner(self):
        if self.file_path:
            try:
                cleaner = PolygonCleaner(self.file_path)
                cleaner.remove_duplicates()
                cleaner.remove_pictures()
                cleaner.save_cleaned_kmz()
                cleaner.save_kml()
                cleaner.cleanup()
                messagebox.showinfo("Success", "KMZ file cleaned successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")