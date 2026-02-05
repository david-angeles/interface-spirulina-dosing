#!/usr/bin/env python3

###################################################################
###   Interfaz para el control del sistema de dosificación      ###
###   Autores: David Ángeles Rojas // Pedro Ponce Cruz          ###
###   Emails: david_angelez@hotmail.com / david_angeles@tec.mx  ###
###           pedro.ponce@tec.mx                                ###
###   Fecha: Febrero 2026                                       ###
###################################################################

import datetime    #para mostrar fecha y hora
from tkinter import PhotoImage #para importar logos
from PIL import Image, ImageTk #para cambiar tamaño de imagenes (hay que instalar)
from tkinter import ttk #para la barra de progreso
import tkinter as tk
from serial.tools import list_ports
import serial
import time
import threading
import queue

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
#img_power = Image.open(BASE_DIR / "icons" / "power.png")
#img_conectado = Image.open(BASE_DIR / "icons" / "arduino_connected.png")
#img_desconectado = Image.open(BASE_DIR / "icons" / "arduino_disconnected.png")


import sys
from serial.tools import list_ports

#ack_queue = queue.Queue()



############# para comunicacion serial ################

def listar_puertos():
    """Regresa una lista de strings con los puertos disponibles."""
    return [p.device for p in list_ports.comports()]

def abrir_serialold(puerto=None, baud=115200, timeout=0.3):
    """
    Abre el puerto serial y regresa el objeto Serial.
    - puerto=None: intenta escoger uno automáticamente
    """
    if puerto is None:
        # intenta detectar un Arduino por descripción / fabricante
        for p in list_ports.comports():
            desc = (p.description or "").lower()
            manuf = (p.manufacturer or "").lower()
            if "arduino" in desc or "arduino" in manuf or "usbmodem" in (p.device or "").lower() or "usbserial" in (p.device or "").lower():
                puerto = p.device
                break

    if puerto is None:
        raise RuntimeError(f"No encontré Arduino. Puertos detectados: {listar_puertos()}")

    ser = serial.Serial(puerto, baudrate=baud, timeout=timeout)
    time.sleep(2)  # Arduino se resetea al abrir el puerto
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except Exception:
        pass
    return ser

def abrir_serial(puerto=None, baud=115200, timeout=0.3):
    if puerto is None:
        puertos = list_ports.comports()

        # 1) Linux
        for p in puertos:
            if p.device.startswith("/dev/ttyACM") or p.device.startswith("/dev/ttyUSB"):
                puerto = p.device
                break

        # 2) macOS
        if puerto is None:
            for p in puertos:
                if "usbmodem" in p.device.lower() or "usbserial" in p.device.lower():
                    puerto = p.device
                    break

        # 3) Windows
        if puerto is None:
            for p in puertos:
                if "arduino" in (p.description or "").lower():
                    puerto = p.device
                    break

    if puerto is None:
        raise RuntimeError(
            "No encontré Arduino. Puertos detectados:\n" +
            "\n".join([p.device for p in list_ports.comports()])
        )

    ser = serial.Serial(puerto, baudrate=baud, timeout=timeout)
    time.sleep(2)  # reset automático del Arduino
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser

def enviar_linea(ser, texto: str):
    """Envía una línea terminada en \\n."""
    ser.write((texto.strip() + "\n").encode("utf-8"))

def leer_linea(ser) -> str:
    """Lee una línea. Regresa '' si no llegó nada dentro del timeout."""
    try:
        return ser.readline().decode("utf-8", errors="ignore").strip()
    except (serial.SerialException, OSError):
        return ""

def ping_pong(ser, intentos=1) -> bool:
    """Manda PING y espera PONG (requiere que Arduino lo implemente)."""
    for _ in range(intentos):
        enviar_linea(ser, "PING")
        t0 = time.time()
        while time.time() - t0 < 0.5:
            r = leer_linea(ser)
            if r == "PONG":
                return True
    return False

def enviar_startold(ser) -> str:
    """
    Envía START y lee una respuesta rápida.
    Regresa el string recibido (ej. 'ACK:START') o 'ERR:TIMEOUT'.
    """
    if ser is None:
        return "ERR:NO_SERIAL"

    try:
        enviar_linea(ser, "START")
        t0 = time.time()
        while time.time() - t0 < 1:
            resp = leer_linea(ser)
            if resp:
               break
        #resp = leer_linea(ser)  # 1 lectura, con timeout del puerto
        return resp if resp else "ERR:TIMEOUT"
    except (serial.SerialException, OSError):
        return "ERR:SERIAL"
    
def enviar_start(ser) -> str:
    if ser is None:
        return "ERR:NO_SERIAL"
    try:
        limpiar_ack_queue()
        enviar_linea(ser, "START")
        return esperar_ack("ACK:START", timeout=1.0)
    except (serial.SerialException, OSError):
        return "ERR:SERIAL"

    
def enviar_stopold(ser) -> str:
    """
    Envía STOP y lee una respuesta rápida.
    Regresa el string recibido (ej. 'ACK:STOP') o 'ERR:TIMEOUT'.
    """
    if ser is None:
        return "ERR:NO_SERIAL"

    try:
        enviar_linea(ser, "STOP")
        t0 = time.time()
        while time.time() - t0 < 1:
            resp = leer_linea(ser)
            if resp:
               break
        #resp = leer_linea(ser)  # 1 lectura, con timeout del puerto
        return resp if resp else "ERR:TIMEOUT"
    except (serial.SerialException, OSError):
        return "ERR:SERIAL"
    
