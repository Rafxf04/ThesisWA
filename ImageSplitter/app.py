import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

class ManualImageSplitterApp:
    def __init__(self, root):
        """
        Scopo: Inizializza l'applicazione di ritaglio manuale delle immagini.

        Parametri:
        - root (tk.Tk): La finestra principale dell'applicazione Tkinter.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.root = root
        self.root.title("Social Feed Manual Splitter")
        self.root.geometry("550x250")
        
        self.label = tk.Label(
            root, 
            text="Strumento di Ritaglio Manuale Definitivo\n\n1. Seleziona l'immagine.\n2. Scorri l'immagine e CLICCA nei punti esatti in cui dividere i post.\n3. Usa la rotella del mouse per scorrere e i tasti +/- per lo zoom.\n4. Premi il bottone FATTO in alto a destra per ritagliare.", 
            justify=tk.CENTER, 
            pady=15,
            font=("Arial", 11)
        )
        self.label.pack()
        
        self.select_btn = tk.Button(
            root, 
            text="Seleziona Immagine", 
            command=self.select_image, 
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5
        )
        self.select_btn.pack(pady=15)
        
        self.selected_file = None

    def select_image(self):
        """
        Scopo: Gestisce la selezione di un'immagine tramite finestra di dialogo.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp")]
        )
        if not file_path:
            return
            
        self.selected_file = file_path
        self.open_editor()
        
    def open_editor(self):
        """
        Scopo: Apre l'editor per il ritaglio manuale dell'immagine selezionata.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.editor = tk.Toplevel(self.root)
        self.editor.title("Ritaglio Manuale: Clicca per aggiungere/rimuovere linee")
        self.editor.geometry("900x800")
        
        self.scale_factor = 1.0
        self.split_points = []
        self.lines = {}
        
        toolbar = tk.Frame(self.editor, bd=1, relief=tk.RAISED, bg="#f0f0f0")
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(
            toolbar, 
            text="Clicca per inserire/rimuovere linee.", 
            fg="#b30000", 
            bg="#f0f0f0",
            font=("Arial", 10, "bold"),
            justify=tk.LEFT
        ).pack(side=tk.LEFT, padx=10, pady=5)
        
        zoom_frame = tk.Frame(toolbar, bg="#f0f0f0")
        zoom_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Button(zoom_frame, text="Zoom In (+)", command=self.zoom_in, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(zoom_frame, text="Zoom Out (-)", command=self.zoom_out, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        done_btn = tk.Button(
            toolbar, 
            text="FATTO - RITAGLIA ORA", 
            font=("Arial", 12, "bold"), 
            bg="#2196F3", 
            fg="white", 
            command=self.perform_split,
            padx=15,
            pady=5
        )
        done_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        
        frame = tk.Frame(self.editor)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(frame, cursor="crosshair", bg="#333333")
        vbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self.canvas.yview)
        hbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.config(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        try:
            self.original_img = Image.open(self.selected_file).convert("RGB")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aprire l'immagine: {e}")
            self.editor.destroy()
            return
            
        self.img_id = self.canvas.create_image(0, 0, anchor=tk.NW)
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.editor.bind("<MouseWheel>", self.on_mouse_wheel)
        
        self.update_image_view()
        
    def on_mouse_wheel(self, event):
        """
        Scopo: Gestisce lo scorrimento verticale del canvas usando la rotella del mouse.

        Parametri:
        - event (Event): Evento associato al movimento della rotella del mouse.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def zoom_in(self):
        """
        Scopo: Aumenta il fattore di zoom per ingrandire l'immagine nel canvas.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.scale_factor *= 1.25
        self.update_image_view()
        
    def zoom_out(self):
        """
        Scopo: Riduce il fattore di zoom per rimpicciolire l'immagine nel canvas.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.scale_factor *= 0.8
        self.update_image_view()
        
    def update_image_view(self):
        """
        Scopo: Aggiorna l'immagine mostrata nel canvas applicando il livello di zoom attuale.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        new_width = int(self.original_img.width * self.scale_factor)
        new_height = int(self.original_img.height * self.scale_factor)
        
        resized_img = self.original_img.resize((new_width, new_height), Image.Resampling.BILINEAR)
        self.photo = ImageTk.PhotoImage(resized_img)
        
        self.canvas.itemconfig(self.img_id, image=self.photo)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        
        for y_orig in self.lines:
            self.canvas.delete(self.lines[y_orig])
            
        self.lines.clear()
        
        for y_orig in self.split_points:
            self.draw_line(y_orig)
            
    def draw_line(self, y_orig):
        """
        Scopo: Disegna una linea rossa tratteggiata per indicare il punto di taglio sull'immagine.

        Parametri:
        - y_orig (int): Ordinata y del punto di taglio riferita all'immagine originale.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        canvas_y = int(y_orig * self.scale_factor)
        canvas_width = int(self.original_img.width * self.scale_factor)
        line_id = self.canvas.create_line(0, canvas_y, canvas_width, canvas_y, fill="red", width=3, dash=(10, 5))
        self.lines[y_orig] = line_id
        
    def on_click(self, event):
        """
        Scopo: Gestisce il click sull'immagine per inserire un nuovo taglio o rimuoverne uno esistente.

        Parametri:
        - event (Event): L'evento associato al click del mouse.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        canvas_y = int(self.canvas.canvasy(event.y))
        y_orig = int(canvas_y / self.scale_factor)
        tolerance_orig = 20 / self.scale_factor
        
        for existing_y in list(self.split_points):
            if abs(y_orig - existing_y) < tolerance_orig:
                self.split_points.remove(existing_y)
                self.canvas.delete(self.lines[existing_y])
                del self.lines[existing_y]
                return
                
        if y_orig > 0 and y_orig < self.original_img.height:
            self.split_points.append(y_orig)
            self.draw_line(y_orig)
        
    def perform_split(self):
        """
        Scopo: Esegue il ritaglio dell'immagine originale in base ai punti di divisione e salva i file generati.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - IOError, OSError: Nel caso si verifichino errori nel salvare i segmenti di immagine.
        """
        if not self.split_points:
            ans = messagebox.askyesno("Nessun taglio", "Non hai inserito nessuna linea rossa di taglio.\n\nVuoi chiudere l'editor senza salvare nulla?", parent=self.editor)
            if ans:
                self.editor.destroy()
            return
            
        self.split_points.sort()
        
        output_dir = os.path.splitext(self.selected_file)[0] + "_splits"
        os.makedirs(output_dir, exist_ok=True)
        
        boundaries = self.split_points + [self.original_img.height]
        prev_split = 0
        saved_files = []
        
        for idx, split_point in enumerate(boundaries):
            if split_point - prev_split > 10:
                box = (0, prev_split, self.original_img.width, split_point)
                cropped_img = self.original_img.crop(box)
                out_path = os.path.join(output_dir, f"post_{idx+1}.png")
                cropped_img.save(out_path)
                saved_files.append(out_path)
                
            prev_split = split_point
            
        messagebox.showinfo("Finito!", f"Hai ritagliato con successo l'immagine in {len(saved_files)} post!\n\nI file sono salvati in:\n{output_dir}", parent=self.root)
        self.editor.destroy()
        
        try:
            os.startfile(output_dir)
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ManualImageSplitterApp(root)
    root.mainloop()

