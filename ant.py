import tkinter as tk
from tkinter import filedialog, messagebox
import csv
import random
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class AntColony:
    def __init__(self, cities, distance_matrix, ant_count, alpha=1.0, beta=2.0, rho=0.1, Q=100):
        self.cities = cities
        self.city_count = len(cities)
        self.distance_matrix = distance_matrix
        self.ant_count = ant_count
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.Q = Q
        self.pheromone = [[1.0 for _ in range(self.city_count)] for _ in range(self.city_count)]
    
    def build_ant_path(self):
        start = 0
        visited = [start]
        current = start
        total_distance = 0
        while len(visited) < self.city_count:
            next_city = self.choose_next_city(current, visited)
            visited.append(next_city)
            total_distance += self.distance_matrix[current][next_city]
            current = next_city
        total_distance += self.distance_matrix[current][start]
        visited.append(start)
        return visited, total_distance

    def choose_next_city(self, current, visited):
        probabilities = []
        total_prob = 0
        for j in range(self.city_count):
            if j not in visited:
                pheromone_val = self.pheromone[current][j] ** self.alpha
                distance_val = (1.0 / self.distance_matrix[current][j]) ** self.beta if self.distance_matrix[current][j] != 0 else 0
                prob = pheromone_val * distance_val
                probabilities.append((j, prob))
                total_prob += prob
        
        if total_prob == 0:
            candidates = [j for j in range(self.city_count) if j not in visited]
            return random.choice(candidates)
        
        r = random.uniform(0, total_prob)
        cumulative = 0
        for (j, prob) in probabilities:
            cumulative += prob
            if r <= cumulative:
                return j
        return probabilities[-1][0]
    
    def update_pheromones(self, all_paths):
        for i in range(self.city_count):
            for j in range(self.city_count):
                self.pheromone[i][j] *= (1 - self.rho)
                if self.pheromone[i][j] < 0.1:
                    self.pheromone[i][j] = 0.1
                if self.pheromone[i][j] > 50:
                    self.pheromone[i][j] = 50
        for path, distance in all_paths:
            deposit = self.Q / distance
            for k in range(len(path) - 1):
                i = path[k]
                j = path[k+1]
                self.pheromone[i][j] += deposit
                self.pheromone[j][i] += deposit

