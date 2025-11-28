import tkinter as tk
from tkinter import ttk, messagebox
import csv
import math

class PriceComparatorApp:
    def __init__(self, root, data):
        self.root = root
        self.root.title("Comparatore Prezzi Dinamico")
        self.root.geometry("1200x700")
        
        # Configurazione colori e stile
        self.bg_color = "#1e1e1e"
        self.text_color = "#ffffff"
        self.bar_blue = "#3498db"
        self.bar_red = "#e74c3c"
        self.font_main = ("Helvetica", 12, "bold")
        self.font_small = ("Helvetica", 10)

        # Dati
        self.all_data = data  # Lista completa dal CSV
        self.active_items = [] # Elementi attivati tramite checkbox
        
        # Variabili per animazione
        self.max_scale_value = 10.0 # Valore massimo scala iniziale
        self.target_max_scale = 10.0
        self.bar_height = 40
        self.spacing = 20
        self.animation_speed = 0.1 # 10% di avvicinamento per frame (smoothing)

        # Dizionario per tracciare lo stato corrente di ogni prodotto (per animazione fluida)
        # { 'nome': { 'current_val_min': 0, 'current_val_max': 0, 'current_y': 0 } }
        self.anim_state = {}
        for item in self.all_data:
            self.anim_state[item['nome']] = {
                'cur_min': 0, 
                'cur_max': 0, 
                'cur_y': 1000, # Parte fuori schermo
                'target_y': 1000
            }

        self._setup_ui()
        self._start_animation_loop()

    def _setup_ui(self):
        # Layout principale: Sinistra (Controlli), Destra (Grafico)
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- PANNELLO SINISTRO (CHECKBOX) ---
        control_panel = tk.Frame(main_frame, width=300, bg="#2c3e50")
        control_panel.pack(side=tk.LEFT, fill=tk.Y)
        control_panel.pack_propagate(False) # Mantiene la larghezza fissa

        lbl_title = tk.Label(control_panel, text="Prodotti", font=("Arial", 16, "bold"), 
                             bg="#2c3e50", fg="white", pady=10)
        lbl_title.pack(side=tk.TOP)

        # Scrollbar per la lista prodotti
        canvas_scroll = tk.Canvas(control_panel, bg="#2c3e50", highlightthickness=0)
        scrollbar = ttk.Scrollbar(control_panel, orient="vertical", command=canvas_scroll.yview)
        self.scrollable_frame = tk.Frame(canvas_scroll, bg="#2c3e50")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
        )

        canvas_scroll.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)

        canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Generazione Checkbox
        self.check_vars = {}
        for item in self.all_data:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.scrollable_frame, text=f"{item['nome']}", 
                                 variable=var, bg="#2c3e50", fg="white", selectcolor="#2c3e50",
                                 activebackground="#2c3e50", activeforeground="white",
                                 font=("Arial", 11), anchor="w",
                                 command=self._update_active_list)
            chk.pack(fill=tk.X, padx=10, pady=2)
            self.check_vars[item['nome']] = var

        # --- PANNELLO DESTRO (GRAFICA) ---
        self.canvas = tk.Canvas(main_frame, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def _update_active_list(self):
        """Ricostruisce la lista degli elementi attivi basandosi sulle checkbox"""
        self.active_items = []
        for item in self.all_data:
            if self.check_vars[item['nome']].get():
                self.active_items.append(item)
        
        # Ordina: I più costosi (Max Price) in cima
        self.active_items.sort(key=lambda x: x['max'], reverse=True)

        # Calcola la nuova scala massima
        if self.active_items:
            # Trova il prezzo massimo tra gli elementi attivi
            global_max = max(item['max'] for item in self.active_items)
            # Aggiungi un 10% di margine
            self.target_max_scale = global_max * 1.1
        else:
            self.target_max_scale = 10.0 # Valore di default

    def _lerp(self, start, end, factor):
        """Interpolazione lineare per animazioni fluide"""
        return start + (end - start) * factor

    def _draw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        # Margini del grafico
        margin_left = 150
        margin_right = 50
        margin_top = 50
        graph_w = w - margin_left - margin_right

        # 1. Disegna l'asse / Scala
        self.canvas.create_line(margin_left, margin_top, margin_left, h, fill="white", width=2)
        
        # Disegna linee griglia verticali e testo scala
        num_ticks = 5
        for i in range(num_ticks + 1):
            val = (self.max_scale_value / num_ticks) * i
            x_pos = margin_left + (val / self.max_scale_value) * graph_w
            
            # Linea griglia
            self.canvas.create_line(x_pos, margin_top, x_pos, h, fill="#333333", dash=(2, 4))
            # Testo
            val_text = f"{val:,.2f}€".replace(",", "X").replace(".", ",").replace("X", ".")
            if val >= 1000: val_text = f"{val/1000:.1f}k€" # Abbrevia se numeri grandi
            
            self.canvas.create_text(x_pos, margin_top - 20, text=val_text, fill="#aaaaaa", font=self.font_small)

        # 2. Aggiorna e disegna barre
        # Calcola le posizioni target Y per il sorting
        target_indices = {item['nome']: i for i, item in enumerate(self.active_items)}
        
        for item in self.all_data:
            name = item['nome']
            state = self.anim_state[name]
            is_active = name in target_indices

            # Calcolo Target Y
            if is_active:
                index = target_indices[name]
                state['target_y'] = margin_top + index * (self.bar_height + self.spacing)
                
                # Se era nascosto (fuori schermo), teletrasportalo sotto l'ultimo elemento visibile per farlo "entrare"
                if state['cur_y'] > h + 100:
                    state['cur_y'] = h + 50 
            else:
                # Se non attivo, fallo scendere fuori schermo
                state['target_y'] = h + 200 

            # ANIMAZIONE: Interpolazione valori
            state['cur_min'] = self._lerp(state['cur_min'], item['min'] if is_active else 0, self.animation_speed)
            state['cur_max'] = self._lerp(state['cur_max'], item['max'] if is_active else 0, self.animation_speed)
            state['cur_y'] = self._lerp(state['cur_y'], state['target_y'], self.animation_speed)

            # Disegno solo se parzialmente visibile
            if state['cur_y'] < h + 100 and state['cur_max'] > 0.01:
                y = state['cur_y']
                
                # Larghezze in pixel
                width_min = (state['cur_min'] / self.max_scale_value) * graph_w
                width_max = (state['cur_max'] / self.max_scale_value) * graph_w

                # Barra BLU (fino al min)
                self.canvas.create_rectangle(
                    margin_left, y, 
                    margin_left + width_min, y + self.bar_height,
                    fill=self.bar_blue, outline=""
                )

                # Barra ROSSA (dal min al max)
                if width_max > width_min:
                    self.canvas.create_rectangle(
                        margin_left + width_min, y, 
                        margin_left + width_max, y + self.bar_height,
                        fill=self.bar_red, outline=""
                    )
                
                # Etichetta Nome (A sinistra)
                self.canvas.create_text(
                    margin_left - 10, y + self.bar_height/2, 
                    text=name, fill="white", anchor="e", font=self.font_main
                )

                # Etichetta Valori (A destra della barra o dentro se troppo lunga)
                label_text = f"{item['min']:,.2f} - {item['max']:,.2f}€"
                text_x = margin_left + width_max + 10
                self.canvas.create_text(
                    text_x, y + self.bar_height/2,
                    text=label_text, fill="white", anchor="w", font=self.font_small
                )

    def _start_animation_loop(self):
        # 1. Interpola la Scala globale (Zoom in/out fluido)
        self.max_scale_value = self._lerp(self.max_scale_value, self.target_max_scale, 0.05)
        
        # 2. Disegna frame
        self._draw()

        # 3. Richiama loop (circa 60 FPS -> 16ms)
        self.root.after(16, self._start_animation_loop)

def clean_price(price_str):
    """Converte stringhe come '1.586€' o '1,20' in float puri"""
    # Rimuovi simbolo euro e spazi
    s = price_str.replace("€", "").strip()
    # Gestione separatori: se c'è la virgola e nessun punto, è decimale.
    # Se ci sono punti e virgole, assumiamo standard italiano (punto migliaia, virgola decimali)
    if "," in s and "." in s:
        s = s.replace(".", "") # Rimuovi migliaia
        s = s.replace(",", ".") # Virgola diventa punto
    elif "," in s:
        s = s.replace(",", ".")
    
    try:
        return float(s)
    except ValueError:
        return 0.0

def load_data(filename):
    data = []
    try:
        with open(filename, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader, None) # Salta header se esiste (opzionale, qui assumiamo formato grezzo o gestito)
            
            for row in reader:
                if len(row) >= 3:
                    # Se la prima riga è l'intestazione, saltala controllando se il prezzo è numerico
                    try:
                        p_min = clean_price(row[1])
                        p_max = clean_price(row[2])
                        data.append({
                            'nome': row[0].strip(),
                            'min': p_min,
                            'max': p_max
                        })
                    except:
                        continue
    except FileNotFoundError:
        messagebox.showerror("Errore", f"File {filename} non trovato!")
        return []
    return data

if __name__ == "__main__":
    # --- CREAZIONE FILE CSV DI ESEMPIO SE NON ESISTE ---
    import os
    if not os.path.exists("prodotti.csv"):
        with open("prodotti.csv", "w", encoding="utf-8") as f:
            f.write("Prodotto;Prezzo Min;Prezzo Max\n")
            f.write("Acqua (Bottiglia);0,20€;1,50€\n")
            f.write("Latte;0,90€;2,20€\n")
            f.write("Benzina;1,586€;2,158€\n")
            f.write("Birra Artigianale;1,8€;10€\n")
            f.write("Olio d'oliva;8,00€;15,50€\n")
            f.write("Vino pregiato;15€;85€\n")
            f.write("Profumo (Chanel);120€;180€\n")
            f.write("Inchiostro Stampante;500€;800€\n")
            f.write("Collirio;750€;1000€\n")
            f.write("Veleno Scorpione;8000€;12000€\n")

    root = tk.Tk()
    data = load_data("prodotti.csv")
    if data:
        app = PriceComparatorApp(root, data)
        root.mainloop()