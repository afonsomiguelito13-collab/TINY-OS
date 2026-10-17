cat > ~/TINY-OS/desktop.py << 'PYEOF'
from Xlib import X, display
import time
import subprocess
import threading
import re
import os
import json
import sys

# ============ SETUP ============
d = display.Display()
s = d.screen()
_root_geo = s.root.get_geometry()
W, H = _root_geo.width, _root_geo.height
print(f"TinyOS Desktop - Tela: {W}x{H}")

cmap = s.default_colormap
def cor(r, g, b): return cmap.alloc_color(r*257, g*257, b*257).pixel

PREFS_DIR = os.path.expanduser("~/.config/tinyos")
PREFS_FILE = os.path.join(PREFS_DIR, "prefs.json")
prefs = {"tema": "escuro"}
def carregar_prefs():
    try:
        os.makedirs(PREFS_DIR, exist_ok=True)
        if os.path.exists(PREFS_FILE):
            with open(PREFS_FILE) as f: prefs.update(json.load(f))
    except: pass
def salvar_prefs():
    try:
        os.makedirs(PREFS_DIR, exist_ok=True)
        with open(PREFS_FILE, "w") as f: json.dump(prefs, f)
    except: pass
carregar_prefs()

PALETA_ESCURO = {
    "PRETO": (0,0,0), "BRANCO": (255,255,255), "AZUL": (0x33,0x99,0xDD),
    "VERDE": (0x33,0xCC,0x66), "AMARELO": (0xDD,0xBB,0x33), "VERMELHO": (0xDD,0x44,0x44),
    "TXT": (0xE0,0xE0,0xE0), "TXT_DIM": (0x99,0x99,0x99),
    "PAINEL_BG": (0x1A,0x1E,0x24), "PAINEL_BORDA": (0x40,0x45,0x4C),
    "CARD": (0x25,0x2A,0x30), "CARD_HOV": (0x35,0x3B,0x43),
    "BG_WALL": [(0x10,0x05), (0x18,0x0A), (0x30,0x18)],
}
PALETA_CLARO = {
    "PRETO": (0,0,0), "BRANCO": (255,255,255), "AZUL": (0x00,0x78,0xD4),
    "VERDE": (0x22,0xAA,0x55), "AMARELO": (0xDD,0xAA,0x22), "VERMELHO": (0xDD,0x33,0x33),
    "TXT": (0x20,0x20,0x20), "TXT_DIM": (0x70,0x70,0x70),
    "PAINEL_BG": (0xF0,0xF0,0xF0), "PAINEL_BORDA": (0xBF,0xBF,0xBF),
    "CARD": (0xE0,0xE0,0xE0), "CARD_HOV": (0xD0,0xD0,0xD0),
    "BG_WALL": [(0xE8,0xD8), (0xE0,0xC8), (0xF0,0xE0)],
}

def get_paleta(): return PALETA_CLARO if prefs["tema"] == "claro" else PALETA_ESCURO

def atualizar_cores():
    global PRETO, BRANCO, AZUL, VERDE, AMARELO, VERMELHO, TXT, TXT_DIM, PAINEL_BG, PAINEL_BORDA, CARD, CARD_HOV, CORES_LINHA
    p = get_paleta()
    PRETO=cor(*p["PRETO"]); BRANCO=cor(*p["BRANCO"]); AZUL=cor(*p["AZUL"])
    VERDE=cor(*p["VERDE"]); AMARELO=cor(*p["AMARELO"]); VERMELHO=cor(*p["VERMELHO"])
    TXT=cor(*p["TXT"]); TXT_DIM=cor(*p["TXT_DIM"]); PAINEL_BG=cor(*p["PAINEL_BG"])
    PAINEL_BORDA=cor(*p["PAINEL_BORDA"]); CARD=cor(*p["CARD"]); CARD_HOV=cor(*p["CARD_HOV"])
    
    bg = p["BG_WALL"]; CORES_LINHA = []
    for y in range(H):
        t = y / H
        r=int(bg[0][0]+(bg[0][1]-bg[0][0])*t); g=int(bg[1][0]+(bg[1][1]-bg[1][0])*t); b=int(bg[2][0]+(bg[2][1]-bg[2][0])*t)
        CORES_LINHA.append(cor(r,g,b))

