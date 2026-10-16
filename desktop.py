cat > ~/TINY-OS/desktop.py << 'PYEOF'
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
def adb(comando, timeout=5):
    try:
        r = subprocess.run(
            ["adb", "shell", comando],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except:
        return None

def adb_local(args, timeout=5):
    try:
        r = subprocess.run(
            ["adb"] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except:
        return None

def adb_disponivel():
    try:
        r = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=3)
        for linha in r.stdout.strip().split('\n')[1:]:
            if '\tdevice' in linha:
                return True
        return False
    except:
        return False

# ============ FILE MANAGER ============
fm = {
    "ativo": False,
    "caminho": "/data/data/com.termux/files/home",
    "arquivos": [],
    "selecionado": None,
    "scroll": 0,
    "info_popup": None,  # arquivo clicado 2x
    "loading": False,
}

def listar_diretorio(caminho):
    """Lista arquivos de um diretório via ADB"""
    resultado = adb(f'ls -la "{caminho}"')
    if not resultado:
        return []

    arquivos = []
    for linha in resultado.split('\n'):
        # formato: drwxr-xr-x  user group size date time name
        partes = linha.split(None, 8)
        if len(partes) < 9:
            continue
        perm = partes[0]
        tamanho = partes[4]
        nome = partes[8].strip()

        # Pula . e ..
        if nome in ('.', '..'):
            continue

        is_dir = perm.startswith('d')
        arquivos.append({
            "nome": nome,
            "caminho": caminho.rstrip('/') + '/' + nome,
            "dir": is_dir,
            "tamanho": tamanho,
            "perm": perm,
        })

    # Ordena: pastas primeiro, depois alfabético
    arquivos.sort(key=lambda x: (not x["dir"], x["nome"].lower()))
    return arquivos

def abrir_file_manager(caminho_inicial="/data/data/com.termux/files/home"):
    fm["ativo"] = True
    fm["caminho"] = caminho_inicial
    fm["loading"] = True
    fm["selecionado"] = None
    fm["scroll"] = 0
    fm["info_popup"] = None
    print(f"Abrindo arquivos: {caminho_inicial}")

    # Carrega em background
    def carregar():
        fm["arquivos"] = listar_diretorio(fm["caminho"])
        fm["loading"] = False
        print(f"  {len(fm['arquivos'])} itens")

    t = threading.Thread(target=carregar, daemon=True)
    t.start()

def fechar_file_manager():
    fm["ativo"] = False
    fm["info_popup"] = None
    print("File manager fechado")

def navegar_para(novo_caminho):
    fm["caminho"] = novo_caminho
    fm["loading"] = True
    fm["scroll"] = 0
    fm["info_popup"] = None

    def carregar():
        fm["arquivos"] = listar_diretorio(novo_caminho)
        fm["loading"] = False

    t = threading.Thread(target=carregar, daemon=True)
    t.start()

def eh_compativel(nome):
    """Verifica se o arquivo pode ser aberto pelo TinyOS"""
    ext = os.path.splitext(nome)[1].lower()
    compativeis = {
        ".py": ("Python Script", True, "Editor de codigo"),
        ".txt": ("Texto", True, "Editor de texto"),
        ".md": ("Markdown", True, "Editor de texto"),
        ".json": ("JSON", True, "Editor de texto"),
        ".sh": ("Shell Script", True, "Terminal"),
        ".jpg": ("Imagem JPEG", True, "Visualizador"),
        ".jpeg": ("Imagem JPEG", True, "Visualizador"),
        ".png": ("Imagem PNG", True, "Visualizador"),
        ".gif": ("GIF", True, "Visualizador"),
        ".mp3": ("Audio MP3", False, "Player de audio"),
        ".mp4": ("Video MP4", False, "Player de video"),
        ".pdf": ("Documento PDF", False, "Leitor PDF"),
        ".zip": ("Arquivo ZIP", False, "Extrator"),
        ".apk": ("App Android", False, "Instalador Android"),
        ".deb": ("Pacote Debian", False, "dpkg"),
    }
    return compativeis.get(ext, ("Desconhecido", False, "Sem suporte"))

def mostrar_info_arquivo(arquivo):
    """Mostra popup com info do arquivo"""
    tipo, compativel, app = eh_compativel(arquivo["nome"])
    fm["info_popup"] = {
        "arquivo": arquivo,
        "tipo": tipo,
        "compativel": compativel,
        "app": app,
    }
    print(f"Info: {arquivo['nome']} - {tipo} - {'OK' if compativel else 'NAO SUPORTADO'}")

# ============ CACHE ============
cache = {
    "wifi": {"ssid": "?", "ip": "?", "sinal": "?", "conectado": False},
    "bateria": {"nivel": "?", "status": "?", "temp": "?"},
    "device": {"modelo": "?", "android": "?", "hostname": "?", "fabricante": "?"},
    "cpu": {"modelo": "?", "cores": "?", "uso": "?", "temp": "?"},
    "ram": {"total": "?", "livre": "?"},
    "debug": {"metodo": "?", "device": "?", "versao": "?"},
    "uptime": "?",
    "ultima_atualizacao": 0,
}

def detectar_metodo_debug():
    try:
        r = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=3)
        saida = r.stdout
        if not saida or 'device' not in saida:
            return "nenhum"
        device = None
        for linha in saida.split('\n')[1:]:
            if '\tdevice' in linha:
                device = linha.split('\t')[0].strip()
                break
        if not device:
            return "nenhum"
        if 'localhost' in device or '127.0.0.1' in device:
            return "shizuku"
        if re.match(r'\d+\.\d+\.\d+\.\d+', device):
            ip_local = adb("ip addr show wlan0 | grep 'inet ' | head -1")
            if ip_local:
                m = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ip_local)
                if m and m.group(1) in device:
                    return "shizuku"
            return "pc"
        if device and ':' not in device:
            return "pc-usb"
        return "desconhecido"
    except:
        return "nenhum"

