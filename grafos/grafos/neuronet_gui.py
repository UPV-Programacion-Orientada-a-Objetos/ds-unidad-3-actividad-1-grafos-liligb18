#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NeuroNet - Sistema de Análisis y Visualización de Grafos Masivos
Interfaz Gráfica de Usuario
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os
import sys
import threading
import time

try:
    import neuronet_core
    CORE_DISPONIBLE = True
except ImportError:
    CORE_DISPONIBLE = False
    print("ADVERTENCIA: El módulo neuronet_core no está compilado.")
    print("Ejecute: python setup.py build_ext --inplace")


class NeuroNetGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NeuroNet - Análisis de Grafos Masivos")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e2e')
        
        # Variable para el grafo
        self.grafo = None
        if CORE_DISPONIBLE:
            self.grafo = neuronet_core.PyGrafoDisperso()
        
        # Datos del grafo cargado
        self.archivo_actual = None
        self.nodos_bfs = []
        self.aristas_bfs = []
        
        self._crear_interfaz()
    
    def _crear_interfaz(self):
        """Crea la interfaz principal"""
        
        # === COLORES DEL TEMA ===
        self.colors = {
            'bg_main': '#1e1e1e',       # Fondo principal (muy oscuro)
            'bg_panel': '#252526',      # Paneles (gris oscuro)
            'bg_input': '#3c3c3c',      # Entradas de texto
            'accent': '#007acc',        # Azul brillante (tipo VS Code)
            'accent_hover': '#0098ff',  # Azul más claro para hover
            'text_main': '#ffffff',     # Texto principal
            'text_sec': '#cccccc',      # Texto secundario
            'success': '#4ec9b0',       # Verde suave
            'warning': '#ce9178',       # Naranja/Rojizo
            'error': '#f44747'          # Rojo
        }

        self.root.configure(bg=self.colors['bg_main'])

        # === PANEL SUPERIOR: TÍTULO ===
        frame_titulo = tk.Frame(self.root, bg=self.colors['bg_panel'], height=80)
        frame_titulo.pack(fill=tk.X, pady=(0, 2)) # Pequeño borde separador
        
        titulo = tk.Label(
            frame_titulo,
            text="🧠 NeuroNet",
            font=('Segoe UI', 28, 'bold'),
            bg=self.colors['bg_panel'],
            fg=self.colors['accent']
        )
        titulo.pack(pady=(10, 0))
        
        subtitulo = tk.Label(
            frame_titulo,
            text="Análisis y Visualización de Propagación en Redes Masivas",
            font=('Segoe UI', 11),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_sec']
        )
        subtitulo.pack(pady=(0, 10))
        
        # === PANEL PRINCIPAL: DIVIDIDO EN IZQUIERDA Y DERECHA ===
        panel_principal = tk.Frame(self.root, bg=self.colors['bg_main'])
        panel_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- PANEL IZQUIERDO: CONTROLES ---
        panel_izquierdo = tk.Frame(panel_principal, bg=self.colors['bg_panel'], width=380)
        panel_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        panel_izquierdo.pack_propagate(False)
        
        # Sección 1: Carga de Datos
        self._crear_seccion_carga(panel_izquierdo)
        
        # Sección 2: Estadísticas
        self._crear_seccion_estadisticas(panel_izquierdo)
        
        # Sección 3: Análisis
        self._crear_seccion_analisis(panel_izquierdo)
        
        # Sección 4: Barra de Progreso
        self._crear_seccion_progreso(panel_izquierdo)
        
        # Sección 5: Consola de Logs
        self._crear_consola_logs(panel_izquierdo)
        
        # --- PANEL DERECHO: VISUALIZACIÓN ---
        panel_derecho = tk.Frame(panel_principal, bg=self.colors['bg_panel'])
        panel_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self._crear_panel_visualizacion(panel_derecho)
    
    def _crear_seccion_carga(self, parent):
        """Sección para cargar datasets"""
        frame = tk.LabelFrame(
            parent,
            text=" Carga de Dataset ",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_main'],
            bd=1,
            relief=tk.SOLID,
            padx=15,
            pady=15
        )
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Botón cargar archivo
        btn_cargar = tk.Button(
            frame,
            text="📂 Seleccionar Archivo .txt",
            font=('Segoe UI', 10),
            bg=self.colors['accent'],
            fg='white',
            activebackground=self.colors['accent_hover'],
            activeforeground='white',
            cursor='hand2',
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=self.cargar_dataset
        )
        btn_cargar.pack(fill=tk.X)
        
        # Label para mostrar archivo actual
        self.lbl_archivo = tk.Label(
            frame,
            text="Ningún archivo cargado",
            font=('Segoe UI', 9, 'italic'),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_sec'],
            wraplength=320,
            justify=tk.LEFT
        )
        self.lbl_archivo.pack(pady=(10, 0))
    
    def _crear_seccion_estadisticas(self, parent):
        """Sección para mostrar estadísticas del grafo"""
        frame = tk.LabelFrame(
            parent,
            text=" Estadísticas ",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_main'],
            bd=1,
            relief=tk.SOLID,
            padx=15,
            pady=15
        )
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Helper para crear filas de stats
        def crear_fila(label, valor_inicial):
            f = tk.Frame(frame, bg=self.colors['bg_panel'])
            f.pack(fill=tk.X, pady=2)
            tk.Label(f, text=label, font=('Segoe UI', 9), bg=self.colors['bg_panel'], fg=self.colors['text_sec']).pack(side=tk.LEFT)
            lbl = tk.Label(f, text=valor_inicial, font=('Segoe UI', 9, 'bold'), bg=self.colors['bg_panel'], fg=self.colors['success'])
            lbl.pack(side=tk.RIGHT)
            return lbl

        self.lbl_nodos = crear_fila("Nodos:", "0")
        self.lbl_aristas = crear_fila("Aristas:", "0")
        self.lbl_memoria = crear_fila("Memoria:", "0 MB")
        self.lbl_max_grado = crear_fila("Max Grado:", "N/A")
    
    def _crear_seccion_analisis(self, parent):
        """Sección para realizar análisis BFS"""
        frame = tk.LabelFrame(
            parent,
            text=" Análisis BFS ",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_main'],
            bd=1,
            relief=tk.SOLID,
            padx=15,
            pady=15
        )
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Grid layout para inputs
        frame_inputs = tk.Frame(frame, bg=self.colors['bg_panel'])
        frame_inputs.pack(fill=tk.X)
        
        # Nodo de inicio
        tk.Label(frame_inputs, text="Nodo Inicio:", font=('Segoe UI', 9), bg=self.colors['bg_panel'], fg=self.colors['text_sec']).grid(row=0, column=0, sticky='w', pady=5)
        self.entry_nodo_inicio = tk.Entry(frame_inputs, font=('Segoe UI', 10), bg=self.colors['bg_input'], fg='white', insertbackground='white', relief=tk.FLAT)
        self.entry_nodo_inicio.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        # Profundidad
        tk.Label(frame_inputs, text="Profundidad:", font=('Segoe UI', 9), bg=self.colors['bg_panel'], fg=self.colors['text_sec']).grid(row=1, column=0, sticky='w', pady=5)
        self.entry_profundidad = tk.Entry(frame_inputs, font=('Segoe UI', 10), bg=self.colors['bg_input'], fg='white', insertbackground='white', relief=tk.FLAT)
        self.entry_profundidad.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=5)
        self.entry_profundidad.insert(0, "2")
        
        frame_inputs.columnconfigure(1, weight=1)
        
        # Botón ejecutar BFS
        btn_bfs = tk.Button(
            frame,
            text="▶ Ejecutar Análisis",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['success'],
            fg='#1e1e2e',
            activebackground='#3aa995',
            activeforeground='#1e1e2e',
            cursor='hand2',
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=self.ejecutar_bfs
        )
        btn_bfs.pack(fill=tk.X, pady=(15, 0))
    
    def _crear_seccion_progreso(self, parent):
        """Sección para mostrar progreso de operaciones"""
        frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Label de estado
        self.lbl_estado = tk.Label(
            frame,
            text="Listo",
            font=('Segoe UI', 9),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_sec'],
            wraplength=350,
            justify=tk.LEFT
        )
        self.lbl_estado.pack(anchor='w', pady=(0, 5))
        
        # Barra de progreso
        self.progress_bar = ttk.Progressbar(
            frame,
            mode='indeterminate',
            length=350
        )
        self.progress_bar.pack(fill=tk.X)
        
        # Configurar estilo de la barra
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "TProgressbar",
            thickness=10,
            troughcolor=self.colors['bg_input'],
            background=self.colors['accent'],
            bordercolor=self.colors['bg_panel']
        )
    
    def _crear_consola_logs(self, parent):
        """Consola para mostrar logs"""
        frame = tk.LabelFrame(
            parent,
            text=" Logs ",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_main'],
            bd=1,
            relief=tk.SOLID,
            padx=5,
            pady=5
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.consola = scrolledtext.ScrolledText(
            frame,
            font=('Consolas', 9),
            bg='#1e1e1e', # Un poco más oscuro que el panel
            fg='#d4d4d4',
            insertbackground='white',
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=5,
            pady=5
        )
        self.consola.pack(fill=tk.BOTH, expand=True)
        
        # Redireccionar stdout a la consola
        sys.stdout = TextRedirector(self.consola, "stdout")
    
    def _crear_panel_visualizacion(self, parent):
        """Panel para visualizar el grafo"""
        # Header del panel derecho
        header = tk.Frame(parent, bg=self.colors['bg_panel'])
        header.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            header,
            text="Visualización",
            font=('Segoe UI', 14),
            bg=self.colors['bg_panel'],
            fg=self.colors['text_main']
        ).pack(side=tk.LEFT)
        
        # Frame para el canvas de matplotlib
        self.frame_canvas = tk.Frame(parent, bg=self.colors['bg_main'])
        self.frame_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Crear figura inicial
        self._crear_figura_vacia()
    
    def _crear_figura_vacia(self):
        """Crea una figura vacía de matplotlib con herramientas de navegación"""
        self.figura = Figure(figsize=(10, 8), facecolor=self.colors['bg_main'])
        self.ax = self.figura.add_subplot(111)
        self.ax.set_facecolor(self.colors['bg_main'])
        self.ax.text(
            0.5, 0.5,
            'Cargue un dataset y ejecute BFS\npara visualizar el subgrafo',
            horizontalalignment='center',
            verticalalignment='center',
            transform=self.ax.transAxes,
            fontsize=12,
            color=self.colors['text_sec']
        )
        self.ax.axis('off')
        
        # Canvas de tkinter
        self.canvas = FigureCanvasTkAgg(self.figura, self.frame_canvas)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Barra de herramientas de navegación (Zoom, Pan, Guardar)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame_canvas)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Configurar colores de la toolbar
        self.toolbar.config(background=self.colors['bg_panel'])
        for button in self.toolbar.winfo_children():
            button.config(background=self.colors['bg_panel'])
            
        # Conectar evento de scroll para zoom con rueda del ratón
        self.canvas.mpl_connect('scroll_event', self._on_scroll)

    def _on_scroll(self, event):
        """Maneja el zoom con la rueda del ratón"""
        ax = self.ax
        if event.inaxes != ax:
            return
            
        # Factor de escala
        base_scale = 1.1
        if event.button == 'up':
            # Zoom in
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            # Zoom out
            scale_factor = base_scale
        else:
            scale_factor = 1
            
        # Obtener límites actuales
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        
        # Posición del ratón
        xdata = event.xdata
        ydata = event.ydata
        
        # Calcular nuevos límites manteniendo el punto del ratón fijo
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        
        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
        
        ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])
        
        self.canvas.draw()

    def cargar_dataset(self):
        """Abre diálogo para cargar un dataset"""
        if not CORE_DISPONIBLE:
            messagebox.showerror(
                "Error",
                "El módulo neuronet_core no está disponible.\nCompile el proyecto primero."
            )
            return
        
        archivo = filedialog.askopenfilename(
            title="Seleccionar Dataset",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if archivo:
            self.archivo_actual = archivo
            nombre_archivo = os.path.basename(archivo)
            self.lbl_archivo.config(text=f"📄 {nombre_archivo}")
            
            # Usar threading para no bloquear la GUI
            def cargar_en_background():
                try:
                    # Actualizar estado
                    self._actualizar_estado(f"🔄 Cargando {nombre_archivo}...", progreso=True)
                    
                    print(f"\n{'='*60}")
                    print(f"Cargando archivo: {archivo}")
                    print(f"{'='*60}\n")
                    
                    # Cargar en el grafo C++
                    self.grafo.cargar_datos(archivo)
                    
                    # Actualizar estado
                    self._actualizar_estado("📊 Calculando estadísticas...", progreso=True)
                    
                    # Actualizar estadísticas
                    self._actualizar_estadisticas()
                    
                    print("\n✅ Carga completada exitosamente\n")
                    
                    # Terminar progreso
                    self._actualizar_estado(f"✅ {nombre_archivo} cargado correctamente", progreso=False)
                    
                except Exception as e:
                    self._actualizar_estado(f"❌ Error al cargar archivo", progreso=False)
                    messagebox.showerror("Error", f"Error al cargar el dataset:\n{str(e)}")
                    print(f"❌ Error: {str(e)}")
            
            # Ejecutar en thread separado
            thread = threading.Thread(target=cargar_en_background, daemon=True)
            thread.start()
    
    def _actualizar_estadisticas(self):
        """Actualiza las estadísticas mostradas en la GUI"""
        if not CORE_DISPONIBLE or self.grafo is None:
            return
        
        try:
            num_nodos = self.grafo.obtener_num_nodos()
            num_aristas = self.grafo.obtener_num_aristas()
            memoria = self.grafo.obtener_memoria_estimada()
            nodo_max, grado_max = self.grafo.obtener_nodo_max_grado()
            
            self.lbl_nodos.config(text=f"{num_nodos:,}")
            self.lbl_aristas.config(text=f"{num_aristas:,}")
            self.lbl_memoria.config(text=f"{memoria / (1024 * 1024):.2f} MB")
            self.lbl_max_grado.config(text=f"Nodo {nodo_max} (grado: {grado_max})")
            
        except Exception as e:
            print(f"Error al actualizar estadísticas: {str(e)}")
    
    def ejecutar_bfs(self):
        """Ejecuta el algoritmo BFS y visualiza el resultado"""
        if not CORE_DISPONIBLE or self.grafo is None:
            messagebox.showwarning(
                "Advertencia",
                "Debe cargar un dataset primero"
            )
            return
        
        try:
            nodo_inicio = int(self.entry_nodo_inicio.get())
            profundidad = int(self.entry_profundidad.get())
            
            if profundidad < 1:
                raise ValueError("La profundidad debe ser mayor a 0")
            
            # Usar threading para no bloquear la GUI
            def ejecutar_en_background():
                try:
                    # Fase 1: Ejecutar BFS
                    self._actualizar_estado(
                        f"🔍 Ejecutando BFS desde nodo {nodo_inicio} (prof. {profundidad})...",
                        progreso=True
                    )
                    
                    print(f"\n{'='*60}")
                    print(f"Iniciando BFS desde nodo {nodo_inicio} con profundidad {profundidad}")
                    print(f"{'='*60}\n")
                    
                    # Ejecutar BFS en C++
                    self.nodos_bfs = self.grafo.bfs(nodo_inicio, profundidad)
                    
                    if not self.nodos_bfs:
                        self._actualizar_estado("❌ No se encontraron nodos", progreso=False)
                        messagebox.showwarning(
                            "Sin resultados",
                            f"No se encontraron nodos desde el nodo {nodo_inicio}"
                        )
                        return
                    
                    # Fase 2: Obtener aristas
                    self._actualizar_estado(
                        f"🔗 Obteniendo aristas del subgrafo ({len(self.nodos_bfs):,} nodos)...",
                        progreso=True
                    )
                    
                    # Obtener aristas del subgrafo
                    self.aristas_bfs = self.grafo.obtener_aristas_subgrafo(self.nodos_bfs)
                    
                    print(f"\n✅ BFS completado. Nodos encontrados: {len(self.nodos_bfs)}")
                    print(f"   Aristas en el subgrafo: {len(self.aristas_bfs)}\n")
                    
                    # Fase 3: Visualizar
                    self._actualizar_estado(
                        f"📊 Generando visualización ({len(self.nodos_bfs):,} nodos)...",
                        progreso=True
                    )
                    
                    # Visualizar (esta función actualiza su propio estado)
                    self._visualizar_subgrafo()
                    
                except ValueError as e:
                    self._actualizar_estado("❌ Error de entrada", progreso=False)
                    messagebox.showerror(
                        "Error de Entrada",
                        f"Por favor ingrese valores numéricos válidos:\n{str(e)}"
                    )
                except Exception as e:
                    self._actualizar_estado("❌ Error en BFS", progreso=False)
                    messagebox.showerror(
                        "Error",
                        f"Error al ejecutar BFS:\n{str(e)}"
                    )
                    print(f"❌ Error: {str(e)}")
            
            # Ejecutar en thread separado
            thread = threading.Thread(target=ejecutar_en_background, daemon=True)
            thread.start()
            
        except ValueError:
            self._actualizar_estado("❌ Valores inválidos", progreso=False)
            messagebox.showerror(
                "Error de Entrada",
                "Por favor ingrese valores numéricos válidos"
            )
    
    def _visualizar_subgrafo(self):
        """Visualiza el subgrafo resultante del BFS usando NetworkX"""
        
        num_nodos = len(self.nodos_bfs)
        num_aristas = len(self.aristas_bfs)
        
        # Advertencia para grafos MUY grandes (pero no limita)
        if num_nodos > 10000:
            respuesta = messagebox.askyesno(
                "⚠️ Grafo Masivo Detectado",
                f"El subgrafo tiene {num_nodos:,} nodos y {num_aristas:,} aristas.\n\n"
                "La visualización de grafos tan grandes puede tomar varios minutos "
                "y consumir mucha memoria.\n\n"
                "¿Desea continuar con la visualización?\n\n"
                "Nota: El análisis BFS ya se completó exitosamente.\n"
                "Los resultados están en la consola.",
                icon='warning'
            )
            
            if not respuesta:
                print(f"\n⏭️ Visualización omitida (grafo de {num_nodos:,} nodos)")
                print(f"   El análisis se completó correctamente.\n")
                self._actualizar_estado(
                    f"✅ BFS completo ({num_nodos:,} nodos) - Visualización omitida",
                    progreso=False
                )
                return
        
        # Limpiar figura anterior
        self.figura.clear()
        self.ax = self.figura.add_subplot(111)
        self.ax.set_facecolor(self.colors['bg_main'])
        
        # Mostrar progreso
        print(f"\n⏳ Generando visualización de {num_nodos:,} nodos y {num_aristas:,} aristas...")
        self.root.update()  # Actualizar GUI
        
        # Crear grafo dirigido con NetworkX
        print("   [1/4] Construyendo estructura del grafo...")
        G = nx.DiGraph()
        G.add_nodes_from(self.nodos_bfs)
        G.add_edges_from(self.aristas_bfs)
        
        # Seleccionar algoritmo de layout según tamaño
        print(f"   [2/4] Calculando layout óptimo...")
        
        if num_nodos < 30:
            # Spring layout de alta calidad para grafos pequeños
            print(f"       Usando Spring Layout (alta calidad, lento)")
            pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
        elif num_nodos < 100:
            # Spring layout moderado
            print(f"       Usando Spring Layout (calidad media)")
            pos = nx.spring_layout(G, k=0.4, iterations=30, seed=42)
        elif num_nodos < 500:
            # Spring layout rápido
            print(f"       Usando Spring Layout (rápido)")
            pos = nx.spring_layout(G, k=0.3, iterations=15, seed=42)
        elif num_nodos < 2000:
            # Kamada-Kawai para grafos medianos (más rápido que spring)
            print(f"       Usando Kamada-Kawai Layout (optimizado)")
            try:
                pos = nx.kamada_kawai_layout(G)
            except:
                print(f"       Fallback a Circular Layout")
                pos = nx.circular_layout(G)
        elif num_nodos < 10000:
            # Spectral layout para grafos grandes (muy rápido)
            print(f"       Usando Spectral Layout (muy rápido)")
            try:
                pos = nx.spectral_layout(G)
            except:
                print(f"       Fallback a Circular Layout")
                pos = nx.circular_layout(G)
        else:
            # Circular o Random para grafos masivos (instantáneo)
            print(f"       Usando Circular Layout (instantáneo para {num_nodos:,} nodos)")
            pos = nx.circular_layout(G)
        
        # Identificar nodo de inicio
        nodo_inicio = self.nodos_bfs[0] if self.nodos_bfs else None
        
        # Colores de nodos
        colores_nodos = []
        for nodo in G.nodes():
            if nodo == nodo_inicio:
                colores_nodos.append(self.colors['error'])  # Rojo para nodo inicial
            else:
                colores_nodos.append(self.colors['accent'])  # Azul para otros
        
        # Tamaños adaptativos según cantidad de nodos
        if num_nodos < 30:
            node_size = 400
            edge_width = 2.0
            arrow_size = 15
            font_size = 9
            mostrar_etiquetas = True
        elif num_nodos < 100:
            node_size = 200
            edge_width = 1.5
            arrow_size = 10
            font_size = 7
            mostrar_etiquetas = True
        elif num_nodos < 500:
            node_size = 80
            edge_width = 0.8
            arrow_size = 5
            font_size = 0
            mostrar_etiquetas = False
        elif num_nodos < 2000:
            node_size = 30
            edge_width = 0.4
            arrow_size = 3
            font_size = 0
            mostrar_etiquetas = False
        else:
            # Grafos masivos: nodos muy pequeños
            node_size = 10
            edge_width = 0.2
            arrow_size = 1
            font_size = 0
            mostrar_etiquetas = False
        
        print(f"   [3/4] Renderizando {num_nodos:,} nodos...")
        # Dibujar nodos
        nx.draw_networkx_nodes(
            G, pos,
            node_color=colores_nodos,
            node_size=node_size,
            alpha=0.8,
            linewidths=0,
            ax=self.ax
        )
        
        print(f"   [4/4] Renderizando {num_aristas:,} aristas...")
        # Dibujar aristas
        nx.draw_networkx_edges(
            G, pos,
            edge_color=self.colors['text_sec'],
            width=edge_width,
            alpha=0.3 if num_nodos > 500 else 0.5,
            arrows=num_nodos < 1000,  # Sin flechas para grafos muy grandes
            arrowsize=arrow_size if num_nodos < 1000 else 0,
            ax=self.ax
        )
        
        # Etiquetas solo para grafos pequeños
        if mostrar_etiquetas and num_nodos <= 100:
            print(f"       Agregando etiquetas...")
            nx.draw_networkx_labels(
                G, pos,
                font_size=font_size,
                font_color='white',
                font_weight='bold',
                ax=self.ax
            )
        
        # Título
        self.ax.set_title(
            f'Subgrafo BFS - {num_nodos:,} nodos, {num_aristas:,} aristas',
            color=self.colors['text_main'],
            fontsize=11,
            pad=20,
            weight='bold'
        )
        
        self.ax.axis('off')
        self.figura.tight_layout()
        
        print(f"       Finalizando renderizado...")
        # Actualizar canvas
        self.canvas.draw()
        
        print(f"✅ Visualización completada! ({num_nodos:,} nodos procesados)\n")
        
        # Actualizar estado final
        self._actualizar_estado(
            f"✅ Visualización completa: {num_nodos:,} nodos, {num_aristas:,} aristas",
            progreso=False
        )


class TextRedirector:
    """Redirige la salida de texto a un widget de Tkinter"""
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, texto):
        self.widget.insert(tk.END, texto)
        self.widget.see(tk.END)
    
    def flush(self):
        pass


def main():
    """Función principal"""
    root = tk.Tk()
    app = NeuroNetGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
