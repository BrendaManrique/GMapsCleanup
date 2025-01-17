import tkinter as tk
from tkinter import filedialog, messagebox
from polygon_cleaner import PolygonCleaner

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Earth Polygon Cleaner")
        self.root.geometry("500x300")  # Set the window size

        # Create a frame for the controls
        self.frame = tk.Frame(root, bd=2, relief=tk.SUNKEN)
        self.frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.label = tk.Label(self.frame, text="Select a KMZ file:")
        self.label.pack(pady=10)

        self.select_button = tk.Button(self.frame, text="Browse", command=self.browse_file)
        self.select_button.pack(pady=5)

        self.file_label = tk.Label(self.frame, text="", wraplength=400)
        self.file_label.pack(pady=5)

        self.run_button = tk.Button(self.frame, text="Run", command=self.run_cleaner, state=tk.DISABLED)
        self.run_button.pack(pady=20)

        self.output_label = tk.Label(self.frame, text="", wraplength=400)
        self.output_label.pack(pady=5)

        self.footer_label = tk.Label(root, text="Developed by BM V1.0 2025", font=("Arial", 8))
        self.footer_label.pack(side=tk.BOTTOM, anchor='se', padx=10, pady=10)

        self.file_path = None

    def browse_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("KMZ files", "*.kmz")])
        if self.file_path:
            self.file_label.config(text=self.file_path)
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
                output_path = cleaner.output_dir
                self.output_label.config(text=f"Output saved to: {output_path}")
                messagebox.showinfo("Success", "KMZ file cleaned successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()