def enviar_stop(ser) -> str:
    if ser is None: return "ERR:NO_SERIAL"
    enviar_linea(ser, "STOP")
    return esperar_ack("ACK:STOP", timeout=1.0)
    
def enviar_pauseold(ser) -> str:
    """
    Envía PAUSE y lee una respuesta rápida.
    Regresa el string recibido (ej. 'ACK:PAUSE') o 'ERR:TIMEOUT'.
    """
    if ser is None:
        return "ERR:NO_SERIAL"

    try:
        enviar_linea(ser, "PAUSE")
        t0 = time.time()
        while time.time() - t0 < 1:
            resp = leer_linea(ser)
            if resp:
               break
        #resp = leer_linea(ser)  # 1 lectura, con timeout del puerto
        return resp if resp else "ERR:TIMEOUT"
    except (serial.SerialException, OSError):
        return "ERR:SERIAL"
    
def enviar_pause(ser) -> str:
    if ser is None: return "ERR:NO_SERIAL"
    enviar_linea(ser, "PAUSE")
    return esperar_ack("ACK:PAUSE", timeout=1.0)
    
def enviar_restartold(ser) -> str:
    """
    Envía RESTART y lee una respuesta rápida.
    Regresa el string recibido (ej. 'ACK:RESTART') o 'ERR:TIMEOUT'.
    """
    if ser is None:
        return "ERR:NO_SERIAL"

    try:
        enviar_linea(ser, "RESTART")
        t0 = time.time()
        while time.time() - t0 < 1:
            resp = leer_linea(ser)
            if resp:
               break
        #resp = leer_linea(ser)  # 1 lectura, con timeout del puerto
        return resp if resp else "ERR:TIMEOUT"
    except (serial.SerialException, OSError):
        return "ERR:SERIAL"
    
def enviar_restart(ser) -> str:
    if ser is None: return "ERR:NO_SERIAL"
    enviar_linea(ser, "RESTART")
    return esperar_ack("ACK:RESTART", timeout=1.0)
    
def enviar_configold(ser, recipientes: int, mililitros: float, dosis: float) -> str:
    """
    Envía configuración al Arduino en una sola línea:
    CFG,<recipientes>,<mililitros>,<dosis>
    Espera ACK:CFG o ERR.
    """
    if ser is None:
        return "ERR:NO_SERIAL"

    # normaliza / limita
    recipientes = max(0, min(999, int(recipientes)))
    mililitros = max(0.0, min(1000.0, float(mililitros)))
    dosis = float(dosis)

    # evita comas raras o floats largos
    linea = f"CFG,{recipientes},{mililitros:.1f},{dosis:.1f}"

    try:
        # limpia basura antes de enviar (muy importante)
        try:
            ser.reset_input_buffer()
        except Exception:
            pass

        enviar_linea(ser, linea)

        t0 = time.time()
        while time.time() - t0 < 1.0:
            resp = leer_linea(ser)
            if resp:
                return resp
        return "ERR:TIMEOUT"
    except (serial.SerialException, OSError):
        return "ERR:SERIAL"
    
def enviar_config(ser, recipientes: int, mililitros: float, dosis: float) -> str:
    if ser is None:
        return "ERR:NO_SERIAL"

    recipientes = max(0, min(999, int(recipientes)))
    mililitros = max(0.0, min(1000.0, float(mililitros)))
    dosis = float(dosis)

    linea = f"CFG,{recipientes},{mililitros:.1f},{dosis:.1f}"

    try:
        limpiar_ack_queue()
        enviar_linea(ser, linea)
        return esperar_ack("ACK:CFG", timeout=1.0)
    except (serial.SerialException, OSError):
        return "ERR:SERIAL"
    
def limpiar_ack_queue():
    while True:
        try:
            ack_queue.get_nowait()
        except queue.Empty:
            break




####################################################################################



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
        global estado
        if estado_iniciar == 0:
        #    btn_iniciar.config(text="DETENER", bg="red", activebackground="red")
        #    estado_iniciar = 1

            # 1) Validaciones
            if dosis_seleccionada is None:
                agregar_log("SYS", "Selecciona una dosis (0.5 / 1.0 / 1.5 / 2.0) antes de iniciar", "-")
                return

            # 2) Enviar CONFIG primero
            r_cfg = enviar_config(ser, num_recipientes, mililitros_dosis, dosis_seleccionada)
            agregar_log("SYS", f"CFG -> {r_cfg}", "-")
            if r_cfg != "ACK:CFG":
                agregar_log("SYS", "No hubo ACK de CFG, no se enviará START", "-")
                return

        # intentamos iniciar en Arduino
            r = enviar_start(ser)
            agregar_log("SYS", f"START -> {r}", "-")

            if r == "ACK:START":
                btn_iniciar.config(text="DETENER", bg="red", activebackground="red")
                root.update_idletasks()
                estado_iniciar = 1
                estado=1
                actualizar_estado_ui()
            else:
                # no cambies a "DETENER" si Arduino no confirmó
                agregar_log("SYS", "No hubo ACK de START", "-")
        else:
            r = enviar_stop(ser)
            agregar_log("SYS", f"STOP -> {r}", "-")
            if r == "ACK:STOP":
                btn_iniciar.config(text="INICIAR", bg="green", activebackground="green")
                estado_iniciar = 0
                estado=2
                actualizar_estado_ui()
            else:
                # no cambies a "INICIAR" si Arduino no confirmó
                agregar_log("SYS", "No hubo ACK de STOP", "-")