# Tkinter arayüzü
class AntColonyFrame(tk.Frame):
    def __init__(self, parent, cities=None):
        super().__init__(parent)
        self.parent = parent
        self.cities = cities
        self.distance_matrix = None
        
        self.ant_count = 20
        self.city_count = 10
        self.iterations = 100
        self.current_iteration = 0
        
        self.best_path = None
        self.best_distance = float('inf')
        self.best_ant = None
        self.best_iteration = None
        self.top4_ants = []
        self.paused = False
        
        self.alpha = 1.0
        self.beta = 2.0
        self.rho = 0.1
        self.Q = 100
        
        self.active_ants = {}
        self.simulation_data = []
        self.csv_path = None
        self.initial_best_path = None
        self.cities_drawn = False
        self.manual_distance_set = False  # Manuel mesafe girişi için bayrak
        
        self.create_widgets()
    
    def create_widgets(self):
        self.pack(fill=tk.BOTH, expand=True)
        input_frame = tk.Frame(self)
        input_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Label(input_frame, text="Iterations:").grid(row=0, column=0)
        self.iterations_entry = tk.Entry(input_frame, width=5)
        self.iterations_entry.insert(0, str(self.iterations))
        self.iterations_entry.grid(row=0, column=1)
        
        tk.Label(input_frame, text="Ant Count:").grid(row=0, column=2)
        self.ant_count_entry = tk.Entry(input_frame, width=5)
        self.ant_count_entry.insert(0, str(self.ant_count))
        self.ant_count_entry.grid(row=0, column=3)
        
        tk.Label(input_frame, text="City Count:").grid(row=0, column=4)
        self.city_count_entry = tk.Entry(input_frame, width=5)
        self.city_count_entry.insert(0, str(self.city_count))
        self.city_count_entry.grid(row=0, column=5)
        
        self.data_source_mode = tk.StringVar(value="generate")
        tk.Radiobutton(input_frame, text="Generate Cities", variable=self.data_source_mode, value="generate", command=self.toggle_city_count_entry).grid(row=1, column=0, columnspan=2)
        tk.Radiobutton(input_frame, text="Load CSV", variable=self.data_source_mode, value="csv", command=self.toggle_city_count_entry).grid(row=1, column=2, columnspan=2)
        
        self.distance_mode = tk.StringVar(value="random")
        tk.Radiobutton(input_frame, text="Random Distance", variable=self.distance_mode, value="random").grid(row=2, column=0, columnspan=2)
        tk.Radiobutton(input_frame, text="Manual Distance", variable=self.distance_mode, value="manual").grid(row=2, column=2, columnspan=2)
        tk.Radiobutton(input_frame, text="Euclidean Distance", variable=self.distance_mode, value="euclidean").grid(row=2, column=4, columnspan=2)
        
        tk.Label(input_frame, text="Speed:").grid(row=3, column=0)
        self.speed_slider = tk.Scale(input_frame, from_=10, to=100, orient=tk.HORIZONTAL)
        self.speed_slider.set(50)
        self.speed_slider.grid(row=3, column=1, columnspan=2)
        
        control_frame = tk.Frame(self)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        self.start_button = tk.Button(control_frame, text="Start", command=self.start_simulation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.pause_button = tk.Button(control_frame, text="Pause", command=self.toggle_pause, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        self.restart_button = tk.Button(control_frame, text="New Simulation", command=self.restart_simulation, state=tk.DISABLED)
        self.restart_button.pack(side=tk.LEFT, padx=5)
        self.this_restart_button = tk.Button(control_frame, text="This Restart", command=self.this_restart_simulation, state=tk.DISABLED)
        self.this_restart_button.pack(side=tk.LEFT, padx=5)
        
        content_frame = tk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        simulation_frame = tk.Frame(content_frame)
        simulation_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(simulation_frame, width=700, height=500, bg="white")
        self.canvas.pack(padx=5, pady=5)
        
        graph_frame = tk.Frame(content_frame)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.fig, self.ax = plt.subplots(figsize=(3, 2))
        self.graph_canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.graph_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.info_text = tk.Text(self, height=5)
        self.info_text.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = tk.Label(self, text="Iteration: - | BEST: - | TOP 4: - | BEST PATH: -")
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
    
    def toggle_city_count_entry(self):
        if self.data_source_mode.get() == "csv":
            self.city_count_entry.config(state=tk.DISABLED)
        else:
            self.city_count_entry.config(state=tk.NORMAL)
    
    def generate_cities(self):
        self.cities = []
        margin = 20
        width = self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else 700
        height = self.canvas.winfo_height() if self.canvas.winfo_height() > 1 else 500
        for i in range(self.city_count):
            x = random.randint(margin, width - margin)
            y = random.randint(margin, height - margin)
            label = chr(65 + i)
            self.cities.append((x, y, label))
    
    def load_cities_from_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                self.cities = []
                mode = 'cities'  # Dosyanın hangi bölümünü okuduğumuzu takip etmek için
                distance_matrix = []
                for row in reader:
                    if row[0] == 'City':
                        continue  # Başlık satırı
                    elif row[0] == 'Distance Matrix':
                        mode = 'matrix'
                        continue
                    if mode == 'cities':
                        try:
                            label = row[0]
                            x = int(row[1])
                            y = int(row[2])
                            self.cities.append((x, y, label))
                        except (ValueError, IndexError):
                            messagebox.showerror("Hata", "CSV dosyasında geçersiz veri formatı.")
                            return
                    elif mode == 'matrix':
                        distance_matrix.append([float(val) for val in row])
                self.city_count = len(self.cities)
                self.distance_matrix = distance_matrix
                messagebox.showinfo("Bilgi", f"{self.city_count} şehir CSV'den yüklendi.")
                self.redraw_cities()    
    
    def generate_random_distance_matrix(self):
        self.distance_matrix = [[0] * self.city_count for _ in range(self.city_count)]
        for i in range(self.city_count):
            for j in range(i + 1, self.city_count):
                value = random.randint(5, 100)
                self.distance_matrix[i][j] = value
                self.distance_matrix[j][i] = value
    
    def calculate_distance_matrix_euclidean(self):
        self.distance_matrix = [[0] * self.city_count for _ in range(self.city_count)]
        for i in range(self.city_count):
            for j in range(self.city_count):
                if i == j:
                    self.distance_matrix[i][j] = 0
                else:
                    xi, yi, _ = self.cities[i]
                    xj, yj, _ = self.cities[j]
                    self.distance_matrix[i][j] = int(math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2))
    
    def open_manual_distance_panel(self):
        self.manual_distance_set = False
        toplevel = tk.Toplevel(self)
        toplevel.title("Manuel Mesafe Girişi")
        
        frame = tk.Frame(toplevel)
        frame.pack(padx=10, pady=10)
        
        self.distance_vars = {}
        for i in range(self.city_count):
            for j in range(i + 1, self.city_count):
                var = tk.StringVar()
                self.distance_vars[(i, j)] = var
        
        for c in range(self.city_count):
            label = tk.Label(frame, text=self.cities[c][2])
            label.grid(row=0, column=c + 1)
        
        for r in range(self.city_count):
            label = tk.Label(frame, text=self.cities[r][2])
            label.grid(row=r + 1, column=0)
            for c in range(self.city_count):
                if r == c:
                    label = tk.Label(frame, text="0")
                    label.grid(row=r + 1, column=c + 1)
                elif r < c:
                    var = self.distance_vars[(r, c)]
                    entry = tk.Entry(frame, textvariable=var, width=5)
                    entry.grid(row=r + 1, column=c + 1)
                else:
                    var = self.distance_vars[(c, r)]
                    entry = tk.Entry(frame, textvariable=var, width=5, state='disabled')
                    entry.grid(row=r + 1, column=c + 1)
        
        def fill_random():
            for var in self.distance_vars.values():
                if not var.get():
                    var.set(str(random.randint(5, 100)))
        
        random_button = tk.Button(toplevel, text="Random", command=fill_random)
        random_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        def confirm():
            try:
                distance_matrix = [[0] * self.city_count for _ in range(self.city_count)]
                for i in range(self.city_count):
                    for j in range(i + 1, self.city_count):
                        val_str = self.distance_vars[(i, j)].get()
                        if not val_str:
                            raise ValueError("Boş alan var")
                        val = int(val_str)
                        distance_matrix[i][j] = val
                        distance_matrix[j][i] = val
                self.distance_matrix = distance_matrix
                self.manual_distance_set = True
                toplevel.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Tüm mesafeler tam sayı olmalı.")
        
        confirm_button = tk.Button(toplevel, text="Confirm", command=confirm)
        confirm_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.wait_window(toplevel)
    
    def draw_roads(self):
        self.canvas.delete("road")
        for i in range(self.city_count):
            for j in range(i + 1, self.city_count):
                x1, y1, _ = self.cities[i]
                x2, y2, _ = self.cities[j]
                self.canvas.create_line(x1, y1, x2, y2, fill="#cccccc", width=1, tags="road")
    
    def animate_city_placement(self, index=0):
        if index >= self.city_count:
            self.cities_drawn = True
            self.draw_roads()
            return
        
        x, y, label = self.cities[index]
        r = 1
        city_id = self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="red", tags="city")
        label_id = self.canvas.create_text(x, y-12, text=label, font=("Helvetica", 10, "bold"), fill="black", tags="city")
        coord_text = f"({x}, {y})"
        coord_id = self.canvas.create_text(x, y+12, text=coord_text, font=("Helvetica", 8), fill="blue", tags="city_coord")
        
        def grow(step=0, max_steps=10):
            if step >= max_steps:
                return
            new_r = 1 + (5 * step / max_steps)
            self.canvas.coords(city_id, x-new_r, y-new_r, x+new_r, y+new_r)
            self.after(50, lambda: grow(step + 1, max_steps))
        
        grow()
        self.after(500, lambda: self.animate_city_placement(index + 1))
    
    def draw_cities(self):
        if not self.cities_drawn:
            self.canvas.delete("city")
            self.canvas.delete("city_coord")
            self.animate_city_placement()
        else:
            self.canvas.delete("city")
            self.canvas.delete("city_coord")
            r = 5
            for (x, y, label) in self.cities:
                self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="red", tags="city")
                self.canvas.create_text(x, y-12, text=label, font=("Helvetica", 10, "bold"), fill="black", tags="city")
                coord_text = f"({x}, {y})"
                self.canvas.create_text(x, y+12, text=coord_text, font=("Helvetica", 8), fill="blue", tags="city_coord")

    def draw_pheromones(self):
        self.canvas.delete("pheromone")
        for i in range(self.city_count):
            for j in range(i + 1, self.city_count):
                ph = self.ant_colony.pheromone[i][j]
                width = min(1, max(0.5, int(ph * 0.05)))
                color = "#CCCCCC"
                x1, y1, _ = self.cities[i]
                x2, y2, _ = self.cities[j]
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, tags="pheromone")
    
    def draw_best_path(self):
        self.canvas.delete("best_path")
        
        if not hasattr(self, 'previous_best_paths'):
            self.previous_best_paths = []
        
        if self.best_path:
            if not self.previous_best_paths or self.best_path != self.previous_best_paths[-1]:
                self.previous_best_paths.append(self.best_path[:])
                if len(self.previous_best_paths) > 3:
                    self.previous_best_paths.pop(0)
        
        colors = ["#90EE90", "#32CD32", "#006400"]
        
        for i, path in enumerate(self.previous_best_paths[:-1]):
            for j in range(len(path) - 1):
                start = path[j]
                end = path[j+1]
                x1, y1, _ = self.cities[start]
                x2, y2, _ = self.cities[end]
                self.canvas.create_line(x1, y1, x2, y2, 
                                     fill=colors[i], 
                                     width=2, 
                                     tags="best_path")
        
        if self.previous_best_paths:
            current_best = self.previous_best_paths[-1]
            for i in range(len(current_best) - 1):
                start = current_best[i]
                end = current_best[i+1]
                x1, y1, _ = self.cities[start]
                x2, y2, _ = self.cities[end]
                self.canvas.create_line(x1, y1, x2, y2, 
                                     fill=colors[-1], 
                                     width=3, 
                                     tags="best_path")
    
    def animate_ant_path(self, path, ant_number, callback):
        ant_radius = 4
        start_city = path[0]
        x, y, _ = self.cities[start_city]
        ant_id = self.canvas.create_oval(x-ant_radius, y-ant_radius, x+ant_radius, y+ant_radius,
                                         fill="orange", tags="ant")
        ant_text = self.canvas.create_text(x, y, text=str(ant_number), fill="black",
                                           font=("Helvetica", 8, "bold"), tags="ant_text")
        self.active_ants[ant_number] = (ant_id, ant_text)
        
        total_distance = sum(self.distance_matrix[path[i]][path[i+1]] for i in range(len(path)-1))
        steps = int(20 * (total_distance / self.best_distance if self.best_distance != float('inf') else 1))
        steps = max(20, min(50, steps))
        
        def animate_segment(segment_index):
            if segment_index >= len(path) - 1:
                self.canvas.delete(ant_id)
                self.canvas.delete(ant_text)
                del self.active_ants[ant_number]
                callback()
                return
            if self.paused:
                self.after(100, lambda: animate_segment(segment_index))
                return
            start_idx = path[segment_index]
            end_idx = path[segment_index+1]
            x_start, y_start, _ = self.cities[start_idx]
            x_end, y_end, _ = self.cities[end_idx]
            dx = (x_end - x_start) / steps
            dy = (y_end - y_start) / steps
            step_counter = 0
            def move_step():
                nonlocal step_counter
                if self.paused:
                    self.after(100, move_step)
                    return
                if ant_id not in self.canvas.find_all():
                    return
                cur_coords = self.canvas.coords(ant_id)
                if len(cur_coords) < 4:
                    return
                if step_counter < steps:
                    current_x = (cur_coords[0] + cur_coords[2]) / 2
                    current_y = (cur_coords[1] + cur_coords[3]) / 2
                    trail_radius = 1
                    trail_id = self.canvas.create_oval(current_x-trail_radius, current_y-trail_radius,
                                                       current_x+trail_radius, current_y+trail_radius,
                                                       fill="yellow", outline="")
                    self.after(300, lambda tid=trail_id: self.canvas.delete(tid))
                    
                    new_x = current_x + dx
                    new_y = current_y + dy
                    self.canvas.coords(ant_id, new_x-ant_radius, new_y-ant_radius, new_x+ant_radius, new_y+ant_radius)
                    self.canvas.coords(ant_text, new_x, new_y)
                    step_counter += 1
                    speed = self.speed_slider.get()
                    delay_per_step = max(1, int(100 - speed))
                    self.after(delay_per_step, move_step)
                else:
                    animate_segment(segment_index+1)
            move_step()
        animate_segment(0)
    
    def start_simulation(self):
        try:
            self.iterations = int(self.iterations_entry.get())
            self.ant_count = int(self.ant_count_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Lütfen geçerli sayılar giriniz.")
            return
        
        if self.data_source_mode.get() == "csv":
            file_path = filedialog.askopenfilename(defaultextension=".csv", 
                                                 filetypes=[("CSV files", "*.csv")])
            if file_path:
                self.load_cities_from_csv()
                if not self.cities:
                    return
            else:
                return
        else:
            try:
                self.city_count = int(self.city_count_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Lütfen geçerli şehir sayısı giriniz.")
                return
            self.generate_cities()

        self.csv_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                    filetypes=[("CSV files", "*.csv")])
        if not self.csv_path:
            messagebox.showerror("Error", "CSV dosyası seçilmedi.")
            return
        
        if self.distance_mode.get() == "random":
            self.generate_random_distance_matrix()
            self.after_distance_setup()
        elif self.distance_mode.get() == "euclidean":
            self.calculate_distance_matrix_euclidean()
            self.after_distance_setup()
        elif self.distance_mode.get() == "manual":
            self.open_manual_distance_panel()
            if self.manual_distance_set:
                self.after_distance_setup()
            else:
                messagebox.showinfo("Info", "Manuel mesafe girişi iptal edildi.")
                return
    
    def after_distance_setup(self):
        self.display_distance_table()  
        self.ant_colony = AntColony(self.cities, self.distance_matrix, self.ant_count, self.alpha, self.beta, self.rho, self.Q)
        self.draw_cities()
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.restart_button.config(state=tk.NORMAL)
        self.this_restart_button.config(state=tk.NORMAL)
        self.iterations_entry.config(state=tk.DISABLED)
        self.ant_count_entry.config(state=tk.DISABLED)
        self.city_count_entry.config(state=tk.DISABLED)
        self.simulation_loop()
    
    def restart_simulation(self):
        self.canvas.delete("all")
        self.info_text.delete(1.0, tk.END)
        self.status_label.config(text="Iteration: - | BEST: - | TOP 4: - | BEST PATH: -")
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="Pause")
        self.restart_button.config(state=tk.DISABLED)
        self.this_restart_button.config(state=tk.DISABLED)
        self.iterations_entry.config(state=tk.NORMAL)
        self.ant_count_entry.config(state=tk.NORMAL)
        self.city_count_entry.config(state=tk.NORMAL)
        self.paused = False
        self.current_iteration = 0
        self.active_ants.clear()
        self.cities = None
        self.distance_matrix = None
        self.ant_colony = None
        self.best_path = None
        self.best_distance = float('inf')
        self.best_ant = None
        self.best_iteration = None
        self.top4_ants = []
        self.simulation_data = []
        self.csv_path = None
        self.initial_best_path = None
        self.cities_drawn = False
        self.ax.clear()
        self.graph_canvas.draw()
    
    def this_restart_simulation(self):
        self.current_iteration = 0
        self.best_path = None
        self.best_distance = float('inf')
        self.best_ant = None
        self.best_iteration = None
        self.top4_ants = []
        self.paused = False
        self.canvas.delete("pheromone")
        self.canvas.delete("best_path")
        self.canvas.delete("ant")
        self.ant_colony.pheromone = [[1.0 for _ in range(self.city_count)] for _ in range(self.city_count)]
        self.simulation_data = []
        self.initial_best_path = None
        self.ax.clear()
        self.graph_canvas.draw()
        self.simulation_loop()
    
    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_button.config(text="Resume")
        else:
            self.pause_button.config(text="Pause")
            self.simulation_loop()
    
    def display_distance_table(self):
        self.info_text.delete(1.0, tk.END)
        for i in range(self.city_count):
            line = f"{self.cities[i][2]}: "
            for j in range(self.city_count):
                if i != j:
                    dist = self.distance_matrix[i][j]
                    line += f"{self.cities[i][2]}->{self.cities[j][2]} ({dist})  "
            self.info_text.insert(tk.END, line + "\n")
    
    def save_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                # Şehir koordinatlarını yaz
                writer.writerow(['City', 'X', 'Y'])
                for city in self.cities:
                    writer.writerow([city[2], city[0], city[1]])  # city: (x, y, label)
                # Mesafe matrisini yaz
                writer.writerow(['Distance Matrix'])
                for row in self.distance_matrix:
                    writer.writerow(row)
            messagebox.showinfo("Bilgi", "Veriler CSV dosyasına kaydedildi.")
    
    def update_graph(self):
        self.ax.clear()
        iterations = [data['iteration'] for data in self.simulation_data]
        distances = [data['best_distance'] for data in self.simulation_data]
        self.ax.plot(iterations, distances, marker='o')
        self.ax.set_xlabel('Iteration')
        self.ax.set_ylabel('Best Distance')
        self.ax.set_title('Best Distance over Iterations')
        self.graph_canvas.draw()
    
    def simulation_loop(self):
        if self.paused:
            return
        if self.current_iteration >= self.iterations:
            best_path_str = " -> ".join([self.cities[i][2] for i in self.best_path]) if self.best_path else "-"
            self.status_label.config(text=f"Simulation finished. BEST: {self.best_ant} | TOP 4: {', '.join(map(str, self.top4_ants))} | Distance: {int(self.best_distance)} | BEST PATH: {best_path_str}")
            self.save_to_csv()
            return
        
        finished_count = 0
        collected_paths = []
        iteration_results = []
        
        def ant_callback(ant_num, path, distance):
            nonlocal finished_count
            collected_paths.append((path, distance))
            iteration_results.append((ant_num, distance, path))
            finished_count += 1
            if finished_count == self.ant_count:
                sorted_results = sorted(iteration_results, key=lambda x: x[1])
                iter_best_ant, iter_best_distance, iter_best_path = sorted_results[0]
                if iter_best_distance < self.best_distance:
                    self.best_distance = iter_best_distance
                    self.best_ant = iter_best_ant
                    self.best_iteration = self.current_iteration
                    self.best_path = iter_best_path
                    if self.current_iteration == 0 and not self.initial_best_path:
                        self.initial_best_path = iter_best_path
                self.top4_ants = [ant for ant, _, _ in sorted_results[:4]]
                self.ant_colony.update_pheromones(collected_paths)
                
                if self.best_path:
                    self.simulation_data.append({
                        'iteration': self.current_iteration + 1,
                        'best_distance': self.best_distance,
                        'best_path': self.best_path
                    })
                    self.update_graph()
                
                self.draw_roads()
                self.draw_pheromones()
                self.draw_best_path()
                if self.cities_drawn:
                    self.draw_cities()
                self.canvas.tag_raise("city")
                self.canvas.tag_raise("city_coord")
                best_path_str = " -> ".join([self.cities[i][2] for i in self.best_path]) if self.best_path else "-"
                self.status_label.config(
                    text=f"Iteration: {self.current_iteration + 1} | BEST: {self.best_ant} | TOP 4: {', '.join(map(str, self.top4_ants))} | Distance: {int(self.best_distance)} | BEST PATH: {best_path_str}"
                )
                self.current_iteration += 1
                self.after(100, self.simulation_loop)
        
        for ant_number in range(1, self.ant_count + 1):
            if ant_number not in self.active_ants:
                path, distance = self.ant_colony.build_ant_path()
                self.animate_ant_path(path, ant_number, lambda an=ant_number, p=path, d=distance: ant_callback(an, p, d))

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Ant Colony Optimization Simulation")
    app = AntColonyFrame(root)
    root.mainloop()