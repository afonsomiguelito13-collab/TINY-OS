from Xlib import X, display
from Xlib.ext import xinput
import time
import subprocess
import threading
import re
import os

# ============ SETUP ============
d = display.Display()
s = d.screen()
W, H = s.width_in_pixels, s.height_in_pixels

cmap = s.default_colormap
def cor(r, g, b):
    return cmap.alloc_color(r*257, g*257, b*257).pixel

PRETO    = cor(0, 0, 0)
BRANCO   = cor(255, 255, 255)
AZUL     = cor(0x33, 0x99, 0xDD)
AZUL_ESC = cor(0x1A, 0x2A, 0x4A)
VERDE    = cor(0x33, 0xCC, 0x66)
AMARELO  = cor(0xDD, 0xBB, 0x33)
VERMELHO = cor(0xDD, 0x44, 0x44)
ROXO     = cor(0x99, 0x66, 0xDD)
TXT      = cor(0xE0, 0xE0, 0xE0)
TXT_DIM  = cor(0x99, 0x99, 0x99)
PAINEL_BG = cor(0x1A, 0x1E, 0x24)
PAINEL_BORDA = cor(0x40, 0x45, 0x4C)
CARD = cor(0x25, 0x2A, 0x30)

TINYOS_VERSAO = "v0.1-alpha"
TINYOS_BUILD = "2026.10.16"

# ============ JANELA ============
win = s.root.create_window(
    0, 0, W, H, 1,
    s.root_depth,
    X.InputOutput,
    X.CopyFromParent,
    background_pixel=PRETO,
    event_mask=(X.ExposureMask | X.KeyPressMask |
                X.ButtonPressMask | X.ButtonReleaseMask)
)
win.set_wm_name("TinyOS - Desktop")
win.map()
d.sync()
d.flush()

gc = win.create_gc()

def rect(x, y, w, h, c):
    gc.change(foreground=c)
    win.fill_rectangle(gc, x, y, w, h)

def borda(x, y, w, h, c):
    gc.change(foreground=c)
    win.rectangle(gc, x, y, w, h)

def texto(txt, x, y, c=TXT):
    gc.change(foreground=c)
    win.draw_text(gc, x, y, txt.encode('latin-1'), len(txt))

def texto_centro(txt, cx, y, c=TXT):
    texto(txt, cx - len(txt) * 3, y, c)

# ============ ADB ============
def adb(comando, timeout=3):
    try:
        r = subprocess.run(
            ["adb", "shell", comando],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except:
        return None

def adb_local():
    """Roda comando LOCAL (não adb shell)"""
    try:
        r = subprocess.run(
            ["adb"] + comando.split(),
            capture_output=True, text=True, timeout=3
        )
        return r.stdout.strip()
    except:
        return None

# ============ DETECTAR MÉTODO DE DEPURAÇÃO ============
def detectar_metodo_debug():
    """
    Detecta como o ADB tá conectado:
    - 'shizuku' → via Shizuku (wireless debugging local)
    - 'pc'      → via PC (USB ou rede externa)
    - 'nenhum'  → nada
    """
    try:
        # 1. ADB tem device conectado?
        r = subprocess.run(
            ["adb", "devices"],
            capture_output=True, text=True, timeout=3
        )
        saida = r.stdout
        if not saida or 'device' not in saida:
            return "nenhum"

        # 2. Descobre o device
        device = None
        for linha in saida.split('\n')[1:]:
            if '\tdevice' in linha:
                device = linha.split('\t')[0].strip()
                break

        if not device:
            return "nenhum"

        # 3. É um IP local (shizuku via wireless debug)?
        #    Shizuku usa localhost/127.0.0.1 ou o IP da própria rede
        if 'localhost' in device or '127.0.0.1' in device:
            return "shizuku"

        # 4. É um IP da rede (PC ou USB via rede)?
        if re.match(r'\d+\.\d+\.\d+\.\d+', device):
            # Verifica se o device é o próprio celular
            ip_local = adb("ip addr show wlan0 | grep 'inet ' | head -1")
            if ip_local:
                m = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ip_local)
                if m and m.group(1) in device:
                    return "shizuku"  # mesmo IP = conexão local
            return "pc"

        # 5. USB
        if device and not ':' in device:
            return "pc-usb"

        return "desconhecido"
    except:
        return "nenhum"