def atualizar_dados():
    global cache
    try:
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

        bat = adb("dumpsys battery")
        if bat:
            m = re.search(r'level:\s*(\d+)', bat)
            if m: cache["bateria"]["nivel"] = m.group(1)
            m = re.search(r'status:\s*(\d+)', bat)
            if m:
                mapa = {"1": "Desconhecido", "2": "Carregando",
                        "3": "Descarregando", "4": "Nao carrega", "5": "Cheio"}
                cache["bateria"]["status"] = mapa.get(m.group(1), "?")
            m = re.search(r'temperature:\s*(\d+)', bat)
            if m: cache["bateria"]["temp"] = str(int(m.group(1)) / 10) + "C"

        cache["device"]["modelo"] = adb("getprop ro.product.model") or "?"
        cache["device"]["android"] = adb("getprop ro.build.version.release") or "?"
        cache["device"]["hostname"] = adb("getprop net.hostname") or "?"
        cache["device"]["fabricante"] = adb("getprop ro.product.manufacturer") or "?"

        cores = adb("nproc")
        if cores: cache["cpu"]["cores"] = cores.strip()
        top = adb("top -n 1 -b | grep -m1 'cpu'")
        if top:
            m = re.search(r'(\d+)%', top)
            if m: cache["cpu"]["uso"] = m.group(1) + "%"

        temp = adb("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null")
        if temp:
            try:
                cache["cpu"]["temp"] = str(int(temp.strip()) / 1000) + "C"
            except: pass

        mem = adb("cat /proc/meminfo | head -2")
        if mem:
            m = re.search(r'MemTotal:\s*(\d+)', mem)
            if m: cache["ram"]["total"] = str(round(int(m.group(1)) / 1024 / 1024, 1)) + " GB"
            m = re.search(r'MemFree:\s*(\d+)', mem)
            if m: cache["ram"]["livre"] = str(round(int(m.group(1)) / 1024 / 1024, 1)) + " GB"

        up = adb("cat /proc/uptime")
        if up:
            seg = int(float(up.split()[0]))
            cache["uptime"] = f"{seg // 3600}h {(seg % 3600) // 60}min"

        cache["debug"]["metodo"] = detectar_metodo_debug()
        r = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=3)
        for linha in r.stdout.split('\n')[1:]:
            if '\tdevice' in linha:
                cache["debug"]["device"] = linha.split('\t')[0].strip()
                break
        r = subprocess.run(["adb", "version"], capture_output=True, text=True, timeout=3)
        m = re.search(r'Version\s+(\S+)', r.stdout)
        if m: cache["debug"]["versao"] = m.group(1)

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
    y = py + 45
    texto("Nivel:", px + 10, y, TXT_DIM)
    nivel = cache["bateria"]["nivel"]
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
    texto("Uptime:", px + 10, y, TXT_DIM)
    texto(cache["uptime"], px + 70, y, TXT)
    y += 20
    texto("Device:", px + 10, y, TXT_DIM)
    texto(cache["device"]["modelo"][:15], px + 70, y, TXT)

