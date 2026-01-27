################################################################
###   Interfaz para el control del sistema de dosificación   ###
###   Autor: David Ángeles Rojas                             ###
###   Email: david_angeles@tec.mx                            ###
################################################################

import datetime    #para mostrar fecha y hora
from tkinter import PhotoImage #para importar logos
from PIL import Image, ImageTk #para cambiar tamaño de imagenes (hay que instalar)
from tkinter import ttk #para la barra de progreso
import tkinter as tk

def dosis_fnc (dosis):
    global dosis_seleccionada
    global color_normal
    dosis_seleccionada = dosis

    for d, btn in botones_dosis.items():
        if d == dosis:
            btn.config(bg="green", activebackground="green")
        else:
            btn.config(bg=color_normal,  activebackground=color_normal)

def toggle_iniciar():
        global estado_iniciar, btn_iniciar
        if estado_iniciar == 0:
            btn_iniciar.config(text="DETENER", bg="red", activebackground="red")
            estado_iniciar = 1
        else:
            btn_iniciar.config(text="INICIAR", bg="green", activebackground="green")
            estado_iniciar = 0

def toggle_pausar():
        global estado_pausar, btn_pausar
        if estado_pausar == 0:
            btn_pausar.config(text="REANUDAR", bg="red", activebackground="red")
            estado_pausar = 1
        else:
            btn_pausar.config(text="PAUSAR", bg="green", activebackground="green")
            estado_pausar = 0

def toggle_guardar():
        #global estado_pausar, btn_pausar
        #if estado_pausar == 0:
        #    btn_pausar.config(text="REANUDAR", bg="red", activebackground="red")
        #    estado_pausar = 1
        #else:
        #    btn_pausar.config(text="PAUSAR", bg="green", activebackground="green")
            estado_pausar = 0

def cambiar_mililitros():
    global mililitros_dosis, lbl_mililitros, root
    
    # Crear ventana de teclado numérico
    ventana_teclado = tk.Toplevel(root)
    ventana_teclado.title("Ingrese Mililitros")
    ventana_teclado.geometry("300x400")
    ventana_teclado.configure(bg="#b3e0ff")
    ventana_teclado.resizable(False, False)
    
    # Variable para almacenar la entrada
    entrada_valor = tk.StringVar(value=str(mililitros_dosis))
    
    # Frame para mostrar el valor actual
    frame_display = tk.Frame(ventana_teclado, bg="#80CBFF", bd=2, relief="sunken")
    frame_display.pack(fill="x", padx=5, pady=5)
    
    lbl_display = tk.Label(frame_display, textvariable=entrada_valor, 
                           font=("Arial", 32, "bold"), bg="#80CBFF", fg="black")
    lbl_display.pack(pady=10)
    
    lbl_unidad = tk.Label(frame_display, text="mL", font=("Arial", 16), bg="#80CBFF", fg="black")
    lbl_unidad.pack(pady=5)
    
    # Frame para los botones numéricos
    frame_botones = tk.Frame(ventana_teclado, bg="#b3e0ff")
    frame_botones.pack(padx=5, pady=5, expand=True, fill="both")
    
    def agregar_digito(digito):
        if entrada_valor.get() == "0":
            entrada_valor.set(str(digito))
        else:
            entrada_valor.set(entrada_valor.get() + str(digito))
    
    def agregar_punto():
        if "." not in entrada_valor.get():
            entrada_valor.set(entrada_valor.get() + ".")
    
    def eliminar():
        valor = entrada_valor.get()
        if len(valor) > 0:
            entrada_valor.set(valor[:-1])
        if entrada_valor.get() == "":
            entrada_valor.set("0")
    
    def aceptar():
        global mililitros_dosis
        try:
            nuevo_valor = float(entrada_valor.get())
            if 0 <= nuevo_valor <= 1000:
                mililitros_dosis = nuevo_valor
                lbl_mililitros.config(text=f"{mililitros_dosis:.1f} mL")
                ventana_teclado.destroy()
            else:
                entrada_valor.set("Valor inválido")
        except:
            entrada_valor.set("Error")
    
    # Crear botones numéricos (3 columnas, 4 filas)
    botones_numeros = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        [0, ".", "DEL"]
    ]
    
    for fila_idx, fila in enumerate(botones_numeros):
        for col_idx, valor in enumerate(fila):
            if valor == "DEL":
                btn = tk.Button(frame_botones, text="DEL", font=("Arial", 14, "bold"),
                               bg="#FF6B6B", fg="white", activebackground="#FF5252",
                               command=eliminar)
            elif valor == ".":
                btn = tk.Button(frame_botones, text=".", font=("Arial", 14, "bold"),
                               bg="#FFB74D", fg="white", activebackground="#FFA726",
                               command=agregar_punto)
            else:
                btn = tk.Button(frame_botones, text=str(valor), font=("Arial", 18, "bold"),
                               bg="#4CAF50", fg="white", activebackground="#45a049",
                               command=lambda v=valor: agregar_digito(v))
            
            btn.grid(row=fila_idx, column=col_idx, sticky="nsew", padx=1, pady=1)
    
    # Configurar el peso de las filas y columnas
    for i in range(4):
        frame_botones.grid_rowconfigure(i, weight=1)
    for i in range(3):
        frame_botones.grid_columnconfigure(i, weight=1)
    
    # Botón ACEPTAR debajo de los números
    btn_aceptar = tk.Button(ventana_teclado, text="✓ ACEPTAR", font=("Arial", 16, "bold"),
                            bg="#00AA00", fg="white", activebackground="#009900",
                            command=aceptar, height=1)
    btn_aceptar.pack(fill="x", padx=1, pady=1)