# ============ CACHE ============
cache = {
    "wifi": {"ssid": "?", "ip": "?", "sinal": "?", "conectado": False, "gateway": "?"},
    "bateria": {"nivel": "?", "status": "?", "temp": "?"},
    "device": {"modelo": "?", "android": "?", "hostname": "?", "fabricante": "?"},
    "cpu": {"modelo": "?", "cores": "?", "uso": "?", "temp": "?"},
    "ram": {"total": "?", "livre": "?"},
    "debug": {"metodo": "?", "device": "?", "versao": "?"},
    "uptime": "?",
    "ultima_atualizacao": 0,
}

def atualizar_dados():
    global cache
    try:
        # Wi-Fi
        wifi_info = adb("dumpsys wifi | grep -m1 'mWifiInfo'")
        if wifi_info:
            m = re.search(r'SSID:\s*"?([^",]+)"?', wifi_info)
            if m:
                cache["wifi"]["ssid"] = m.group(1).strip()
                cache["wifi"]["conectado"] = True

        ip = adb("ip addr show wlan0 | grep 'inet ' | head -1")
        if ip:
            partes = ip.split()
            if len(partes) >= 2:
                cache["wifi"]["ip"] = partes[1].split('/')[0]

        rssi = adb("dumpsys wifi | grep -m1 'RSSI'")
        if rssi:
            m = re.search(r'RSSI:\s*(-?\d+)', rssi)
            if m:
                cache["wifi"]["sinal"] = m.group(1) + " dBm"

        gw = adb("ip route | grep default | head -1")
        if gw:
            m = re.search(r'via\s+(\d+\.\d+\.\d+\.\d+)', gw)
            if m:
                cache["wifi"]["gateway"] = m.group(1)

        # Bateria
        bat = adb("dumpsys battery")
        if bat:
            m = re.search(r'level:\s*(\d+)', bat)
            if m: cache["bateria"]["nivel"] = m.group(1)
            m = re.search(r'status:\s*(\d+)', bat)
            if m:
                st = m.group(1)
                mapa = {"1": "Desconhecido", "2": "Carregando",
                        "3": "Descarregando", "4": "Nao carrega",
                        "5": "Cheio"}
                cache["bateria"]["status"] = mapa.get(st, "?")
            m = re.search(r'temperature:\s*(\d+)', bat)
            if m: cache["bateria"]["temp"] = str(int(m.group(1)) / 10) + "C"

        # Device
        cache["device"]["modelo"] = adb("getprop ro.product.model") or "?"
        cache["device"]["android"] = adb("getprop ro.build.version.release") or "?"
        cache["device"]["hostname"] = adb("getprop net.hostname") or "?"
        cache["device"]["fabricante"] = adb("getprop ro.product.manufacturer") or "?"

        # CPU
        cpu_info = adb("cat /proc/cpuinfo | grep -m1 'model name'")
        if cpu_info:
            m = re.search(r'model name\s*:\s*(.+)', cpu_info)
            if m: cache["cpu"]["modelo"] = m.group(1).strip()[:25]
        else:
            # ARM não tem "model name", usa Hardware
            hw = adb("cat /proc/cpuinfo | grep -m1 'Hardware'")
            if hw:
                m = re.search(r'Hardware\s*:\s*(.+)', hw)
                if m: cache["cpu"]["modelo"] = m.group(1).strip()[:25]
            else:
                cache["cpu"]["modelo"] = cache["device"]["modelo"]

        cores = adb("nproc")
        if cores:
            cache["cpu"]["cores"] = cores.strip()

        # Uso de CPU (via top uma vez)
        top = adb("top -n 1 -b | grep -m1 'cpu'")
        if top:
            m = re.search(r'(\d+)%', top)
            if m: cache["cpu"]["uso"] = m.group(1) + "%"
        else:
            cache["cpu"]["uso"] = "?"

        # Temperatura CPU (thermal zone)
        temp = adb("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null")
        if temp:
            try:
                t = int(temp.strip())
                cache["cpu"]["temp"] = str(t / 1000) + "C"
            except:
                cache["cpu"]["temp"] = "?"

        # RAM
        mem = adb("cat /proc/meminfo | head -2")
        if mem:
            m = re.search(r'MemTotal:\s*(\d+)', mem)
            if m:
                cache["ram"]["total"] = str(round(int(m.group(1)) / 1024 / 1024, 1)) + " GB"
            m = re.search(r'MemFree:\s*(\d+)', mem)
            if m:
                cache["ram"]["livre"] = str(round(int(m.group(1)) / 1024 / 1024, 1)) + " GB"

        # Uptime
        up = adb("cat /proc/uptime")
        if up:
            segundos = int(float(up.split()[0]))
            horas = segundos // 3600
            minutos = (segundos % 3600) // 60
            cache["uptime"] = str(horas) + "h " + str(minutos) + "min"

        # Método de depuração
        cache["debug"]["metodo"] = detectar_metodo_debug()

        # Device conectado (endereço)
        r = subprocess.run(["adb", "devices"],
                          capture_output=True, text=True, timeout=3)
        for linha in r.stdout.split('\n')[1:]:
            if '\tdevice' in linha:
                cache["debug"]["device"] = linha.split('\t')[0].strip()
                break

        # Versão do ADB
        r = subprocess.run(["adb", "version"],
                          capture_output=True, text=True, timeout=3)
        m = re.search(r'Version\s+(\S+)', r.stdout)
        if m:
            cache["debug"]["versao"] = m.group(1)

        cache["ultima_atualizacao"] = time.time()
    except Exception as e:
        print("Erro:", e)