# ============ PAINEL CONFIG ============
def desenhar_painel_config():
    pw, ph = min(700, W - 40), min(500, H - 80)
    px = (W - pw) // 2
    py = (H - ph) // 2
    rect(px, py, pw, ph, PAINEL_BG)
    borda(px, py, pw, ph, PAINEL_BORDA)
    rect(px, py, pw, 32, CARD)
    texto("Configuracoes do Sistema", px + 15, py + 22, TXT)
    rect(px + pw - 30, py + 5, 22, 22, VERMELHO)
    texto("X", px + pw - 23, py + 21, BRANCO)

    col_w = (pw - 30) // 2
    col1_x = px + 10
    col2_x = px + 20 + col_w
    y1 = py + 45
    y2 = py + 45

    texto("SISTEMA", col1_x, y1, AZUL); y1 += 8
    rect(col1_x, y1, col_w, 1, PAINEL_BORDA); y1 += 15
    texto("OS: TinyOS " + TINYOS_VERSAO, col1_x + 5, y1, TXT); y1 += 16
    texto("Uptime: " + cache["uptime"], col1_x + 5, y1, TXT); y1 += 16
    texto("Hostname: " + cache["device"]["hostname"][:18], col1_x + 5, y1, TXT); y1 += 20

    texto("CPU", col1_x, y1, AZUL); y1 += 8
    rect(col1_x, y1, col_w, 1, PAINEL_BORDA); y1 += 15
    texto("Nucleos: " + cache["cpu"]["cores"], col1_x + 5, y1, TXT); y1 += 16
    texto("Uso: " + cache["cpu"]["uso"], col1_x + 5, y1, TXT); y1 += 16
    texto("Temp: " + cache["cpu"]["temp"], col1_x + 5, y1, TXT); y1 += 20

    texto("MEMORIA", col1_x, y1, AZUL); y1 += 8
    rect(col1_x, y1, col_w, 1, PAINEL_BORDA); y1 += 15
    texto("Total: " + cache["ram"]["total"], col1_x + 5, y1, TXT); y1 += 16
    texto("Livre: " + cache["ram"]["livre"], col1_x + 5, y1, TXT)

    texto("INTERNET", col2_x, y2, AZUL); y2 += 8
    rect(col2_x, y2, col_w, 1, PAINEL_BORDA); y2 += 15
    met = "Wi-Fi" if cache["wifi"]["conectado"] else "Nenhum"
    texto("Metodo: " + met, col2_x + 5, y2, TXT); y2 += 16
    texto("SSID: " + cache["wifi"]["ssid"][:18], col2_x + 5, y2, TXT); y2 += 16
    texto("IP: " + cache["wifi"]["ip"], col2_x + 5, y2, TXT); y2 += 16
    texto("Sinal: " + cache["wifi"]["sinal"], col2_x + 5, y2, TXT); y2 += 20

    texto("DEPURACAO (ADB)", col2_x, y2, VERDE); y2 += 8
    rect(col2_x, y2, col_w, 1, PAINEL_BORDA); y2 += 15
    metodo = cache["debug"]["metodo"]
    if metodo == "shizuku":
        texto("Metodo: Shizuku", col2_x + 5, y2, ROXO); y2 += 16
        texto("(conexao local)", col2_x + 5, y2, TXT_DIM)
    elif metodo == "pc":
        texto("Metodo: PC (rede)", col2_x + 5, y2, AZUL); y2 += 16
    elif metodo == "nenhum":
        texto("Metodo: Nenhum", col2_x + 5, y2, VERMELHO); y2 += 16
    else:
        texto("Metodo: " + metodo, col2_x + 5, y2, TXT); y2 += 16
    y2 += 16
    texto("Device: " + cache["debug"]["device"][:20], col2_x + 5, y2, TXT); y2 += 16
    texto("ADB: " + cache["debug"]["versao"], col2_x + 5, y2, TXT); y2 += 20

    texto("HARDWARE", col2_x, y2, AZUL); y2 += 8
    rect(col2_x, y2, col_w, 1, PAINEL_BORDA); y2 += 15
    texto("Modelo: " + cache["device"]["modelo"][:20], col2_x + 5, y2, TXT); y2 += 16
    texto("Android: " + cache["device"]["android"], col2_x + 5, y2, TXT); y2 += 16
    texto("Bateria: " + cache["bateria"]["nivel"] + "%", col2_x + 5, y2, TXT)