def toggle_pausar():
        global estado_pausar, btn_pausar
        global estado
        if estado_pausar == 0:
            r = enviar_pause(ser)
            agregar_log("SYS", f"PAUSE -> {r}", "-")
            if r == "ACK:PAUSE":
                btn_pausar.config(text="REANUDAR", bg="red", activebackground="red")
                root.update_idletasks()
                estado_pausar = 1
                estado = 3
                actualizar_estado_ui()
            else:
                # no cambies a "PAUSAR" si Arduino no confirmó
                agregar_log("SYS", "No hubo ACK de PAUSE", "-")
        else:
            r = enviar_restart(ser)
            agregar_log("SYS", f"RESTART -> {r}", "-")
            if r == "ACK:RESTART":
                btn_pausar.config(text="PAUSAR", bg="green", activebackground="green")
                estado_pausar = 0
                estado = 1
                actualizar_estado_ui()
            else:
                # no cambies a "PAUSAR" si Arduino no confirmó
                agregar_log("SYS", "No hubo ACK de RESTART", "-")

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
    

    #ventana_teclado = tk.Toplevel(root)  # o ventana = tk.Toplevel(root)

    # --- FIX: asegurar que se vea encima del fullscreen ---
    ventana_teclado.transient(root)      # se “amarra” a la ventana principal
    ventana_teclado.grab_set()           # modal (bloquea clicks atrás)
    ventana_teclado.lift()               # al frente
    ventana_teclado.attributes("-topmost", True)
    ventana_teclado.focus_force()
    ventana_teclado.update_idletasks()

    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    w = int(sw * 0.55)   # 55% del ancho pantalla
    h = int(sh * 0.75)   # 75% del alto pantalla

    #centrar_ventana(ventana_teclado, w, h)

    #ventana_teclado.after(200, lambda: ventana_teclado.attributes("-topmost", False))
    ventana_teclado.after(10, lambda: centrar_ventana_en_root(ventana_teclado, root, w, h))
    # ------------------------------------------------------


    ventana_teclado.title("Ingrese Mililitros")
    #ventana_teclado.geometry(f"{sx(300)}x{sy(400)}")
    ventana_teclado.configure(bg="#b3e0ff")
    ventana_teclado.resizable(False, False)
    
    # Variable para almacenar la entrada
    entrada_valor = tk.StringVar(value=str(mililitros_dosis))
    
    # Frame para mostrar el valor actual
    frame_display = tk.Frame(ventana_teclado, bg="#80CBFF", bd=2, relief="sunken")
    frame_display.pack(fill="x", padx=5, pady=5)
    
    lbl_display = tk.Label(frame_display, textvariable=entrada_valor, 
                           font=("Arial", F(32), "bold"), bg="#80CBFF", fg="black")
    lbl_display.pack(pady=10)
    
    lbl_unidad = tk.Label(frame_display, text="mL", font=("Arial", F(16)), bg="#80CBFF", fg="black")
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
                btn = tk.Button(frame_botones, text="DEL", font=("Arial", F(14), "bold"),
                               bg="#FF6B6B", fg="white", activebackground="#FF5252",
                               command=eliminar)
            elif valor == ".":
                btn = tk.Button(frame_botones, text=".", font=("Arial", F(14), "bold"),
                               bg="#FFB74D", fg="white", activebackground="#FFA726",
                               command=agregar_punto)
            else:
                btn = tk.Button(frame_botones, text=str(valor), font=("Arial", F(18), "bold"),
                               bg="#4CAF50", fg="white", activebackground="#45a049",
                               command=lambda v=valor: agregar_digito(v))
            
            btn.grid(row=fila_idx, column=col_idx, sticky="nsew", padx=1, pady=1)
    
    # Configurar el peso de las filas y columnas
    for i in range(4):
        frame_botones.grid_rowconfigure(i, weight=1)
    for i in range(3):
        frame_botones.grid_columnconfigure(i, weight=1)
    
    # Botón ACEPTAR debajo de los números
    btn_aceptar = tk.Button(ventana_teclado, text="✓ ACEPTAR", font=("Arial", F(16), "bold"),
                            bg="#00AA00", fg="white", activebackground="#009900",
                            command=aceptar, height=sy(1))
    btn_aceptar.pack(fill="x", padx=1, pady=1)