CORES_LINHA = []
atualizar_cores()

# ============ JANELA ============
win = s.root.create_window(0,0,W,H,1,s.root_depth,X.InputOutput,X.CopyFromParent,
    background_pixel=PRETO, event_mask=(X.ExposureMask|X.KeyPressMask|X.ButtonPressMask|X.ButtonReleaseMask))
win.set_wm_name("TinyOS Desktop")
win.map(); d.sync(); d.flush()

buffer = win.create_pixmap(W, H, s.root_depth)
gc = buffer.create_gc()

def rect(x,y,w,h,c): gc.change(foreground=c); buffer.fill_rectangle(gc,x,y,w,h)
def borda(x,y,w,h,c): gc.change(foreground=c); buffer.rectangle(gc,x,y,w,h)
def texto(txt,x,y,c=None):
    if c is None: c=TXT
    gc.change(foreground=c); buffer.draw_text(gc,x,y,txt.encode('latin-1','replace'),len(txt))
def texto_centro(txt,cx,y,c=None): texto(txt,cx-len(txt)*3,y,c)

# ============ ADB ============
def adb(comando, timeout=5):
    try:
        r = subprocess.run(["adb","shell",comando], capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except: return None

# ============ CACHE / DADOS ============
cache = {"wifi": {"conectado":False}, "bateria": {"nivel":"?"}, "uptime": "?"}

def atualizar_dados():
    try:
        bat = adb("dumpsys battery")
        if bat:
            m = re.search(r'level:\s*(\d+)', bat)
            if m: cache["bateria"]["nivel"] = m.group(1)
        up = adb("cat /proc/uptime")
        if up:
            seg = int(float(up.split()[0]))
            cache["uptime"] = f"{seg//3600}h {(seg%3600)//60}min"
    except: pass

threading.Thread(target=atualizar_dados, daemon=True).start()

# ============ WALLPAPER ============
ESTRELAS = [(50,30),(120,80),(200,25),(280,110),(350,45),(420,90),(500,20)]
def desenhar_wallpaper():
    for y in range(H): rect(0,y,W,1,CORES_LINHA[y])
    if prefs["tema"] == "escuro":
        for ex,ey in ESTRELAS:
            if ex < W and ey < H: rect(ex,ey,2,2,BRANCO)

# ============ BARRA ============
BARRA_H = 28; BARRA_Y = H - BARRA_H
def desenhar_barra():
    rect(0,BARRA_Y,W,BARRA_H,PAINEL_BG); rect(0,BARRA_Y,W,1,PAINEL_BORDA)
    texto(time.strftime("%H:%M"),10,BARRA_Y+19,TXT)
    texto(time.strftime("%d/%m"),55,BARRA_Y+19,TXT_DIM)
    bat = cache["bateria"]["nivel"]
    texto(bat+"%" if bat!="?" else "--", W-55, BARRA_Y+19, VERMELHO if bat!="?" and int(bat)<20 else VERDE)

# ============ CONFIG ============
painel_ativo = None
def desenhar_painel_config():
    pw,ph = min(600,W-40),min(400,H-80); px,py=(W-pw)//2,(H-ph)//2
    rect(px,py,pw,ph,PAINEL_BG); borda(px,py,pw,ph,PAINEL_BORDA)
    rect(px,py,pw,32,CARD); texto("Configuracoes",px+15,py+22,TXT)
    rect(px+pw-30,py+5,22,22,VERMELHO); texto("X",px+pw-23,py+21,BRANCO)
    y = py+50
    texto("Uptime: "+cache["uptime"], px+15, y, TXT); y+=20
    texto("Tema:", px+15, y, TXT_DIM)
    c = CARD_HOV if hover=="btn_tema" else CARD
    rect(px+60, y-12, 100, 20, c); borda(px+60, y-12, 100, 20, AZUL)
    texto_centro("Escuro" if prefs["tema"]=="escuro" else "Claro", px+110, y+4, TXT)

# ============ FUNÇÃO DE RODAR COMANDO ============
def executar_no_termux(comando, descricao):
    """Fecha a janela temporariamente, roda no Termux e volta"""
    print(f"\n>>> Executando: {comando}")
    
    # 1. Destroi a janela do X11 (pra liberar o terminal)
    win.destroy()
    d.sync()
    
    # 2. Roda o comando no terminal real (bloqueia até acabar)
    print(f"=== {descricao} ===")
    os.system(comando)
    print("=== Fim do comando ===")
    input("Pressione ENTER para voltar ao TinyOS...")
    
    # 3. Reinicia o script pra recriar a janela (e atualizar os ícones)
    print("Recarregando TinyOS...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ============ ÍCONES ============
icones = [
    ("Meu PC",   20, 20,  "icone_pc"),
    ("Lixeira",  20, 80,  "icone_lixeira"),
    ("Config",   20, 140, "icone_config"),
    ("Terminal", 20, 200, "icone_terminal"),
    ("App Store",20, 260, "icone_store"),
]

def desenhar_icones():
    for nome,ix,iy,key in icones:
        hov = (hover==key)
        rect(ix,iy,32,32,CARD_HOV if hov else CARD); borda(ix,iy,32,32,AZUL if hov else PAINEL_BORDA)
        
        if key=="icone_pc":
            rect(ix+6,iy+8,20,14,AZUL); rect(ix+13,iy+24,6,2,AZUL)
        elif key=="icone_lixeira":
            rect(ix+8,iy+10,16,18,TXT_DIM); rect(ix+6,iy+8,20,3,TXT)
        elif key=="icone_config":
            rect(ix+12,iy+10,8,12,TXT); rect(ix+8,iy+14,16,4,TXT); rect(ix+14,iy+8,4,16,TXT)
        elif key=="icone_terminal":
            rect(ix+5,iy+8,22,16,PRETO); borda(ix+5,iy+8,22,16,VERDE)
            texto(">_",ix+8,iy+20,VERDE)
        elif key=="icone_store":
            rect(ix+8,iy+8,16,16,AZUL); texto("ST",ix+12,iy+20,BRANCO)
            
        texto(nome,ix,iy+45,TXT)

def desenhar_tudo():
    desenhar_wallpaper(); desenhar_icones(); desenhar_barra()
    if painel_ativo == "config": desenhar_painel_config()
    win.copy_area(gc, buffer, 0,0,W,H,0,0); d.sync(); d.flush()

# ============ HOVER / CLIQUE ============
hover = None
def detectar_hover(mx,my):
    for nome,ix,iy,key in icones:
        if ix<=mx<=ix+32 and iy<=my<=iy+32: return key
    if painel_ativo == "config":
        pw,ph=min(600,W-40),min(400,H-80); px,py=(W-pw)//2,(H-ph)//2
        if px+pw-30<=mx<=px+pw-8 and py+5<=my<=py+27: return "btn_fechar_config"
        if px+60<=mx<=px+160 and py+90<=my<=py+110: return "btn_tema"
    return None

def ao_clicar(target):
    global painel_ativo
    if target == "icone_terminal":
        executar_no_termux("bash", "Abrindo Terminal do Termux")
    elif target == "icone_store":
        executar_no_termux("bash getapp.sh", "TinyOS App Store")
    elif target == "icone_config": painel_ativo="config"
    elif target == "btn_tema":
        prefs["tema"] = "claro" if prefs["tema"]=="escuro" else "escuro"
        salvar_prefs(); atualizar_cores()
    elif target == "btn_fechar_config": painel_ativo=None

# ============ INICIAL ============
desenhar_tudo()

# ============ LOOP ============
rodando = True
while rodando:
    while d.pending_events():
        ev = d.next_event()
        if ev.type == X.Expose: desenhar_tudo()
        elif ev.type == X.ButtonPress:
            if ev.detail == 1:
                hover = detectar_hover(ev.event_x, ev.event_y)
                ao_clicar(hover); desenhar_tudo()
        elif ev.type == X.KeyPress:
            if ev.detail in (9, 67):
                if painel_ativo: painel_ativo = None; desenhar_tudo()
                else: rodando = False
    time.sleep(0.05)

win.destroy(); d.sync()
PYEOF