def agregar_log(num_rec, temp_log, ph_log):
    global txt_log
    from datetime import datetime
    ahora = datetime.now().strftime("%H:%M:%S")
    linea = f"{ahora} | Recipiente: {num_rec} | Temp: {temp_log}°C | pH: {ph_log}\n"
    txt_log.config(state="normal")
    txt_log.insert("end", linea)
    txt_log.see("end")  # Desplaza el scroll al final
    txt_log.config(state="disabled")


def date_time(lbl_fecha_hora):
    ahora = datetime.datetime.now()
    lbl_fecha_hora.config(text=ahora.strftime("%d/%m/%Y %H:%M:%S"))
    lbl_fecha_hora.after(1000, lambda: date_time(lbl_fecha_hora))




def main():
    global botones_dosis, color_normal, dosis_seleccionada, estado_iniciar, btn_iniciar
    global estado_pausar, btn_pausar
    global txt_log, mililitros_dosis, lbl_mililitros, root
    dosis_seleccionada = None
    estado_iniciar = 0   #para indicar si esta en ejecución la tarea
    estado_pausar = 0   #para indicar si esta en ejecución la tarea
    mililitros_dosis = 10.0  #valor inicial en mililitros


    root = tk.Tk()
    root.title("DOSIFICADOR DE ESPIRULINA AUTOMÁTICO TEC-IPN")

    width, height = 800, 480
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = int((screen_w - width) / 2)
    y = int((screen_h - height) / 2)

    root.geometry(f"{width}x{height}+{x}+{y}")

    root.resizable(True, True)

    root.bind("<Escape>", lambda e: root.destroy())

    ######### paleta de colores ##########
    azul = "#b3e0ff"  # color de fondo
    azul_1 = "#80CBFF"  # otro color paleta colores
    aqua = "#B3FFF8" #otro color paleta colores
    moradito = "#B3BAFF" #otro color paleta colores
    verdecito = "#BAFFB3" #otro color paleta colores
    root.configure(bg=azul)

    ########## Frame para el baner ##########
    frame_banner = tk.Frame(root, bg="white")
    frame_banner.place(relx=0.0, rely=0.0, anchor="nw", width=400, height=40)

    lbl_banner = tk.Label(frame_banner, text="DOSIFICADOR DE ESPIRULINA TEC-IPN", \
                             font=("Arial", 15), bg=azul, fg="black")
    lbl_banner.pack(fill="both", expand=True)

    ########## Frame para indicador de conexión ##########

    # Cargar y ajustar el icono
    img_conectado = Image.open("icons/arduino_connected.png").resize((40, 40)) #tamaño en pix
    icono_conectado = ImageTk.PhotoImage(img_conectado)

    img_desconectado = Image.open("icons/arduino_disconnected.png").resize((24, 24))
    icono_desconectado = ImageTk.PhotoImage(img_desconectado)

    frame_conectado = tk.Frame(root, bg="white")
    frame_conectado.place(relx=0.53, rely=0.0, anchor="nw", width=200, height=40)

    conectado_arduino = True

    if conectado_arduino:
        lbl_conectado = tk.Label(frame_conectado, image=icono_conectado, bg=azul)
        lbl_conectado.pack(side="left", padx=0, pady=0)

        lbl_conectado = tk.Label(frame_conectado, text="CONECTADO", font=("Arial", 15), bg=azul, fg="black")
        lbl_conectado.pack(fill="both", expand=True)
    else:
        lbl_conectado = tk.Label(frame_conectado, image=icono_desconectado, bg=azul)
        lbl_conectado.pack(side="left", padx=0, pady=0)

        lbl_conectado = tk.Label(frame_conectado, text="DESCONECTADO", font=("Arial", 15), bg=azul, fg="black")
        lbl_conectado.pack(fill="both", expand=True)

    ########## Frame para la fecha y hora ##########
    frame_fecha_hora = tk.Frame(root, bg="white")
    frame_fecha_hora.place(relx=1.0, rely=0.0, anchor="ne", width=150, height=40)

    lbl_fecha_hora = tk.Label(frame_fecha_hora, font=("Arial", 12), bg=azul, fg="black")
    lbl_fecha_hora.pack(fill="both", expand=True)
    date_time(lbl_fecha_hora)

    ########## Frame recipientes a dosificar ##########
    frame_dosificacion = tk.Frame(root, bg=azul)
    frame_dosificacion.place(relx=0.01, rely=0.1, anchor="nw", width=520, height=270)

    lbl_dosificacion = tk.Label(frame_dosificacion, text="Recipientes a dosificar", \
                          font=("Arial", 15), bg=azul_1, fg="black")
    lbl_dosificacion.place(relx=0.05, rely=0.0, anchor="nw", width=230, height=40)

    num_recipientes = 999   #numero de recipientes a dosificar
    lbl_num_recipientes = tk.Label(frame_dosificacion, text=str(num_recipientes), font=("Arial", 80, "bold"), bg=azul_1)
    lbl_num_recipientes.place(relx=0.05, rely=0.14, anchor="nw", width=230, height=100)

    # Para actualizar el número en cualquier parte del código:
    # lbl_num_recipientes.config(text=str(nuevo_valor))

    lbl_dosificacion = tk.Label(frame_dosificacion, text="Dosificados", \
                          font=("Arial", 15), bg=azul_1, fg="black")
    lbl_dosificacion.place(relx=0.55, rely=0.0, anchor="nw", width=230, height=40)

    num_recipientes_dosificados = 600   #numero de recipientes dosificados
    lbl_num_recipientes = tk.Label(frame_dosificacion, text=str(num_recipientes_dosificados), font=("Arial", 80, "bold"), bg=azul_1)
    lbl_num_recipientes.place(relx=0.55, rely=0.14, anchor="nw", width=230, height=100)

    # barra de progreso
    progress = ttk.Progressbar(frame_dosificacion, length=200, maximum=num_recipientes)
    progress.place(relx=0.1, rely=0.53, anchor="nw", width=440, height=30)
    progress['value'] = num_recipientes_dosificados

    estado = 2

    match estado:
        case 1:
            lbl_dosificacion = tk.Label(frame_dosificacion, text="ACTIVO", \
                          font=("Arial", 24), bg=moradito, fg="black")
            lbl_dosificacion.place(relx=0.1, rely=0.65, anchor="nw", width=230, height=40)
        case 2:
            lbl_dosificacion = tk.Label(frame_dosificacion, text="INACTIVO", \
                          font=("Arial", 24), bg=moradito, fg="black")
            lbl_dosificacion.place(relx=0.1, rely=0.65, anchor="nw", width=230, height=40)
        case 3:
            lbl_dosificacion = tk.Label(frame_dosificacion, text="EN PAUSA", \
                          font=("Arial", 24), bg=moradito, fg="black")
            lbl_dosificacion.place(relx=0.1, rely=0.65, anchor="nw", width=230, height=40)

    # indicador mililitros a dosificar
    lbl_mililitros = tk.Button(frame_dosificacion, text=f"{mililitros_dosis:.1f} mL", 
                               font=("Arial", 20, "bold"), bg=verdecito, fg="black",
                               activebackground=verdecito, activeforeground="black",
                               command=cambiar_mililitros, relief="raised", bd=3)
    lbl_mililitros.place(relx=0.55, rely=0.65, anchor="nw", width=207, height=40)


    # boton iniciar/detener
    btn_iniciar = tk.Button(frame_dosificacion, text="INICIAR", font=("Arial", 15, "bold"),
                            width=10, height=2, bg="green", fg="white",
                            activebackground="green", activeforeground="white",
                            command=toggle_iniciar)
    btn_iniciar.place(relx=0.2, rely=0.97, anchor="s", width=150, height=40)

    # boton pausar/reanudar
    btn_pausar = tk.Button(frame_dosificacion, text="PAUSAR", font=("Arial", 15, "bold"),
                            width=10, height=2, bg="green", fg="white",
                            activebackground="green", activeforeground="white",
                            command=toggle_pausar)
    btn_pausar.place(relx=0.495, rely=0.97, anchor="s", width=130, height=40)

    # boton guardar
    btn_guardar = tk.Button(frame_dosificacion, text="GUARDAR DATOS", font=("Arial", 15, "bold"),
                            width=10, height=2, bg="green", fg="white",
                            activebackground="green", activeforeground="white",
                            command=toggle_guardar)
    btn_guardar.place(relx=0.82, rely=0.97, anchor="s", width=180, height=40)
    ##########################################################################


    ########### HISTORIAL ##########
    frame_historial = tk.Frame(root, bg="white")
    frame_historial.place(relx=0.04, rely=0.67, anchor="nw", width=495, height=140)

    lbl_hist = tk.Label(frame_historial, text="Historial", \
                          font=("Arial", 14), bg=azul_1, fg="black")
    lbl_hist.place(relx=0.0, rely=0.0, anchor="nw", width=495, height=25)

    # Crear el widget Text para el log
    txt_log = tk.Text(frame_historial, font=("Consolas", 12), bg="white", fg="black", state="disabled")
    #txt_log.pack(fill="both", expand=True)
    txt_log.place(relx=0.0, rely=0.182, anchor="nw", width=495, height=115)

    agregar_log(1, 23.4, 7.1)
    agregar_log(2, 23.5, 7.2)

    ########### DATOS DE TELEMETRIA ###########
    frame_telemetria = tk.Frame(root, bg=azul, bd=2, relief="groove")
    frame_telemetria.place(relx=0.675, rely=0.1, anchor="nw", width=250, height=260)

    lbl_tele = tk.Label(frame_telemetria, text="Telemetría", \
                          font=("Arial", 24), bg=azul_1, fg="black")
    lbl_tele.place(relx=0.0, rely=0.0, anchor="nw", width=245, height=40)

    lbl_temp = tk.Label(frame_telemetria, text="Temperatura", font=("Arial", 14), bg=moradito)
    lbl_temp.place(relx=0.0, rely=0.158, anchor="nw", width=122, height=41)

    temp_0 = 20.4   #temperatura para mostrar
    lbl_temp_show = tk.Label(frame_telemetria, text=f"{temp_0} °C", font=("Arial", 25, "bold"), bg=moradito)
    lbl_temp_show.place(relx=0.0, rely=0.315, anchor="nw", width=122, height=51)

    lbl_ph = tk.Label(frame_telemetria, text="pH", font=("Arial", 14), bg=moradito)
    lbl_ph.place(relx=0.5, rely=0.158, anchor="nw", width=122, height=41)

    pH_0 = 7.1   #pH para mostrar
    lbl_pH_show = tk.Label(frame_telemetria, text=str(pH_0), font=("Arial", 25, "bold"), bg=moradito)
    lbl_pH_show.place(relx=0.5, rely=0.315, anchor="nw", width=122, height=51)

    dosis_1 = 0.5
    lbl_dosis_1 = tk.Label(frame_telemetria, text=f"{dosis_1} %", font=("Arial", 14), bg=moradito)
    lbl_dosis_1.place(relx=0.0, rely=0.52, anchor="nw", width=80, height=41)

    temp_1 = 22.3
    lbl_temp_1 = tk.Label(frame_telemetria, text=f"{temp_1} °C", font=("Arial", 14), bg=moradito)
    lbl_temp_1.place(relx=0.0, rely=0.68, anchor="nw", width=80, height=41)

    pH_1 = 5.1
    lbl_pH_1 = tk.Label(frame_telemetria, text=f"pH {pH_1}", font=("Arial", 14), bg=moradito)
    lbl_pH_1.place(relx=0.0, rely=0.84, anchor="nw", width=80, height=40)

    dosis_2 = 1
    lbl_dosis_2 = tk.Label(frame_telemetria, text=f"{dosis_2} %", font=("Arial", 14), bg=moradito)
    lbl_dosis_2.place(relx=0.33, rely=0.52, anchor="nw", width=80, height=41)

    temp_2 = 23.4
    lbl_temp_2 = tk.Label(frame_telemetria, text=f"{temp_2} °C", font=("Arial", 14), bg=moradito)
    lbl_temp_2.place(relx=0.33, rely=0.68, anchor="nw", width=80, height=41)

    pH_2 = 6.2
    lbl_pH_2 = tk.Label(frame_telemetria, text=f"pH {pH_2}", font=("Arial", 14), bg=moradito)
    lbl_pH_2.place(relx=0.33, rely=0.84, anchor="nw", width=80, height=40)

    dosis_3 = 1.5
    lbl_dosis_3 = tk.Label(frame_telemetria, text=f"{dosis_3} %", font=("Arial", 14), bg=moradito)
    lbl_dosis_3.place(relx=0.66, rely=0.52, anchor="nw", width=83, height=41)

    temp_3 = 24.4
    lbl_temp_3 = tk.Label(frame_telemetria, text=f"{temp_3} °C", font=("Arial", 14), bg=moradito)
    lbl_temp_3.place(relx=0.66, rely=0.68, anchor="nw", width=83, height=41)

    pH_3 = 7.3
    lbl_pH_3 = tk.Label(frame_telemetria, text=f"pH {pH_3}", font=("Arial", 14), bg=moradito)
    lbl_pH_3.place(relx=0.66, rely=0.84, anchor="nw", width=83, height=40)


    ##########################################################################

    frame_dosis = tk.Frame(root, bg="white", bd=2, relief="groove")
    frame_dosis.place(relx=0.675, rely=0.65, anchor="nw", width=250, height=150)
    #frame_dosis.pack(expand=True)
    
    lbl_dosis_titulo = tk.Label(frame_dosis, text="Dosis", font=("Arial", 24), bg=azul_1)
    lbl_dosis_titulo.place(relx=0.0, rely=0.0, anchor="nw", width=245, height=40)
    #lbl_dosis_titulo.grid(row=0, column=0, columnspan=2, pady=(10, 10))

    frame_dosis_lista = tk.Frame(frame_dosis, bg=moradito)
    frame_dosis_lista.place(relx=0.0, rely=0.28, anchor="nw", width=245, height=104)

    dosis_list = [0.5, 1.0, 1.5, 2.0]
    botones_dosis = {}

    color_normal = "gray"  # root.cget("bg")

    for i, dosis in enumerate(dosis_list):
        btn = tk.Button(frame_dosis_lista, text=f"{dosis:.1f} %", font=("Arial", 15, "bold"),
                        width=9, height=1, command=lambda d=dosis: dosis_fnc(d))
        btn.grid(row= i // 2, column=i % 2, padx=2, pady=4)
        #btn.place(relx=0.0, rely=0.3, anchor="nw", width=245, height=80)
        #btn.pack(expand=True)
        botones_dosis[dosis] = btn

    root.mainloop()

if __name__ == "__main__":
    main()