def atualizar_em_background():
    t = threading.Thread(target=atualizar_dados, daemon=True)
    t.start()

# ============ WALLPAPER ============
CORES_LINHA = []
for y in range(H):
    t = y / H
    r = int(0x10 + (0x05 - 0x10) * t)
    g = int(0x18 + (0x0A - 0x18) * t)
    b = int(0x30 + (0x18 - 0x30) * t)
    CORES_LINHA.append(cor(r, g, b))

ESTRELAS = [
    (50, 30), (120, 80), (200, 25), (280, 110), (350, 45),
    (420, 90), (500, 20), (580, 130), (650, 60), (720, 100),
    (800, 35), (80, 160), (180, 200), (300, 180), (450, 220),
    (600, 170), (700, 210), (750, 150), (30, 250), (400, 280),
    (550, 300), (680, 260), (820, 320), (100, 350), (250, 380),
    (420, 400), (600, 420), (740, 390), (200, 440), (500, 460),
    (60, 300), (330, 340), (770, 270), (140, 420), (620, 90),
]

def desenhar_wallpaper():
    for y in range(H):
        rect(0, y, W, 1, CORES_LINHA[y])
    for ex, ey in ESTRELAS:
        if ex < W and ey < H:
            rect(ex, ey, 2, 2, BRANCO)
            c_dim = cor(0x88, 0x99, 0xBB)
            rect(ex - 1, ey, 4, 1, c_dim)
            rect(ex, ey - 1, 1, 4, c_dim)

# ============ BARRA INFERIOR ============
BARRA_H = 28
BARRA_Y = H - BARRA_H

