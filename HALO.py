import tkinter as tk
import customtkinter as ctk
import requests
import threading
import pyperclip

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class HaloInterfaceStreaming(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("HALO AI - REALTIME STATION")
        self.geometry("1000x740")
        self.minsize(900, 650)

        self.api_url = "http://localhost:5000/chat"
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header = ctk.CTkFrame(self, height=80, fg_color="#0a0e17", corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        self.title_lbl = ctk.CTkLabel(self.header, text="HALO AI", 
                                      font=ctk.CTkFont("Segoe UI", 28, "bold"), text_color="#4cc9f0")
        self.title_lbl.grid(row=0, column=0, pady=(20, 0), padx=40, sticky="w")

        self.sub_lbl = ctk.CTkLabel(self.header, text="Motor Local • Streaming en tiempo real",
                                    font=ctk.CTkFont("Segoe UI", 13), text_color="#8a9ba8")
        self.sub_lbl.grid(row=1, column=0, pady=(0, 15), padx=40, sticky="w")

        self.status = ctk.CTkLabel(self.header, text="● ONLINE", text_color="#06d6a0", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"))
        self.status.grid(row=0, column=1, rowspan=2, padx=40, sticky="e")

        # Chat
        self.chat_canvas = ctk.CTkScrollableFrame(self, fg_color="#0a0e17")
        self.chat_canvas.grid(row=1, column=0, sticky="nsew")
        self.chat_canvas.grid_columnconfigure(0, weight=1)

        self.grid_index = 0

        # Mensaje de bienvenida
        self.crear_globo_fijo("Estación base activada. Flujo continuo sincronizado.\n¿En qué te ayudo hoy, controlador?", de_usuario=False)

        # Input
        self.footer = ctk.CTkFrame(self, fg_color="#0a0e17", height=90)
        self.footer.grid(row=2, column=0, sticky="ew")
        self.footer.grid_columnconfigure(0, weight=1)

        self.input_field = ctk.CTkEntry(self.footer, placeholder_text="Escribe aquí...",
                                        fg_color="#1a2333", border_color="#2a3a5a", 
                                        text_color="#e0e7ff", font=ctk.CTkFont("Segoe UI", 15), height=52)
        self.input_field.grid(row=0, column=0, padx=(40, 15), pady=18, sticky="ew")
        self.input_field.bind("<Return>", lambda e: self.enviar_mensaje())

        self.btn_send = ctk.CTkButton(self.footer, text="ENVIAR", width=140,
                                      font=ctk.CTkFont("Segoe UI", 15, "bold"),
                                      fg_color="#4cc9f0", text_color="#0a0e17",
                                      command=self.enviar_mensaje)
        self.btn_send.grid(row=0, column=1, padx=(0, 40), pady=18)

    def crear_globo_fijo(self, texto, de_usuario=False):
        color = "#1e2a44" if de_usuario else "#13213a"
        padx = (180, 40) if de_usuario else (40, 180)
        sticky = "e" if de_usuario else "w"

        # Burbuja
        bubble = ctk.CTkFrame(self.chat_canvas, fg_color=color, border_width=1, 
                              border_color="#253a5f", corner_radius=16)
        bubble.grid(row=self.grid_index, column=0, padx=padx, pady=(10, 4), sticky=sticky)

        lbl = ctk.CTkLabel(bubble, text=texto, justify="left", wraplength=680,
                           font=ctk.CTkFont("Segoe UI", 15), text_color="#e8f0ff")
        lbl.pack(padx=18, pady=14, anchor="w")

        self.grid_index += 1

        # Botón solo para respuestas de HALO
        if not de_usuario:
            self.agregar_boton_copiar(texto, padx, sticky)

        self.chat_canvas._parent_canvas.yview_moveto(1.0)

    def agregar_boton_copiar(self, texto, padx, sticky):
        btn_frame = ctk.CTkFrame(self.chat_canvas, fg_color="transparent")
        btn_frame.grid(row=self.grid_index, column=0, padx=padx, pady=(0, 12), sticky=sticky)

        btn = ctk.CTkButton(btn_frame, text="📋 Copiar", width=90, height=28,
                            font=ctk.CTkFont("Segoe UI", 12),
                            fg_color="#1f2a44", hover_color="#2a3a5a",
                            command=lambda t=texto: self.copiar_texto(t))
        btn.pack(anchor="e")

        self.grid_index += 1

    def copiar_texto(self, texto):
        try:
            pyperclip.copy(texto)
            print("✅ Copiado")
        except:
            print("❌ Error")

    def enviar_mensaje(self):
        msg = self.input_field.get().strip()
        if not msg: return

        self.input_field.delete(0, tk.END)
        self.crear_globo_fijo(msg, de_usuario=True)

        self.btn_send.configure(state="disabled")
        self.input_field.configure(state="disabled")

        threading.Thread(target=self.procesar_stream, args=(msg,), daemon=True).start()

    def procesar_stream(self, prompt):
        try:
            self.after(0, self.iniciar_globo_stream)

            response = requests.post(self.api_url, json={"prompt": prompt}, stream=True, timeout=120)

            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=128, decode_unicode=True):
                    if chunk:
                        self.after(0, lambda c=chunk: self.actualizar_stream(c))
        except Exception as e:
            self.after(0, lambda: self.actualizar_stream(f"\n[Error: {str(e)}]"))
        finally:
            self.after(0, self.finalizar_stream)

    def iniciar_globo_stream(self):
        self.acumulador_texto = ""
        self.current_stream_frame = ctk.CTkFrame(self.chat_canvas, fg_color="#13213a", 
                                                 border_width=1, border_color="#253a5f", corner_radius=16)
        self.current_stream_frame.grid(row=self.grid_index, column=0, padx=(40, 180), pady=(10, 4), sticky="w")

        self.current_stream_lbl = ctk.CTkLabel(self.current_stream_frame, text="● Pensando...", 
                                               justify="left", wraplength=680,
                                               font=ctk.CTkFont("Segoe UI", 15), text_color="#e8f0ff")
        self.current_stream_lbl.pack(padx=18, pady=14, anchor="w")

        self.grid_index += 1
        self.chat_canvas._parent_canvas.yview_moveto(1.0)

    def actualizar_stream(self, texto):
        if self.current_stream_lbl:
            self.acumulador_texto += texto
            self.current_stream_lbl.configure(text=self.acumulador_texto)
            self.chat_canvas._parent_canvas.yview_moveto(1.0)

    def finalizar_stream(self):
        if self.acumulador_texto:
            self.agregar_boton_copiar(self.acumulador_texto, (40, 180), "w")
        
        self.btn_send.configure(state="normal")
        self.input_field.configure(state="normal")
        self.input_field.focus()

        self.current_stream_lbl = None
        self.current_stream_frame = None

if __name__ == "__main__":
    app = HaloInterfaceStreaming()
    app.mainloop()