# ============ FILE MANAGER UI ============
def desenhar_file_manager():
    """Janela do file manager"""
    pw, ph = min(720, W - 30), min(520, H - 60)
    px = (W - pw) // 2
    py = (H - ph) // 2

    # Fundo
    rect(px, py, pw, ph, PAINEL_BG)
    borda(px, py, pw, ph, PAINEL_BORDA)

    # Header
    rect(px, py, pw, 32, CARD)
    texto("Arquivos", px + 15, py + 22, TXT)

    # Botão X (fechar)
    rect(px + pw - 30, py + 5, 22, 22, VERMELHO)
    texto("X", px + pw - 23, py + 21, BRANCO)

    # Barra de caminho
    y_bar = py + 40
    rect(px + 10, y_bar, pw - 20, 26, cor(0x15, 0x18, 0x1C))
    borda(px + 10, y_bar, pw - 20, 26, PAINEL_BORDA)

    # Botão voltar (se não tá na home)
    bx = px + 15
    if fm["caminho"] != "/":
        if hover == "btn_fm_voltar":
            rect(bx, y_bar + 3, 24, 20, AZUL)
        texto("<<", bx + 6, y_bar + 17, TXT)
        bx += 30

    # Caminho
    caminho_mostrar = fm["caminho"]
    if len(caminho_mostrar) > 60:
        caminho_mostrar = "..." + caminho_mostrar[-57:]
    texto(caminho_mostrar, bx, y_bar + 17, TXT_DIM)

    # Sidebar (locais)
    sb_w = 130
    sb_y = y_bar + 35
    rect(px + 10, sb_y, sb_w, ph - 90, cor(0x20, 0x24, 0x2A))
    borda(px + 10, sb_y, sb_w, ph - 90, PAINEL_BORDA)

    locais = [
        ("Home Termux", "/data/data/com.termux/files/home"),
        ("Downloads", "/sdcard/Download"),
        ("DCIM", "/sdcard/DCIM"),
        ("Storage", "/sdcard"),
        ("Root Termux", "/data/data/com.termux/files/usr"),
    ]
    texto("Locais", px + 18, sb_y + 18, AZUL)
    for i, (nome, caminho) in enumerate(locais):
        ly = sb_y + 35 + i * 24
        hov = (hover == f"loc_{i}")
        atual = (fm["caminho"] == caminho)
        if hov or atual:
            rect(px + 15, ly - 12, sb_w - 10, 20,
                 AZUL if atual else CARD_HOV)
        texto(nome, px + 20, ly, TXT if not atual else BRANCO)

    # Lista de arquivos
    lista_x = px + sb_w + 20
    lista_w = pw - sb_w - 30
    lista_y = sb_y
    lista_h = ph - 90

    rect(lista_x, lista_y, lista_w, lista_h, cor(0x18, 0x1C, 0x22))
    borda(lista_x, lista_y, lista_w, lista_h, PAINEL_BORDA)

    if fm["loading"]:
        texto("Carregando...", lista_x + 15, lista_y + 30, AMARELO)
    elif not fm["arquivos"]:
        texto("(vazio)", lista_x + 15, lista_y + 30, TXT_DIM)
    else:
        max_visiveis = (lista_h - 10) // 22
        scroll = fm["scroll"]
        visiveis = fm["arquivos"][scroll:scroll + max_visiveis]

        for i, arq in enumerate(visiveis):
            ay = lista_y + 5 + i * 22
            sel = (fm["selecionado"] == arq["nome"])
            hov = (hover == f"file_{i}")

            if sel:
                rect(lista_x + 3, ay, lista_w - 6, 20, AZUL)
            elif hov:
                rect(lista_x + 3, ay, lista_w - 6, 20, CARD_HOV)

            # Ícone
            icone = "[D]" if arq["dir"] else "[F]"
            cor_icone = AMARELO if arq["dir"] else AZUL
            texto(icone, lista_x + 10, ay + 14, cor_icone)

            # Nome
            nome_mostrar = arq["nome"]
            max_chars = (lista_w - 100) // 6
            if len(nome_mostrar) > max_chars:
                nome_mostrar = nome_mostrar[:max_chars - 3] + "..."
            texto(nome_mostrar, lista_x + 40, ay + 14, TXT)

            # Tamanho (se arquivo)
            if not arq["dir"] and arq["tamanho"].isdigit():
                tam = int(arq["tamanho"])
                if tam > 1024 * 1024:
                    tam_txt = f"{tam // (1024*1024)}M"
                elif tam > 1024:
                    tam_txt = f"{tam // 1024}K"
                else:
                    tam_txt = f"{tam}B"
                texto(tam_txt, lista_x + lista_w - 50, ay + 14, TXT_DIM)

    # Popup de info (duplo clique)
    if fm["info_popup"]:
        info = fm["info_popup"]
        ippw, iph = 320, 180
        ipx = (W - ippw) // 2
        ipy = (H - iph) // 2

        # Fundo escurecido
        for yy in range(0, H, 4):
            rect(0, yy, W, 2, cor(0, 0, 0))

        rect(ipx, ipy, ippw, iph, PAINEL_BG)
        borda(ipx, ipy, ippw, iph, AZUL)
        rect(ipx, ipy, ippw, 28, CARD)
        texto(info["arquivo"]["nome"][:35], ipx + 10, ipy + 19, TXT)

        y = ipy + 45
        texto("Tipo:", ipx + 15, y, TXT_DIM)
        texto(info["tipo"], ipx + 90, y, TXT)
        y += 20
        texto("App:", ipx + 15, y, TXT_DIM)
        texto(info["app"], ipx + 90, y, TXT)
        y += 20
        texto("Tamanho:", ipx + 15, y, TXT_DIM)
        texto(info["arquivo"]["tamanho"], ipx + 90, y, TXT)
        y += 25

        if info["compativel"]:
            rect(ipx + 15, y, ippw - 30, 28, VERDE)
            texto_centro("COMPATIVEL - pode abrir", ipx + ippw // 2, y + 19, PRETO)
        else:
            rect(ipx + 15, y, ippw - 30, 28, VERMELHO)
            texto_centro("NAO SUPORTADO - sem app", ipx + ippw // 2, y + 19, BRANCO)

        # Botão fechar
        rect(ipx + ippw - 30, ipy + 5, 22, 22, VERMELHO)
        texto("X", ipx + ippw - 23, ipy + 21, BRANCO)

# ============ DESENHAR PAINEL ATIVO ============
def desenhar_painel():
    if painel_ativo == "wifi": desenhar_painel_wifi()
    elif painel_ativo == "bateria": desenhar_painel_bateria()
    elif painel_ativo == "hora": desenhar_painel_hora()
    elif painel_ativo == "config": desenhar_painel_config()

# ============ ÍCONES DO DESKTOP ============
icones = [
    ("Meu PC",   20, 20,  "icone_pc"),
    ("Lixeira",  20, 80,  "icone_lixeira"),
    ("Config",   20, 140, "icone_config"),
    ("Arquivos", 20, 200, "icone_arquivos"),
]

def desenhar_icones():
    for nome, ix, iy, key in icones:
        hov = (hover == key)
        c_bg = cor(0x40, 0x55, 0x80) if hov else cor(0x30, 0x40, 0x60)
        rect(ix, iy, 32, 32, c_bg)
        borda(ix, iy, 32, 32, AZUL if hov else cor(0x55, 0x66, 0x88))

        if key == "icone_pc":
            rect(ix + 6, iy + 8, 20, 14, cor(0x88, 0xAA, 0xDD))
            rect(ix + 6, iy + 8, 20, 1, BRANCO)
            rect(ix + 13, iy + 24, 6, 2, cor(0x88, 0xAA, 0xDD))
        elif key == "icone_lixeira":
            rect(ix + 8, iy + 10, 16, 18, cor(0x88, 0xAA, 0xDD))
            rect(ix + 6, iy + 8, 20, 3, BRANCO)
            rect(ix + 14, iy + 6, 4, 2, BRANCO)
        elif key == "icone_config":
            rect(ix + 12, iy + 10, 8, 12, cor(0xDD, 0xDD, 0xDD))
            rect(ix + 8, iy + 14, 16, 4, cor(0xDD, 0xDD, 0xDD))
            rect(ix + 14, iy + 8, 4, 16, cor(0xDD, 0xDD, 0xDD))
            rect(ix + 12, iy + 13, 8, 6, AZUL)
        elif key == "icone_arquivos":
            # Pasta amarela
            rect(ix + 6, iy + 12, 20, 14, AMARELO)
            rect(ix + 8, iy + 9, 8, 3, AMARELO)
            borda(ix + 6, iy + 12, 20, 14, cor(0xAA, 0x88, 0x22))

        texto(nome, ix, iy + 45, TXT)

# ============ RENDER ============
def desenhar_tudo():
    desenhar_wallpaper()
    desenhar_icones()
    desenhar_barra()

    if fm["ativo"]:
        desenhar_file_manager()
    elif painel_ativo:
        desenhar_painel()

    d.sync()
    d.flush()

# ============ HOVER ============
hover = None

def detectar_hover(mx, my):
    # Se file manager tá aberto, ele tem prioridade
    if fm["ativo"]:
        pw, ph = min(720, W - 30), min(520, H - 60)
        px = (W - pw) // 2
        py = (H - ph) // 2

        # Popup de info tem prioridade máxima
        if fm["info_popup"]:
            ippw, iph = 320, 180
            ipx = (W - ippw) // 2
            ipy = (H - iph) // 2
            if ipx + ippw - 30 <= mx <= ipx + ippw - 8 and ipy + 5 <= my <= ipy + 27:
                return "btn_info_fechar"
            return None

        # Botão X
        if px + pw - 30 <= mx <= px + pw - 8 and py + 5 <= my <= py + 27:
            return "btn_fm_fechar"

        # Botão voltar
        y_bar = py + 40
        if px + 15 <= mx <= px + 39 and y_bar + 3 <= my <= y_bar + 23:
            if fm["caminho"] != "/":
                return "btn_fm_voltar"

        # Sidebar
        sb_w = 130
        sb_y = y_bar + 35
        locais = ["/data/data/com.termux/files/home", "/sdcard/Download",
                  "/sdcard/DCIM", "/sdcard",
                  "/data/data/com.termux/files/usr"]
        for i in range(len(locais)):
            ly = sb_y + 35 + i * 24
            if px + 10 <= mx <= px + 10 + sb_w and ly - 12 <= my <= ly + 8:
                return f"loc_{i}"

        # Lista de arquivos
        lista_x = px + sb_w + 20
        lista_y = sb_y
        lista_h = ph - 90
        max_visiveis = (lista_h - 10) // 22
        for i in range(max_visiveis):
            ay = lista_y + 5 + i * 22
            if lista_x + 3 <= mx <= lista_x + (pw - sb_w - 30) and ay <= my <= ay + 20:
                return f"file_{i}"

        return None

    # Ícones do desktop
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
ultimo_clique_tempo = 0
ultimo_clique_alvo = None

def ao_clicar(mx, my, target):
    global painel_ativo, ultimo_clique_tempo, ultimo_clique_alvo

    # ========== FILE MANAGER ==========
    if fm["ativo"]:
        if target == "btn_fm_fechar":
            fechar_file_manager()
            return

        if target == "btn_info_fechar":
            fm["info_popup"] = None
            return

        if target == "btn_fm_voltar":
            pai = os.path.dirname(fm["caminho"].rstrip("/"))
            if pai:
                navegar_para(pai)
            return

        if target and target.startswith("loc_"):
            idx = int(target.split("_")[1])
            locais = ["/data/data/com.termux/files/home", "/sdcard/Download",
                      "/sdcard/DCIM", "/sdcard",
                      "/data/data/com.termux/files/usr"]
            navegar_para(locais[idx])
            return

        if target and target.startswith("file_"):
            idx = int(target.split("_")[1])
            lista_h = min(520, H - 60) - 90
            max_visiveis = (lista_h - 10) // 22
            scroll = fm["scroll"]
            idx_real = scroll + idx
            if idx_real >= len(fm["arquivos"]):
                return
            arq = fm["arquivos"][idx_real]

            # Detecção de duplo clique
            agora = time.time()
            duplo = (target == ultimo_clique_alvo and agora - ultimo_clique_tempo < 0.5)
            ultimo_clique_tempo = agora
            ultimo_clique_alvo = target

            if duplo:
                # Duplo clique!
                if arq["dir"]:
                    navegar_para(arq["caminho"])
                else:
                    mostrar_info_arquivo(arq)
            else:
                # Clique simples
                fm["selecionado"] = arq["nome"]
            return

        return

    # ========== DESKTOP ==========
    if target == "icone_arquivos":
        abrir_file_manager()
        return

    if target == "icone_config":
        painel_ativo = "config"
        atualizar_em_background()
        time.sleep(0.5)
        return

    if target == "icone_pc":
        print("Meu PC (nao implementado)")
        return

    if target == "icone_lixeira":
        print("Lixeira (vazia)")
        return

    if target == "btn_fechar_config":
        painel_ativo = None
        return

    if target == "btn_wifi":
        painel_ativo = None if painel_ativo == "wifi" else "wifi"
    elif target == "btn_bat":
        painel_ativo = None if painel_ativo == "bateria" else "bateria"
    elif target == "btn_hora":
        painel_ativo = None if painel_ativo == "hora" else "hora"
    else:
        if painel_ativo:
            painel_ativo = None

# ============ RENDER INICIAL ============
print("=== TinyOS Desktop v6 ===")
print("Atualizando dados via ADB...")
desenhar_tudo()
atualizar_em_background()
time.sleep(2)
desenhar_tudo()
print("")
print("Clique em 'Arquivos' no desktop")
print("Duplo clique num arquivo pra ver info")
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
                hover = detectar_hover(mx, my)
                ao_clicar(mx, my, hover)
                desenhar_tudo()
        elif ev.type == X.KeyPress:
            if ev.detail in (9, 67):
                if fm["ativo"]:
                    fechar_file_manager()
                else:
                    print("Saindo...")
                    rodando = False

    hora_atual = time.strftime("%H:%M")
    if hora_atual != ultima_hora_str:
        desenhar_tudo()
        ultima_hora_str = hora_atual

    if time.time() - ultimo_update > 15:
        atualizar_em_background()
        ultimo_update = time.time()

    if not eventos:
        time.sleep(0.1)

print("Fechando...")
win.destroy()
d.sync()
print("Adeus!")
PYEOF