def desenhar_barra():
    rect(0, BARRA_Y, W, BARRA_H, cor(0x15, 0x18, 0x1C))
    rect(0, BARRA_Y, W, 1, PAINEL_BORDA)

    hora = time.strftime("%H:%M")
    texto(hora, 10, BARRA_Y + 19, TXT)
    data = time.strftime("%d/%m")
    texto(data, 55, BARRA_Y + 19, TXT_DIM)

    wifi_txt = "WiFi*" if cache["wifi"]["conectado"] else "WiFi"
    wifi_x = W - 130
    if hover == "btn_wifi":
        rect(wifi_x - 5, BARRA_Y + 2, 60, BARRA_H - 4, cor(0x25, 0x2A, 0x30))
    cor_wifi = VERDE if cache["wifi"]["conectado"] else VERMELHO
    texto(wifi_txt, wifi_x, BARRA_Y + 19, cor_wifi)

    bat_txt = cache["bateria"]["nivel"]
    if bat_txt != "?":
        try:
            nivel = int(bat_txt)
            c_bat = VERDE if nivel > 50 else (AMARELO if nivel > 20 else VERMELHO)
            bat_txt = str(nivel) + "%"
        except:
            c_bat = TXT_DIM
    else:
        c_bat = TXT_DIM
        bat_txt = "--"

    bat_x = W - 55
    if hover == "btn_bat":
        rect(bat_x - 5, BARRA_Y + 2, 50, BARRA_H - 4, cor(0x25, 0x2A, 0x30))
    texto(bat_txt, bat_x, BARRA_Y + 19, c_bat)

# ============ PAINÉIS PEQUENOS ============
painel_ativo = None

def desenhar_painel_wifi():
    pw, ph = 240, 130
    px = W - pw - 10
    py = BARRA_Y - ph - 5
    rect(px, py, pw, ph, PAINEL_BG)
    borda(px, py, pw, ph, PAINEL_BORDA)
    rect(px, py, pw, 26, CARD)
    texto("Wi-Fi", px + 10, py + 18, TXT)
    y = py + 45
    texto("SSID:", px + 10, y, TXT_DIM)
    texto(cache["wifi"]["ssid"][:20], px + 70, y, TXT)
    y += 20
    texto("IP:", px + 10, y, TXT_DIM)
    texto(cache["wifi"]["ip"], px + 70, y, TXT)
    y += 20
    texto("Sinal:", px + 10, y, TXT_DIM)
    texto(cache["wifi"]["sinal"], px + 70, y, TXT)
    y += 20
    texto("Status:", px + 10, y, TXT_DIM)
    if cache["wifi"]["conectado"]:
        texto("Conectado", px + 70, y, VERDE)
    else:
        texto("Desconectado", px + 70, y, VERMELHO)

def desenhar_painel_bateria():
    pw, ph = 240, 130
    px = W - pw - 10
    py = BARRA_Y - ph - 5
    rect(px, py, pw, ph, PAINEL_BG)
    borda(px, py, pw, ph, PAINEL_BORDA)
    rect(px, py, pw, 26, CARD)
    texto("Bateria", px + 10, py + 18, TXT)
    nivel = cache["bateria"]["nivel"]
    y = py + 45
    texto("Nivel:", px + 10, y, TXT_DIM)
    if nivel != "?":
        try:
            n = int(nivel)
            c = VERDE if n > 50 else (AMARELO if n > 20 else VERMELHO)
        except:
            c = TXT
        texto(nivel + "%", px + 70, y, c)
    y += 20
    texto("Status:", px + 10, y, TXT_DIM)
    texto(cache["bateria"]["status"], px + 70, y, TXT)
    y += 20
    texto("Temp:", px + 10, y, TXT_DIM)
    texto(cache["bateria"]["temp"], px + 70, y, TXT)

def desenhar_painel_hora():
    pw, ph = 240, 130
    px = 10
    py = BARRA_Y - ph - 5
    rect(px, py, pw, ph, PAINEL_BG)
    borda(px, py, pw, ph, PAINEL_BORDA)
    rect(px, py, pw, 26, CARD)
    texto("Data e Hora", px + 10, py + 18, TXT)
    y = py + 45
    texto("Hora:", px + 10, y, TXT_DIM)
    texto(time.strftime("%H:%M:%S"), px + 70, y, TXT)
    y += 20
    texto("Data:", px + 10, y, TXT_DIM)
    texto(time.strftime("%d/%m/%Y"), px + 70, y, TXT)
    y += 20
    texto("Dia:", px + 10, y, TXT_DIM)
    dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
    texto(dias[time.localtime().tm_wday], px + 70, y, TXT)
    y += 20
    texto("Uptime:", px + 10, y, TXT_DIM)
    texto(cache["uptime"], px + 70, y, TXT)

