
import tkinter as tk
from tkinter import ttk
from ant import AntColonyFrame  # ant.py'den AntColonyFrame'i import ediyoruz

class AboutFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        
        info_text = (
            "Hakkında\n\n"
            "Ad: Sebahattin Gökcen\n"
            "Soyad: Özden]\n"
            "E-posta: bygokcen@gmail.com\n"
            "linkedin: in/bygokcen\n"
            "X : @bygokcen"
        )
        label = tk.Label(self, text=info_text, justify=tk.LEFT)
        label.pack(padx=10, pady=10)

def main():
    root = tk.Tk()
    root.title("ACO Simulation ")

    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)

    
    aco_frame = AntColonyFrame(notebook)
    notebook.add(aco_frame, text="TSP with Ant Colony Optimization")

    
    about_frame = AboutFrame(notebook)
    notebook.add(about_frame, text="Hakkında")

    root.mainloop()

if __name__ == "__main__":
    main()