def cambiar_recipientes():
    global num_recipientes, lbl_num_recipientes_objetivo, root

    ventana = tk.Toplevel(root)

    # --- FIX: asegurar que se vea encima del fullscreen ---
    ventana.transient(root)      # se “amarra” a la ventana principal
    ventana.grab_set()           # modal (bloquea clicks atrás)
    ventana.lift()               # al frente
    ventana.attributes("-topmost", True)
    ventana.focus_force()
    ventana.update_idletasks()

    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    w = int(sw * 0.55)   # 55% del ancho pantalla
    h = int(sh * 0.75)   # 75% del alto pantalla


    ventana.after(10, lambda: centrar_ventana_en_root(ventana, root, w, h))
    #ventana.after(200, lambda: ventana.attributes("-topmost", False))
    # ------------------------------------------------------

    ventana.title("Ingrese Recipientes")
    ventana.geometry(f"{sx(300)}x{sy(400)}")
    ventana.configure(bg="#b3e0ff")
    ventana.resizable(False, False)

    entrada_valor = tk.StringVar(value=str(num_recipientes))

    frame_display = tk.Frame(ventana, bg="#80CBFF", bd=2, relief="sunken")
    frame_display.pack(fill="x", padx=5, pady=5)

    lbl_display = tk.Label(frame_display, textvariable=entrada_valor,
                           font=("Arial", F(32), "bold"), bg="#80CBFF", fg="black")
    lbl_display.pack(pady=10)

    lbl_unidad = tk.Label(frame_display, text="recipientes", font=("Arial", F(14)),
                          bg="#80CBFF", fg="black")
    lbl_unidad.pack(pady=5)

    frame_botones = tk.Frame(ventana, bg="#b3e0ff")
    frame_botones.pack(padx=5, pady=5, expand=True, fill="both")

    def agregar_digito(d):
        s = entrada_valor.get()

        # si estaba "0", reemplaza
        if s == "0":
            s = str(d)
        else:
            s = s + str(d)

        # máximo 3 dígitos
        if len(s) > 3:
            return

        entrada_valor.set(s)

    def eliminar():
        s = entrada_valor.get()
        if len(s) > 0:
            s = s[:-1]
        if s == "":
            s = "0"
        entrada_valor.set(s)

    def aceptar():
        global num_recipientes
        global progress
        try:
            val = int(entrada_valor.get())
            if 0 <= val <= 999:
                num_recipientes = val
                lbl_num_recipientes_objetivo.config(text=str(num_recipientes))
                ventana.destroy()
            else:
                entrada_valor.set("999 max")
        except:
            entrada_valor.set("Error")

    # Teclado sin punto
    botones = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        [0, "DEL", ""]
    ]

    for fila_idx, fila in enumerate(botones):
        for col_idx, v in enumerate(fila):
            if v == "":
                # celda vacía para mantener el layout 3x4
                dummy = tk.Label(frame_botones, text="", bg="#b3e0ff")
                dummy.grid(row=fila_idx, column=col_idx, sticky="nsew", padx=1, pady=1)
                continue

            if v == "DEL":
                btn = tk.Button(frame_botones, text="DEL", font=("Arial", F(14), "bold"),
                                bg="#FF6B6B", fg="white", activebackground="#FF5252",
                                command=eliminar)
            else:
                btn = tk.Button(frame_botones, text=str(v), font=("Arial", F(18), "bold"),
                                bg="#4CAF50", fg="white", activebackground="#45a049",
                                command=lambda x=v: agregar_digito(x))

            btn.grid(row=fila_idx, column=col_idx, sticky="nsew", padx=1, pady=1)

    for i in range(4):
        frame_botones.grid_rowconfigure(i, weight=1)
    for i in range(3):
        frame_botones.grid_columnconfigure(i, weight=1)

    btn_ok = tk.Button(ventana, text="✓ ACEPTAR", font=("Arial", F(16), "bold"),
                       bg="#00AA00", fg="white", activebackground="#009900",
                       command=aceptar, height=sy(1))
    btn_ok.pack(fill="x", padx=1, pady=1)

    progress.configure(maximum=num_recipientes)
    progress['value'] = 0


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

def actualizar_estado_ui():
    global estado, lbl_estado
    if estado == 1:
        lbl_estado.config(text="ACTIVO")
    elif estado == 2:
        lbl_estado.config(text="INACTIVO")
    elif estado == 3:
        lbl_estado.config(text="EN PAUSA")
    else:
        lbl_estado.config(text=f"ESTADO {estado}")

#def serial_reader_thread(ser, rx_queue):
#    global stop_reader
#    while not stop_reader:
#        try:
#            line = leer_linea(ser)  # tu función (readline + decode)
#            if line:
#                rx_queue.put(line)
#        except Exception:
#            time.sleep(0.05)

def serial_reader_thread(ser, rx_queue, ack_queue):
    global stop_reader
    while not stop_reader:
        try:
            line = leer_linea(ser)
            if not line:
                continue

            # TEL a rx_queue
            if line.startswith("TEL,"):
                rx_queue.put(line)
            else:
                # TODO lo demás es ACK / mensajes
                ack_queue.put(line)

        except Exception:
            time.sleep(0.05)