# ============ PAINEL CONFIGURAÇÕES (GRANDE) ============
def desenhar_painel_config():
    """Painel grande de Configurações"""
    pw, ph = min(700, W - 40), min(500, H - 80)
    px = (W - pw) // 2
    py = (H - ph) // 2

    # Fundo
    rect(px, py, pw, ph, PAINEL_BG)
    borda(px, py, pw, ph, PAINEL_BORDA)

    # Header
    rect(px, py, pw, 32, CARD)
    texto("Configuracoes do Sistema", px + 15, py + 22, TXT)
    # Botão X (fechar)
    rect(px + pw - 30, py + 5, 22, 22, VERMELHO)
    texto("X", px + pw - 23, py + 21, BRANCO)

    # Colunas (2 colunas)
    col_w = (pw - 30) // 2
    col1_x = px + 10
    col2_x = px + 20 + col_w

    y1 = py + 45
    y2 = py + 45

    # ===== COLUNA 1 =====
    # --- Sistema ---
    texto("SISTEMA", col1_x, y1, AZUL)
    y1 += 8
    rect(col1_x, y1, col_w, 1, PAINEL_BORDA)
    y1 += 15
    texto("OS: TinyOS " + TINYOS_VERSAO, col1_x + 5, y1, TXT); y1 += 16
    texto("Build: " + TINYOS_BUILD, col1_x + 5, y1, TXT_DIM); y1 += 16
    texto("Uptime: " + cache["uptime"], col1_x + 5, y1, TXT); y1 += 16
    texto("Hostname: " + cache["device"]["hostname"], col1_x + 5, y1, TXT); y1 += 20

    # --- CPU ---
    texto("CPU", col1_x, y1, AZUL)
    y1 += 8
    rect(col1_x, y1, col_w, 1, PAINEL_BORDA)
    y1 += 15
    texto("Modelo: " + cache["cpu"]["modelo"][:22], col1_x + 5, y1, TXT); y1 += 16
    texto("Nucleos: " + cache["cpu"]["cores"], col1_x + 5, y1, TXT); y1 += 16
    texto("Uso: " + cache["cpu"]["uso"], col1_x + 5, y1, TXT); y1 += 16
    texto("Temp: " + cache["cpu"]["temp"], col1_x + 5, y1, TXT); y1 += 20

    # --- RAM ---
    texto("MEMORIA", col1_x, y1, AZUL)
    y1 += 8
    rect(col1_x, y1, col_w, 1, PAINEL_BORDA)
    y1 += 15
    texto("Total: " + cache["ram"]["total"], col1_x + 5, y1, TXT); y1 += 16
    texto("Livre: " + cache["ram"]["livre"], col1_x + 5, y1, TXT); y1 += 20

    # ===== COLUNA 2 =====
    # --- Internet ---
    texto("INTERNET", col2_x, y2, AZUL)
    y2 += 8
    rect(col2_x, y2, col_w, 1, PAINEL_BORDA)
    y2 += 15
    met = "Wi-Fi" if cache["wifi"]["conectado"] else "Nenhum"
    texto("Metodo: " + met, col2_x + 5, y2, TXT); y2 += 16
    texto("SSID: " + cache["wifi"]["ssid"][:18], col2_x + 5, y2, TXT); y2 += 16
    texto("IP: " + cache["wifi"]["ip"], col2_x + 5, y2, TXT); y2 += 16
    texto("Gateway: " + cache["wifi"]["gateway"], col2_x + 5, y2, TXT); y2 += 16
    texto("Sinal: " + cache["wifi"]["sinal"], col2_x + 5, y2, TXT); y2 += 20

    # --- Depuração (DESTAQUE) ---
    texto("DEPURACAO (ADB)", col2_x, y2, VERDE)
    y2 += 8
    rect(col2_x, y2, col_w, 1, PAINEL_BORDA)
    y2 += 15

    metodo = cache["debug"]["metodo"]
    if metodo == "shizuku":
        texto("Metodo: Shizuku", col2_x + 5, y2, ROXO)
        y2 += 16
        texto("(conexao local)", col2_x + 5, y2, TXT_DIM)
    elif metodo == "pc":
        texto("Metodo: PC (rede)", col2_x + 5, y2, AZUL)
        y2 += 16
        texto("(conexao externa)", col2_x + 5, y2, TXT_DIM)
    elif metodo == "pc-usb":
        texto("Metodo: PC (USB)", col2_x + 5, y2, AZUL)
        y2 += 16
        texto("(cabo USB)", col2_x + 5, y2, TXT_DIM)
    elif metodo == "nenhum":
        texto("Metodo: Nenhum", col2_x + 5, y2, VERMELHO)
        y2 += 16
        texto("(ADB desconectado)", col2_x + 5, y2, TXT_DIM)
    else:
        texto("Metodo: " + metodo, col2_x + 5, y2, TXT)
        y2 += 16

    y2 += 16
    texto("Device: " + cache["debug"]["device"][:20], col2_x + 5, y2, TXT); y2 += 16
    texto("ADB: " + cache["debug"]["versao"], col2_x + 5, y2, TXT); y2 += 20

    # --- Hardware ---
    texto("HARDWARE", col2_x, y2, AZUL)
    y2 += 8
    rect(col2_x, y2, col_w, 1, PAINEL_BORDA)
    y2 += 15
    texto("Modelo: " + cache["device"]["modelo"][:20], col2_x + 5, y2, TXT); y2 += 16
    texto("Fabricante: " + cache["device"]["fabricante"][:18], col2_x + 5, y2, TXT); y2 += 16
    texto("Android: " + cache["device"]["android"], col2_x + 5, y2, TXT); y2 += 16
    texto("Bateria: " + cache["bateria"]["nivel"] + "%", col2_x + 5, y2, TXT)

def desenhar_painel():
    if painel_ativo == "wifi":
        desenhar_painel_wifi()
    elif painel_ativo == "bateria":
        desenhar_painel_bateria()
    elif painel_ativo == "hora":
        desenhar_painel_hora()
    elif painel_ativo == "config":
        desenhar_painel_config()

# ============ ÍCONES ============
icones = [
    ("Meu PC",     20, 20,  "icone_pc"),
    ("Lixeira",    20, 80,  "icone_lixeira"),
    ("Config",     20, 140, "icone_config"),
]

def desenhar_icones():
    for nome, ix, iy, key in icones:
        hov = (hover == key)
        # Cor do fundo (mais claro se hover)
        c_bg = cor(0x40, 0x55, 0x80) if hov else cor(0x30, 0x40, 0x60)
        rect(ix, iy, 32, 32, c_bg)
        borda(ix, iy, 32, 32, AZUL if hov else cor(0x55, 0x66, 0x88))

        # Ícone específico
        if key == "icone_pc":
            # Monitor
            rect(ix + 6, iy + 8, 20, 14, cor(0x88, 0xAA, 0xDD))
            rect(ix + 6, iy + 8, 20, 1, BRANCO)
            rect(ix + 13, iy + 24, 6, 2, cor(0x88, 0xAA, 0xDD))
        elif key == "icone_lixeira":
            # Lixeira
            rect(ix + 8, iy + 10, 16, 18, cor(0x88, 0xAA, 0xDD))
            rect(ix + 6, iy + 8, 20, 3, BRANCO)
            rect(ix + 14, iy + 6, 4, 2, BRANCO)
        elif key == "icone_config":
            # Engrenagem simples
            rect(ix + 12, iy + 10, 8, 12, cor(0xDD, 0xDD, 0xDD))
            rect(ix + 8, iy + 14, 16, 4, cor(0xDD, 0xDD, 0xDD))
            rect(ix + 14, iy + 8, 4, 16, cor(0xDD, 0xDD, 0xDD))
            rect(ix + 12, iy + 13, 8, 6, AZUL)
            rect(ix + 14, iy + 15, 4, 2, cor(0xDD, 0xDD, 0xDD))

        texto(nome, ix, iy + 45, TXT)