def esperar_ack(prefijo, timeout=1.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            msg = ack_queue.get_nowait()
        except queue.Empty:
            time.sleep(0.01)
            continue

        if msg == prefijo:
            return msg
        
        if msg.startswith("EVT:"):
            ack_queue.put(msg)
        # si llega otra cosa, la ignoras o la puedes loggear
    return "ERR:TIMEOUT"



def procesar_rx_queue():
    # procesa todo lo que haya en cola
    while True:
        try:
            line = rx_queue.get_nowait()
        except queue.Empty:
            break

        # Parseo
        if line.startswith("TEL,"):
            parts = line.split(",")
            # Esperamos 1 + 1 + 8 = 10 elementos: TEL + dosificados + (t,ph)*4
            if len(parts) == 10:
                try:
                    dosificados = int(parts[1])
                    dosif_var.set(str(dosificados))
                    progress['value']=dosificados

                    # Actualiza 4 sensores
                    # parts: [TEL, dosif, t0, ph0, t1, ph1, t2, ph2, t3, ph3]
                    idx = 2
                    for i in range(4):
                        t = float(parts[idx]);    idx += 1
                        p = float(parts[idx]);    idx += 1
                        #temp_vars[i].set(f"{t:.1f} °C") #se ocultó para ver si el sensor mide temperatura 
                        ph_vars[i].set(f"pH {p:.2f}")
                except:
                    pass

    # vuelve a llamar
    root.after(50, procesar_rx_queue)

def procesar_ack_queue():
    global estado_iniciar, estado_pausar, estado

    while True:
        try:
            msg = ack_queue.get_nowait()
        except queue.Empty:
            break

        if msg == "EVT:DONE":
            agregar_log("SYS", "Proceso terminado (Arduino)", "-")
            estado = 2
            estado_iniciar = 0
            estado_pausar = 0
            btn_iniciar.config(text="INICIAR", bg="green", activebackground="green")
            btn_pausar.config(text="PAUSAR", bg="green", activebackground="green")

            actualizar_estado_ui()

    root.after(50, procesar_ack_queue)


def on_close():
    global stop_reader, ser
    stop_reader = True
    try:
        if ser is not None:
            ser.close()
    except:
        pass
    root.destroy()

def centrar_ventana_en_root(win, root, w, h):
    # Tamaño fijo del popup
    win.geometry(f"{w}x{h}")

    # Asegura que Tk ya “dibujó” root y win
    root.update_idletasks()
    win.update_idletasks()

    # Posición del root (en pantalla)
    rx = root.winfo_rootx()
    ry = root.winfo_rooty()
    rw = root.winfo_width()
    rh = root.winfo_height()

    # Centro relativo al root
    x = rx + (rw - w) // 2
    y = ry + (rh - h) // 2

    win.geometry(f"{w}x{h}+{x}+{y}")





def main():
    global botones_dosis, color_normal, dosis_seleccionada, estado_iniciar, btn_iniciar
    global estado_pausar, btn_pausar
    global txt_log, mililitros_dosis, lbl_mililitros, root
    global num_recipientes, lbl_num_recipientes_objetivo
    global ser
    global lbl_estado
    global estado

    global ack_queue

    global progress

    global rx_queue
    global stop_reader

    global dosif_var, temp_vars, ph_vars




    estado = 2  #para indicar el estado del sistema (2: sin iniciar, 1: iniciado, 2: pausa)
    dosis_seleccionada = None
    estado_iniciar = 0   #para indicar si esta en ejecución la tarea
    estado_pausar = 0   #para indicar si esta en ejecución la tarea
    mililitros_dosis = 10.0  #valor inicial en mililitros


    root = tk.Tk()
    root.title("DOSIFICADOR DE ESPIRULINA AUTOMÁTICO TEC-IPN v0.3")


    secret_taps = 0
    secret_last_ms = 0
    SECRET_TAPS_REQUIRED = 7
    SECRET_TIMEOUT_MS = 1200   # si pasan >1.2s entre taps, se reinicia


    #### pueba de comunicación serial con Arduino ######
    ser = None
    try:
        ser = abrir_serial(puerto=None, baud=115200, timeout=0.3)
        print("Serial abierto:", ser.port)
        
    except Exception as e:
        print("No pude abrir serial:", e)
        conectado_arduino = False

    if ser is not None:
        ok = ping_pong(ser, intentos=2)
        print("PING/PONG:", ok)
        conectado_arduino = True
        if not ok:
            conectado_arduino = False
    #####################################################

    ############ enviar "iniciar"? #####################
    #ser = None
    #try:
    #    ser = abrir_serial(puerto=None, baud=115200, timeout=0.3)
    #    print("Serial abierto:", ser.port)
    #except Exception as e:
    #    print("No pude abrir serial:", e)
    #    ser = None
    #####################################################



    rx_queue = queue.Queue()
    ack_queue = queue.Queue()
    stop_reader = False

    t = threading.Thread(target=serial_reader_thread, args=(ser, rx_queue, ack_queue), daemon=True)
    t.start()

    #rx_queue = queue.Queue()
    #stop_reader = False

    #if ser is not None:
    #    t = threading.Thread(target=serial_reader_thread, args=(ser, rx_queue), daemon=True)
    #    t.start()
    #else:
    #    print("Sin serial: no arranco thread de lectura")
    
    # ---------- Responsive layout / auto-scale ----------
    # Base design size (the UI was originally laid out for this resolution)
    BASE_W, BASE_H = 800, 480

    # Real screen size (Raspberry Pi display / HDMI)
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    # Scale factors for X/Y
    scale_x = screen_w / BASE_W
    scale_y = screen_h / BASE_H
    scale   = min(scale_x, scale_y)  # for fonts (uniform scaling)
    
    def sx(v: int) -> int:
        return max(1, int(v * scale_x))

    def sy(v: int) -> int:
        return max(1, int(v * scale_y))

    def F(pt: int) -> int:
    # Font size scaler with a minimum to keep it readable
        return max(8, int(pt * scale)) 
    
    globals()["sx"] = sx
    globals()["sy"] = sy
    globals()["F"]  = F

    # Make the app fill the whole screen
    try:
        root.attributes("-fullscreen", True)
    except Exception:
        # fallback
        root.geometry(f"{screen_w}x{screen_h}+0+0")
# ---------------------------------------------------

    root.resizable(True, True)

    root.bind("<Escape>", lambda e: root.destroy())



    #######cierre oculto con 7 taps ##########
    def secret_exit(event=None):
        nonlocal secret_taps, secret_last_ms

        now = int(time.time() * 1000)

        # si tardaste mucho entre taps, reinicia conteo
        if now - secret_last_ms > SECRET_TIMEOUT_MS:
            secret_taps = 0

        secret_last_ms = now
        secret_taps += 1

        if secret_taps >= SECRET_TAPS_REQUIRED:
            # reinicia para que no vuelva a dispararse
            secret_taps = 0

            # cierra limpio (usa tu on_close)
            on_close()

    ###############################################

    ######### paleta de colores ##########
    azul = "#b3e0ff"  # color de fondo
    azul_1 = "#80CBFF"  # otro color paleta colores
    aqua = "#B3FFF8" #otro color paleta colores
    moradito = "#B3BAFF" #otro color paleta colores
    verdecito = "#BAFFB3" #otro color paleta colores
    root.configure(bg=azul)


    temp_vars = [tk.StringVar(value="--.- °C") for _ in range(4)]
    ph_vars   = [tk.StringVar(value="pH --.--") for _ in range(4)]
    dosif_var = tk.StringVar(value="0")  # recipientes dosificados

    ########## Frame para el baner ##########
    frame_banner = tk.Frame(root, bg="white")
    frame_banner.place(relx=0.0, rely=0.0, anchor="nw", width=sx(400), height=sy(40))

    lbl_banner = tk.Label(frame_banner, text="DOSIFICADOR DE ESPIRULINA TEC-IPN", \
                             font=("Arial", F(15)), bg=azul, fg="black")
    lbl_banner.bind("<Button-1>", secret_exit)   # click/tap izquierdo

    lbl_banner.pack(fill="both", expand=True)

    ########### icono para apagar ##########
    import os
    from tkinter import messagebox

    # Icono de apagar
    #img_power = Image.open("icons/power.png").resize((sx(28), sy(28)))
    img_power = Image.open(BASE_DIR / "icons" / "power.png")
    icono_power = ImageTk.PhotoImage(img_power)




    ########## Frame para indicador de conexión ##########

    # Cargar y ajustar el icono
    #img_conectado = Image.open("icons/arduino_connected.png").resize((sx(40), sy(40))) #tamaño en pix
    img_conectado = Image.open(BASE_DIR / "icons" / "arduino_connected.png")
    icono_conectado = ImageTk.PhotoImage(img_conectado)

    #img_desconectado = Image.open("icons/arduino_disconnected.png").resize((sx(24), sy(24)))
    img_desconectado = Image.open(BASE_DIR / "icons" / "arduino_disconnected.png")
    icono_desconectado = ImageTk.PhotoImage(img_desconectado)

    frame_conectado = tk.Frame(root, bg="white")
    frame_conectado.place(relx=0.53, rely=0.0, anchor="nw", width=sx(200), height=sy(40))

    ########## Frame para indicador de conexión ##########
    #frame_conectado = tk.Frame(root, bg="white")
    #frame_conectado.place(relx=0.53, rely=0.0, anchor="nw", width=sx(200), height=sy(40))

    # -------- ICONO POWER (A LA IZQUIERDA) ----------
    import os
    from tkinter import messagebox

    #img_power = Image.open("icons/power.png").convert("RGBA").resize((sx(28), sy(28)))
    img_power = Image.open(BASE_DIR / "icons" / "power.png").convert("RGBA").resize((sx(28), sy(28)))
    icono_power = ImageTk.PhotoImage(img_power)

    def apagar_raspberry():
        if not messagebox.askyesno("Apagar", "¿Seguro que deseas apagar la Raspberry Pi?"):
            return

        # (opcional) avisar al Arduino que pare
        try:
            if ser is not None:
                enviar_linea(ser, "STOP")
                time.sleep(0.1)
        except Exception:
            pass

        # Apaga el sistema (lo ideal es NO llamar on_close antes; shutdown ya mata el proceso)
        os.system("sudo shutdown -h now")

    btn_power = tk.Button( frame_conectado, image=icono_power, bg=azul, activebackground=azul, bd=0, relief="flat", 
                          command=apagar_raspberry)
    btn_power.image = icono_power   # <- IMPORTANTÍSIMO: mantener referencia
    btn_power.pack(side="left", padx=sx(4), pady=0)
# -----------------------------------------------


    #conectado_arduino = True
    

    if conectado_arduino:
        lbl_conectado = tk.Label(frame_conectado, image=icono_conectado, bg=azul)
        lbl_conectado.pack(side="left", padx=0, pady=0)

        lbl_conectado = tk.Label(frame_conectado, text="CONECTADO", font=("Arial", F(15)), bg=azul, fg="black")
        lbl_conectado.pack(fill="both", expand=True)
    else:
        lbl_conectado = tk.Label(frame_conectado, image=icono_desconectado, bg=azul)
        lbl_conectado.pack(side="left", padx=0, pady=0)

        lbl_conectado = tk.Label(frame_conectado, text="DESCONECTADO", font=("Arial", F(15)), bg=azul, fg="black")
        lbl_conectado.pack(fill="both", expand=True)

    ########## Frame para la fecha y hora ##########
    frame_fecha_hora = tk.Frame(root, bg="white")
    frame_fecha_hora.place(relx=1.0, rely=0.0, anchor="ne", width=sx(150), height=sy(40))

    lbl_fecha_hora = tk.Label(frame_fecha_hora, font=("Arial", F(12)), bg=azul, fg="black")
    lbl_fecha_hora.pack(fill="both", expand=True)
    date_time(lbl_fecha_hora)

    ########## Frame recipientes a dosificar ##########
    frame_dosificacion = tk.Frame(root, bg=azul)
    frame_dosificacion.place(relx=0.01, rely=0.1, anchor="nw", width=sx(520), height=sy(270))

    lbl_dosificacion = tk.Label(frame_dosificacion, text="Recipientes a dosificar", \
                          font=("Arial", F(15)), bg=azul_1, fg="black")
    lbl_dosificacion.place(relx=0.05, rely=0.0, anchor="nw", width=sx(230), height=sy(40))

    num_recipientes = 10  # global
    lbl_num_recipientes_objetivo = tk.Button(
        frame_dosificacion,
        text=str(num_recipientes),
        font=("Arial", F(80), "bold"),
        bg=azul_1,
        activebackground=azul_1,
        relief="flat",
        bd=0,
        command=cambiar_recipientes  # <- la nueva función
    )
    lbl_num_recipientes_objetivo.place(relx=0.05, rely=0.14, anchor="nw", width=sx(230), height=sy(100))

    # Para actualizar el número en cualquier parte del código:
    # lbl_num_recipientes.config(text=str(nuevo_valor))

    lbl_dosificacion = tk.Label(frame_dosificacion, text="Dosificados", \
                          font=("Arial", F(15)), bg=azul_1, fg="black")
    lbl_dosificacion.place(relx=0.55, rely=0.0, anchor="nw", width=sx(230), height=sy(40))

    num_recipientes_dosificados = 600   #numero de recipientes dosificados

    lbl_num_recipientes = tk.Label(frame_dosificacion, textvariable=dosif_var, font=("Arial", F(80), "bold"), bg=azul_1)

    #lbl_num_recipientes = tk.Label(frame_dosificacion, text=str(num_recipientes_dosificados), font=("Arial", F(80), "bold"), bg=azul_1)
    lbl_num_recipientes.place(relx=0.55, rely=0.14, anchor="nw", width=sx(230), height=sy(100))

    # barra de progreso
    progress = ttk.Progressbar(frame_dosificacion, length=200, maximum=num_recipientes)
    progress.place(relx=0.1, rely=0.53, anchor="nw", width=sx(440), height=sy(30))
    progress['value'] = 0

    #actualziar estado del sistema
    lbl_estado = tk.Label(frame_dosificacion, font=("Arial", F(24)), bg=moradito, fg="black")
    lbl_estado.place(relx=0.1, rely=0.65, anchor="nw", width=sx(230), height=sy(40))

    actualizar_estado_ui()

    # indicador mililitros a dosificar
    lbl_mililitros = tk.Button(frame_dosificacion, text=f"{mililitros_dosis:.1f} mL", 
                               font=("Arial", F(20), "bold"), bg=verdecito, fg="black",
                               activebackground=verdecito, activeforeground="black",
                               command=cambiar_mililitros, relief="raised", bd=3)
    lbl_mililitros.place(relx=0.55, rely=0.65, anchor="nw", width=sx(207), height=sy(40))


    # boton iniciar/detener
    btn_iniciar = tk.Button(frame_dosificacion, text="INICIAR", font=("Arial", F(15), "bold"),
                            width=sx(10), height=sy(2), bg="green", fg="white",
                            activebackground="green", activeforeground="white",
                            command=toggle_iniciar)
    btn_iniciar.place(relx=0.2, rely=0.97, anchor="s", width=sx(150), height=sy(40))

    # boton pausar/reanudar
    btn_pausar = tk.Button(frame_dosificacion, text="PAUSAR", font=("Arial", F(15), "bold"),
                            width=sx(10), height=sy(2), bg="green", fg="white",
                            activebackground="green", activeforeground="white",
                            command=toggle_pausar)
    btn_pausar.place(relx=0.495, rely=0.97, anchor="s", width=sx(130), height=sy(40))

    # boton guardar
    btn_guardar = tk.Button(frame_dosificacion, text="GUARDAR DATOS", font=("Arial", F(15), "bold"),
                            width=sx(10), height=sy(2), bg="green", fg="white",
                            activebackground="green", activeforeground="white",
                            command=toggle_guardar)
    btn_guardar.place(relx=0.82, rely=0.97, anchor="s", width=sx(180), height=sy(40))
    ##########################################################################


    ########### HISTORIAL ##########
    frame_historial = tk.Frame(root, bg="white")
    frame_historial.place(relx=0.04, rely=0.67, anchor="nw", width=sx(495), height=sy(140))

    lbl_hist = tk.Label(frame_historial, text="Historial", \
                          font=("Arial", F(14)), bg=azul_1, fg="black")
    lbl_hist.place(relx=0.0, rely=0.0, anchor="nw", width=sx(495), height=sy(25))

    # Crear el widget Text para el log
    txt_log = tk.Text(frame_historial, font=("Consolas", F(12)), bg="white", fg="black", state="disabled")
    #txt_log.pack(fill="both", expand=True)
    txt_log.place(relx=0.0, rely=0.182, anchor="nw", width=sx(495), height=sy(115))

    agregar_log(1, 23.4, 7.1)
    agregar_log(2, 23.5, 999.2)

    ########### DATOS DE TELEMETRIA ###########
    ########### DATOS DE TELEMETRIA (2x2) ###########
    frame_telemetria = tk.Frame(root, bg=azul, bd=2, relief="groove")
    frame_telemetria.place(relx=0.675, rely=0.1, anchor="nw", width=sx(250), height=sy(260))

    # Título arriba
    lbl_tele = tk.Label(frame_telemetria, text="Telemetría",
                    font=("Arial", F(24)), bg=azul_1, fg="black")
    lbl_tele.place(relx=0.0, rely=0.0, anchor="nw", width=sx(245), height=sy(40))

    # Área “grid” debajo del título
    grid_area = tk.Frame(frame_telemetria, bg=azul)
    grid_area.place(relx=0.0, rely=0.16, anchor="nw", width=sx(245), height=sy(210))

    # 2 columnas / 2 filas iguales
    grid_area.grid_columnconfigure(0, weight=1, uniform="col")
    grid_area.grid_columnconfigure(1, weight=1, uniform="col")
    grid_area.grid_rowconfigure(0, weight=1, uniform="row")
    grid_area.grid_rowconfigure(1, weight=1, uniform="row")

    # Orden y títulos por celda (idx 0..3)
    dose_titles = ["0.5 %", "1.0 %", "1.5 %", "2.0 %"]

    def make_card(parent, idx):
        card = tk.Frame(parent, bg=moradito, bd=2, relief="ridge")
        card.grid_propagate(False)

        # 2 filas: título dosis + valor pH
        card.grid_rowconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=2)
        card.grid_columnconfigure(0, weight=1)

        lbl_title = tk.Label(card, text=f"Dosis {dose_titles[idx]}",
                         font=("Arial", F(13), "bold"),
                         bg=moradito, fg="black")
        lbl_title.grid(row=0, column=0, sticky="nsew", padx=sx(2), pady=sy(2))

        lbl_ph = tk.Label(card, textvariable=ph_vars[idx],
                      font=("Arial", F(22), "bold"),
                      bg=moradito, fg="black")
        lbl_ph.grid(row=1, column=0, sticky="nsew", padx=sx(2), pady=sy(2))

        return card

    # 2x2: 0->(0,0) 1->(0,1) 2->(1,0) 3->(1,1)
    for idx in range(4):
        r = idx // 2
        c = idx % 2
        card = make_card(grid_area, idx)
        card.grid(row=r, column=c, sticky="nsew", padx=sx(2), pady=sy(2))


    #def make_card(parent, idx):
    #    # tarjeta contenedora
    #    card = tk.Frame(parent, bg=moradito, bd=2, relief="ridge")
    #    card.grid_propagate(False)  # evita que se “achique” por el contenido

    #    # Layout interno: 2 filas (Temp y pH)
    #    card.grid_rowconfigure(0, weight=1)
    #    card.grid_rowconfigure(1, weight=1)
    #    card.grid_columnconfigure(0, weight=1)

    #    lbl_t = tk.Label(card, textvariable=temp_vars[idx],
    #                 font=("Arial", F(16), "bold"), bg=moradito, fg="black")
    #    lbl_t.grid(row=0, column=0, sticky="nsew", padx=sx(2), pady=sy(2))

    #    lbl_p = tk.Label(card, textvariable=ph_vars[idx],
    #                 font=("Arial", F(16), "bold"), bg=moradito, fg="black")
    #    lbl_p.grid(row=1, column=0, sticky="nsew", padx=sx(2), pady=sy(2))

    #    return card

    ## Coloca los 4 sensores en 2x2:
    ## idx 0 -> (0,0), idx 1 -> (0,1), idx 2 -> (1,0), idx 3 -> (1,1)
    #for idx in range(4):
    #    r = idx // 2
    #    c = idx % 2
    #    card = make_card(grid_area, idx)
    #    card.grid(row=r, column=c, sticky="nsew", padx=sx(2), pady=sy(2))
###############################################


    ##########################################################################

    frame_dosis = tk.Frame(root, bg="white", bd=2, relief="groove")
    frame_dosis.place(relx=0.675, rely=0.65, anchor="nw", width=sx(250), height=sy(150))
    #frame_dosis.pack(expand=True)
    
    lbl_dosis_titulo = tk.Label(frame_dosis, text="Dosis", font=("Arial", F(24)), bg=azul_1)
    lbl_dosis_titulo.place(relx=0.0, rely=0.0, anchor="nw", width=sx(245), height=sy(40))
    #lbl_dosis_titulo.grid(row=0, column=0, columnspan=2, pady=(10, 10))

    frame_dosis_lista = tk.Frame(frame_dosis, bg=moradito)

    frame_dosis_lista.place(relx=0.0, rely=0.28, anchor="nw", width=sx(245), height=sy(104))
    frame_dosis_lista.pack_propagate(False)
    frame_dosis_lista.grid_propagate(False)

    # 2 columnas iguales y 2 filas iguales
    frame_dosis_lista.grid_columnconfigure(0, weight=1)
    frame_dosis_lista.grid_columnconfigure(1, weight=1)
    frame_dosis_lista.grid_rowconfigure(0, weight=1)
    frame_dosis_lista.grid_rowconfigure(1, weight=1)

    dosis_list = [0.5, 1.0, 1.5, 2.0]
    botones_dosis = {}

    color_normal = "gray"  # root.cget("bg")

    for i, dosis in enumerate(dosis_list):
        btn = tk.Button(frame_dosis_lista, text=f"{dosis:.1f} %", font=("Arial", F(15), "bold"),
        command=lambda d=dosis: dosis_fnc(d) )
        btn.grid(row=i // 2, column=i % 2, padx=sx(2), pady=sy(4), sticky="nsew")
        botones_dosis[dosis] = btn
        #btn = tk.Button(frame_dosis_lista, text=f"{dosis:.1f} %", font=("Arial", F(15), "bold"),
        #                width=sx(9), height=sy(1), command=lambda d=dosis: dosis_fnc(d))
        #btn.grid(row= i // 2, column=i % 2, padx=2, pady=4)
        ##btn.place(relx=0.0, rely=0.3, anchor="nw", width=sx(245), height=sy(80))
        ##btn.pack(expand=True)
        #botones_dosis[dosis] = btn

    root.after(50, procesar_rx_queue)
    root.after(50, procesar_ack_queue)
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()