# ============ RENDER ============
def desenhar_tudo():
    desenhar_wallpaper()
    desenhar_icones()
    desenhar_barra()
    if painel_ativo:
        desenhar_painel()
    d.sync()
    d.flush()

# ============ HOVER ============
hover = None

def detectar_hover(mx, my):
    # Ícones
    for nome, ix, iy, key in icones:
        if ix <= mx <= ix + 32 and iy <= my <= iy + 32:
            return key

    # Barra inferior
    if BARRA_Y <= my <= H:
        if W - 135 <= mx <= W - 75:
            return "btn_wifi"
        if W - 60 <= mx <= W - 10:
            return "btn_bat"
        if 5 <= mx <= 50:
            return "btn_hora"

    # Botão X do painel de config
    if painel_ativo == "config":
        pw, ph = min(700, W - 40), min(500, H - 80)
        px = (W - pw) // 2
        py = (H - ph) // 2
        if px + pw - 30 <= mx <= px + pw - 8 and py + 5 <= my <= py + 27:
            return "btn_fechar_config"

    return None

# ============ CLIQUE ============
def ao_clicar(mx, my, target):
    global painel_ativo

    if target == "icone_config":
        painel_ativo = "config"
        print("Abrindo Configuracoes")
        # Força atualização dos dados
        atualizar_em_background()
        time.sleep(0.5)

    elif target == "icone_pc":
        print("Abrindo Meu PC (nao implementado)")

    elif target == "icone_lixeira":
        print("Lixeira (vazia)")

    elif target == "btn_fechar_config":
        painel_ativo = None
        print("Fechando Configuracoes")

    elif target == "btn_wifi":
        painel_ativo = None if painel_ativo == "wifi" else "wifi"
    elif target == "btn_bat":
        painel_ativo = None if painel_ativo == "bateria" else "bateria"
    elif target == "btn_hora":
        painel_ativo = None if painel_ativo == "hora" else "hora"

    else:
        # Clicou fora
        if painel_ativo:
            painel_ativo = None
            print("Painel fechado")

# ============ RENDER INICIAL ============
print("=== TinyOS Desktop v5 ===")
print("Atualizando dados via ADB...")
desenhar_tudo()
atualizar_em_background()
time.sleep(2)
desenhar_tudo()

print("")
print("Clique em:")
print("  - Config (3o icone)  -> painel completo")
print("  - WiFi/Bat/Hora      -> paineis rapidos")
print("ESC pra sair")
print("")

# ============ LOOP ============
rodando = True
ultima_hora_str = time.strftime("%H:%M")
ultimo_update = time.time()

while rodando:
    eventos = False
    while d.pending_events():
        ev = d.next_event()
        eventos = True

        if ev.type == X.Expose:
            desenhar_tudo()
        elif ev.type == X.ButtonPress:
            if ev.detail == 1:
                mx, my = ev.event_x, ev.event_y
                # Atualiza hover antes de clicar
                hover = detectar_hover(mx, my)
                ao_clicar(mx, my, hover)
                desenhar_tudo()
        elif ev.type == X.KeyPress:
            if ev.detail in (9, 67):
                print("Saindo...")
                rodando = False

    # Relógio
    hora_atual = time.strftime("%H:%M")
    if hora_atual != ultima_hora_str:
        desenhar_tudo()
        ultima_hora_str = hora_atual

    # Atualiza dados a cada 15s
    if time.time() - ultimo_update > 15:
        atualizar_em_background()
        ultimo_update = time.time()

    if not eventos:
        time.sleep(0.1)

print("Fechando...")
win.destroy()
d.sync()
print("Adeus!")
