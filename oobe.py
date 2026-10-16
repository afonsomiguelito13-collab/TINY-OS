from Xlib import X, display
import time
import os
import subprocess
import re

# ============ SETUP ============
d = display.Display()
s = d.screen()
W, H = s.width_in_pixels, s.height_in_pixels

cmap = s.default_colormap
def cor(r, g, b):
    return cmap.alloc_color(r*257, g*257, b*257).pixel

BG       = cor(0x20, 0x24, 0x2A)
CARD     = cor(0x2A, 0x2F, 0x36)
CARD_HOV = cor(0x35, 0x3B, 0x43)
AZUL     = cor(0x00, 0x78, 0xD4)
AZUL_HOV = cor(0x1A, 0x88, 0xE4)
VERDE    = cor(0x33, 0xCC, 0x66)
VERDE_HV = cor(0x55, 0xDD, 0x88)
VERMELHO = cor(0xDD, 0x44, 0x44)
AMARELO  = cor(0xDD, 0xBB, 0x33)
AMARELO_HV = cor(0xEE, 0xCC, 0x44)
TXT      = cor(0xF0, 0xF0, 0xF0)
TXT_DIM  = cor(0x99, 0x99, 0x99)
CINZA    = cor(0x3C, 0x3C, 0x3C)
BRANCO   = cor(0xFF, 0xFF, 0xFF)

win = s.root.create_window(
    0, 0, W, H, 1,
    s.root_depth,
    X.InputOutput,
    X.CopyFromParent,
    background_pixel=BG,
    event_mask=(X.ExposureMask | X.KeyPressMask |
                X.ButtonPressMask | X.PointerMotionMask)
)
win.set_wm_name("TinyOS - Configuracao Inicial")
win.map()
d.sync()
d.flush()
time.sleep(0.2)

gc = win.create_gc()

# ============ HELPERS ============
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

def botao(x, y, w, h, txt, cor_bg, cor_txt=BRANCO, cor_borda=None):
    rect(x, y, w, h, cor_bg)
    if cor_borda:
        borda(x, y, w, h, cor_borda)
    texto_centro(txt, x + w // 2, y + h // 2 + 5, cor_txt)

# ============ CPU METER ============
CPU_HIST = [0.0] * 60
_last_idle = 0
_last_total = 0

def ler_cpu():
    try:
        with open('/proc/stat') as f:
            linha = f.readline()
        campos = [int(x) for x in linha.split()[1:]]
        idle = campos[3] + campos[4]
        total = sum(campos)
        return idle, total
    except:
        return 0, 0

def init_cpu():
    global _last_idle, _last_total
    _last_idle, _last_total = ler_cpu()

def cpu_uso():
    global _last_idle, _last_total
    idle, total = ler_cpu()
    d_idle = idle - _last_idle
    d_total = total - _last_total
    _last_idle, _last_total = idle, total
    if d_total <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - (d_idle / d_total)))

init_cpu()
time.sleep(0.2)
init_cpu()

def desenhar_cpu(x, y, w, h):
    uso = cpu_uso()
    CPU_HIST.append(uso)
    if len(CPU_HIST) > w:
        CPU_HIST.pop(0)
    rect(x, y, w, h, cor(0x15, 0x18, 0x1C))
    borda(x, y, w, h, cor(0x40, 0x45, 0x4C))
    for i, val in enumerate(CPU_HIST):
        bh = int((h - 2) * val)
        if bh > 0:
            if val < 0.5: c = VERDE
            elif val < 0.8: c = AMARELO
            else: c = VERMELHO
            rect(x + 1 + i, y + h - 1 - bh, 1, bh, c)
    texto(str(int(uso * 100)) + "%", x + w + 6, y + h - 4, TXT_DIM)

# ============ ADB ============
def adb_cmd(comando, timeout=5):
    try:
        r = subprocess.run(
            ["adb", "shell", comando],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except:
        return None

def adb_disponivel():
    try:
        r = subprocess.run(
            ["adb", "devices"],
            capture_output=True, text=True, timeout=3
        )
        for linha in r.stdout.strip().split('\n')[1:]:
            if '\tdevice' in linha:
                return True
        return False
    except:
        return False

def scan_wifi():
    redes = []
    if not adb_disponivel():
        return redes
    out = adb_cmd("cmd wifi list-networks")
    if out:
        for linha in out.split('\n'):
            m = re.match(r'^\s*(.+?)\s+(-?\d+)\s+(\S+)\s*(.*)$', linha)
            if m:
                ssid = m.group(1).strip()
                if ssid and ssid != 'SSID':
                    redes.append({
                        "ssid": ssid,
                        "sinal": m.group(2),
                        "seg": m.group(3),
                        "conectado": 'connected' in m.group(4).lower()
                    })
    if not redes:
        out = adb_cmd("dumpsys wifi | grep -E 'SSID:' | head -20")
        if out:
            for linha in out.split('\n'):
                m = re.search(r'SSID:\s*"?([^"]+)"?', linha)
                if m:
                    ssid = m.group(1).strip()
                    if ssid and ssid != '<unknown ssid>':
                        redes.append({"ssid": ssid, "sinal": "?", "seg": "?", "conectado": False})
    return redes

def wifi_atual():
    if not adb_disponivel():
        return None
    out = adb_cmd("dumpsys wifi | grep -m1 'mWifiInfo'")
    if out:
        m = re.search(r'SSID:\s*"?([^",]+)"?', out)
        if m:
            return m.group(1).strip()
    return None

def verificar_device_info():
    info = {}
    if not adb_disponivel():
        return info
    campos = {
        "modelo": "getprop ro.product.model",
        "fabricante": "getprop ro.product.manufacturer",
        "android": "getprop ro.build.version.release",
        "hostname": "getprop net.hostname",
        "bateria": "dumpsys battery | grep level",
    }
    for chave, cmd in campos.items():
        out = adb_cmd(cmd)
        if out:
            if chave == "bateria":
                m = re.search(r'level:\s*(\d+)', out)
                if m:
                    info[chave] = m.group(1) + "%"
            else:
                info[chave] = out.strip()
    return info

# ============ ESTADO ============
estado = {
    "idioma": "Portugues (Brasil)",
    "usuario": "",
    "hostname": "tinyos",
    "senha_definida": False,
    "senha_pulada": False,
    "rede": "Wi-Fi",
    "tema": "Escuro",
    "animacao": "Ativadas",
    "redes": [],
    "rede_selecionada": None,
    "wifi_atual": None,
    "escaneando": False,
    "device_info": None,
    "scroll_wifi": 0,
}

etapa = 1
TOTAL_ETAPAS = 6
mouse_x, mouse_y = 0, 0
hover = None

# ============ HEADER / PROGRESSO / BOTÕES ============
def desenhar_header(titulo, subtitulo=""):
    texto(titulo, 40, 55, TXT)
    if subtitulo:
        texto(subtitulo, 40, 75, TXT_DIM)
    rect(40, 85, W - 80, 1, CINZA)

def desenhar_progresso():
    y = H - 70
    tam = 10
    gap = 18
    total_w = TOTAL_ETAPAS * tam + (TOTAL_ETAPAS - 1) * gap
    x0 = (W - total_w) // 2
    for i in range(TOTAL_ETAPAS):
        cx = x0 + i * (tam + gap)
        if i + 1 <= etapa:
            rect(cx, y, tam, tam, AZUL)
            if i + 1 == etapa:
                borda(cx - 2, y - 2, tam + 4, tam + 4, AZUL)
        else:
            rect(cx, y, tam, tam, CINZA)
    texto_centro("Etapa " + str(etapa) + " de " + str(TOTAL_ETAPAS),
                 W // 2, y + 30, TXT_DIM)

def desenhar_botoes(voltar_ativo=True, continuar_txt="Continuar", pular=False):
    y = H - 40
    bx = 40
    c = CARD_HOV if hover == "voltar" else CARD
    botao(bx, y, 90, 28, "Voltar", c if voltar_ativo else cor(0x25, 0x28, 0x2D),
          TXT if voltar_ativo else TXT_DIM)

    # Botão Pular (só quando pular=True)
    if pular:
        px = W // 2 - 45
        c_p = AMARELO_HV if hover == "pular" else AMARELO
        botao(px, y, 90, 28, "Pular", c_p, cor(0x1A, 0x1A, 0x1A))

    bx2 = W - 130
    c2 = AZUL_HOV if hover == "continuar" else AZUL
    botao(bx2, y, 90, 28, continuar_txt, c2)

# ============ ETAPAS ============
def desenhar_etapa_1():
    desenhar_header("Idioma e regiao", "Escolha o idioma do sistema")
    opcoes = [
        ("Portugues (Brasil)", "idioma_pt"),
        ("English (United States)", "idioma_en"),
        ("Espanol", "idioma_es"),
    ]
    y0 = 130
    for i, (nome, key) in enumerate(opcoes):
        y = y0 + i * 45
        sel = (estado["idioma"] == nome)
        hov = (hover == key)
        c = CARD_HOV if hov else CARD
        rect(60, y, W - 120, 36, c)
        if sel:
            borda(60, y, W - 120, 36, AZUL)
            rect(75, y + 13, 10, 10, AZUL)
            rect(78, y + 16, 4, 4, BRANCO)
        else:
            borda(60, y, W - 120, 36, CINZA)
            borda(75, y + 13, 10, 10, TXT_DIM)
        texto(nome, 100, y + 22, TXT)

def desenhar_etapa_2():
    desenhar_header("Conta de usuario", "Digite um nome para sua conta")
    y = 140
    rect(60, y, W - 120, 36, CARD)
    borda(60, y, W - 120, 36, AZUL if hover == "input_user" else CINZA)
    nome = estado["usuario"] if estado["usuario"] else "Digite aqui..."
    c = TXT if estado["usuario"] else TXT_DIM
    texto(nome, 75, y + 22, c)

    if estado["usuario"] and int(time.time() * 2) % 2 == 0:
        cx = 75 + len(estado["usuario"]) * 6
        rect(cx, y + 8, 1, 20, AZUL)

    if estado["usuario"]:
        if len(estado["usuario"]) < 2:
            texto("Nome muito curto (min 2)", 60, y + 60, VERMELHO)
        elif len(estado["usuario"]) > 16:
            texto("Nome muito longo (max 16)", 60, y + 60, VERMELHO)
        else:
            texto("OK", 60, y + 60, VERDE)

    texto("Hostname: " + estado["hostname"], 60, y + 90, TXT_DIM)

def desenhar_etapa_3():
    desenhar_header("Senha", "Defina uma senha ou pule esta etapa")
    y = 140

    # Campo senha
    rect(60, y, W - 120, 36, CARD)
    borda(60, y, W - 120, 36, AZUL if hover == "input_senha" else CINZA)
    if estado["senha_definida"]:
        texto("************", 75, y + 22, TXT)
    elif estado["senha_pulada"]:
        texto("(senha pulada)", 75, y + 22, AMARELO)
    else:
        texto("Digite a senha...", 75, y + 22, TXT_DIM)

    # Campo confirmar
    y2 = y + 55
    rect(60, y2, W - 120, 36, CARD)
    borda(60, y2, W - 120, 36, CINZA)
    if estado["senha_pulada"]:
        texto("(nao precisa)", 75, y2 + 22, TXT_DIM)
    else:
        texto("Confirmar senha...", 75, y2 + 22, TXT_DIM)

    # Aviso
    if estado["senha_pulada"]:
        texto("AVISO: Sem senha o sistema fica inseguro!", 60, y2 + 60, AMARELO)
        texto("Voce pode definir depois nas Configuracoes.", 60, y2 + 80, TXT_DIM)
    else:
        texto("Dica: pelo menos 8 caracteres", 60, y2 + 60, TXT_DIM)
        texto("Ou clique em PULAR para nao usar senha.", 60, y2 + 80, TXT_DIM)

def desenhar_etapa_4():
    desenhar_header("Rede", "Escolha a rede Wi-Fi")
    y_status = 105
    rect(60, y_status, W - 120, 30, CARD)
    borda(60, y_status, W - 120, 30, CINZA)
    if estado["wifi_atual"]:
        texto("Conectado em: " + estado["wifi_atual"], 75, y_status + 20, VERDE)
    else:
        texto("Nao conectado (ou ADB offline)", 75, y_status + 20, TXT_DIM)

    y_scan = 145
    c_scan = VERDE_HV if hover == "btn_scan" else VERDE
    botao(60, y_scan, 140, 32, "Escanear Wi-Fi", c_scan, BRANCO)

    if estado["escaneando"]:
        texto("Encontrando Wi-Fi proximos...", 220, y_scan + 20, AMARELO)

    y_lista = 190
    altura_lista = H - y_lista - 110

    if not estado["redes"]:
        rect(60, y_lista, W - 120, altura_lista, CARD)
        borda(60, y_lista, W - 120, altura_lista, CINZA)
        if estado["escaneando"]:
            texto("Procurando redes...", 80, y_lista + 30, TXT_DIM)
        elif estado["wifi_atual"]:
            texto("Clique em ESCANEAR para ver redes proximas", 80, y_lista + 30, TXT_DIM)
        else:
            texto("ADB offline - rode: adb connect <ip>:<porta>", 80, y_lista + 30, TXT_DIM)
    else:
        max_visiveis = altura_lista // 28
        scroll = estado["scroll_wifi"]
        redes_visiveis = estado["redes"][scroll:scroll + max_visiveis]

        for i, r in enumerate(redes_visiveis):
            y = y_lista + i * 28
            sel = (estado["rede_selecionada"] == r["ssid"])
            hov = (hover == "wifi_" + str(i))
            c = CARD_HOV if hov else CARD
            rect(60, y, W - 120, 26, c)
            borda(60, y, W - 120, 26, AZUL if sel else CINZA)

            sinal = r.get("sinal", "?")
            if sinal != "?":
                try:
                    sv = int(sinal)
                    if sv > -50: c_sinal = VERDE
                    elif sv > -70: c_sinal = AMARELO
                    else: c_sinal = VERMELHO
                except:
                    c_sinal = TXT_DIM
            else:
                c_sinal = TXT_DIM

            rect(70, y + 9, 3, 8, c_sinal)
            rect(75, y + 6, 3, 11, c_sinal)
            rect(80, y + 3, 3, 14, c_sinal)

            texto(r["ssid"][:35], 92, y + 18, TXT)

            if r.get("conectado"):
                texto("[OK]", W - 110, y + 18, VERDE)
            elif sel:
                texto(">>>", W - 110, y + 18, AZUL)

def desenhar_etapa_5():
    desenhar_header("Aparencia", "Personalize a interface")
    texto("Tema:", 60, 120, TXT)
    temas = [("Escuro", "tema_esc"), ("Claro", "tema_cla")]
    for i, (nome, key) in enumerate(temas):
        x = 60 + i * 130
        y = 135
        sel = estado["tema"] == nome
        hov = hover == key
        c = CARD_HOV if hov else CARD
        rect(x, y, 120, 60, c)
        if sel:
            borda(x, y, 120, 60, AZUL)
        else:
            borda(x, y, 120, 60, CINZA)
        cor_prev = cor(0x20, 0x24, 0x2A) if nome == "Escuro" else cor(0xF0, 0xF0, 0xF0)
        rect(x + 10, y + 10, 100, 25, cor_prev)
        texto_centro(nome, x + 60, y + 52, TXT)

    texto("Animacoes:", 60, 230, TXT)
    anims = [("Ativadas", "anim_on"), ("Desativadas", "anim_off")]
    for i, (nome, key) in enumerate(anims):
        x = 60 + i * 150
        y = 245
        sel = estado["animacao"] == nome
        hov = hover == key
        c = CARD_HOV if hov else CARD
        rect(x, y, 140, 36, c)
        if sel:
            borda(x, y, 140, 36, AZUL)
            rect(x + 12, y + 13, 10, 10, AZUL)
            rect(x + 15, y + 16, 4, 4, BRANCO)
        else:
            borda(x, y, 140, 36, CINZA)
            borda(x + 12, y + 13, 10, 10, TXT_DIM)
        texto(nome, x + 32, y + 22, TXT)

def desenhar_etapa_6():
    desenhar_header("Tudo pronto!", "Revise antes de comecar")
    if estado["device_info"] is None:
        estado["device_info"] = verificar_device_info()

    senha_txt = "Definida"
    if estado["senha_pulada"]:
        senha_txt = "(pulada)"
    elif not estado["senha_definida"]:
        senha_txt = "(nao definida)"

    itens = [
        ("Idioma", estado["idioma"]),
        ("Usuario", estado["usuario"] or "(nao definido)"),
        ("Hostname", estado["hostname"]),
        ("Senha", senha_txt),
        ("Wi-Fi", estado["wifi_atual"] or "(nao conectado)"),
        ("Tema", estado["tema"]),
    ]
    y0 = 105
    for i, (k, v) in enumerate(itens):
        y = y0 + i * 20
        texto(k + ":", 60, y, TXT_DIM)
        texto(v[:40], 200, y, TXT)

    y_dev = y0 + len(itens) * 20 + 15
    if estado["device_info"]:
        texto("--- Dispositivo ---", 60, y_dev, VERDE)
        campos = [
            ("Modelo", estado["device_info"].get("modelo", "?")),
            ("Android", estado["device_info"].get("android", "?")),
            ("Bateria", estado["device_info"].get("bateria", "?")),
        ]
        for i, (k, v) in enumerate(campos):
            y = y_dev + 20 + i * 20
            texto(k + ":", 60, y, TXT_DIM)
            texto(v, 200, y, TXT)
    else:
        texto("(Sem dados do ADB)", 60, y_dev, TXT_DIM)

def desenhar():
    rect(0, 0, W, H, BG)
    if etapa == 1: desenhar_etapa_1()
    elif etapa == 2: desenhar_etapa_2()
    elif etapa == 3: desenhar_etapa_3()
    elif etapa == 4: desenhar_etapa_4()
    elif etapa == 5: desenhar_etapa_5()
    elif etapa == 6: desenhar_etapa_6()

    desenhar_cpu(W - 180, 20, 120, 24)
    texto("TinyOS", 40, 25, TXT_DIM)
    desenhar_progresso()
    txt_cont = "Iniciar" if etapa == TOTAL_ETAPAS else "Continuar"
    desenhar_botoes(voltar_ativo=(etapa > 1),
                    continuar_txt=txt_cont,
                    pular=(etapa == 3))
    d.sync()
    d.flush()

# ============ HOVER ============
def detectar_hover(mx, my):
    y_btn = H - 40
    if 40 <= mx <= 130 and y_btn <= my <= y_btn + 28: return "voltar"
    if W - 130 <= mx <= W - 40 and y_btn <= my <= y_btn + 28: return "continuar"
    if etapa == 3 and W // 2 - 45 <= mx <= W // 2 + 45 and y_btn <= my <= y_btn + 28:
        return "pular"

    if etapa == 1:
        y0 = 130
        for i in range(3):
            y = y0 + i * 45
            if 60 <= mx <= W - 60 and y <= my <= y + 36:
                return ["idioma_pt", "idioma_en", "idioma_es"][i]

    if etapa == 2:
        if 60 <= mx <= W - 60 and 140 <= my <= 176:
            return "input_user"

    if etapa == 3:
        if 60 <= mx <= W - 60 and 140 <= my <= 176:
            return "input_senha"

    if etapa == 4:
        if 60 <= mx <= 200 and 145 <= my <= 177:
            return "btn_scan"
        y_lista = 190
        altura_lista = H - y_lista - 110
        max_visiveis = altura_lista // 28
        for i in range(max_visiveis):
            y = y_lista + i * 28
            if 60 <= mx <= W - 60 and y <= my <= y + 26:
                return "wifi_" + str(i)

    if etapa == 5:
        for i, key in enumerate(["tema_esc", "tema_cla"]):
            x = 60 + i * 130
            if x <= mx <= x + 120 and 135 <= my <= 195: return key
        for i, key in enumerate(["anim_on", "anim_off"]):
            x = 60 + i * 150
            if x <= mx <= x + 140 and 245 <= my <= 281: return key

    return None

# ============ AÇÃO ============
def ao_clicar(target):
    global etapa
    if target == "continuar":
        if etapa < TOTAL_ETAPAS:
            if etapa == 2:
                if len(estado["usuario"].strip()) < 2:
                    print("! Nome muito curto"); return
            if etapa == 3:
                if not estado["senha_definida"] and not estado["senha_pulada"]:
                    print("! Defina senha ou clique em Pular"); return
            etapa += 1
            print("-> Etapa", etapa)
        else:
            print("-> Iniciando TinyOS...")
            return "fim"

    elif target == "voltar":
        if etapa > 1:
            etapa -= 1
            print("<- Etapa", etapa)

    elif target == "pular":
        estado["senha_pulada"] = True
        estado["senha_definida"] = False
        print("Senha pulada. Avancando...")
        etapa += 1
        print("-> Etapa", etapa)

    elif target == "idioma_pt": estado["idioma"] = "Portugues (Brasil)"
    elif target == "idioma_en": estado["idioma"] = "English (United States)"
    elif target == "idioma_es": estado["idioma"] = "Espanol"

    elif target == "btn_scan":
        print("Escaneando Wi-Fi...")
        estado["escaneando"] = True
        estado["redes"] = []
        estado["rede_selecionada"] = None
        desenhar()

        estado["wifi_atual"] = wifi_atual()
        estado["redes"] = scan_wifi()
        estado["escaneando"] = False
        print("  Encontradas:", len(estado["redes"]), "redes")
        if estado["wifi_atual"]:
            print("  Conectado em:", estado["wifi_atual"])

    elif target and target.startswith("wifi_"):
        idx = int(target.split("_")[1])
        y_lista = 190
        altura_lista = H - y_lista - 110
        max_visiveis = altura_lista // 28
        scroll = estado["scroll_wifi"]
        idx_real = scroll + idx
        if idx_real < len(estado["redes"]):
            r = estado["redes"][idx_real]
            estado["rede_selecionada"] = r["ssid"]
            print("Selecionado:", r["ssid"])

    elif target == "tema_esc": estado["tema"] = "Escuro"
    elif target == "tema_cla": estado["tema"] = "Claro"
    elif target == "anim_on": estado["animacao"] = "Ativadas"
    elif target == "anim_off": estado["animacao"] = "Desativadas"

    elif target == "input_user":
        if not estado["usuario"]:
            estado["usuario"] = "user"
        elif len(estado["usuario"]) < 16:
            estado["usuario"] += "x"

    elif target == "input_senha":
        # Simula digitação: marca como definida
        estado["senha_definida"] = True
        estado["senha_pulada"] = False
        print("Senha definida (simulada)")

    return None

# ============ LOOP ============
print("=== TinyOS OOBE v3 ===")
print("Tela:", W, "x", H)
print("")

rodando = True
desenhar()

while rodando:
    while d.pending_events():
        ev = d.next_event()
        if ev.type == X.Expose:
            desenhar()
        elif ev.type == X.MotionNotify:
            mouse_x, mouse_y = ev.event_x, ev.event_y
            novo = detectar_hover(mouse_x, mouse_y)
            if novo != hover:
                hover = novo
                desenhar()
        elif ev.type == X.ButtonPress:
            if ev.detail == 1:
                target = detectar_hover(ev.event_x, ev.event_y)
                if target:
                    res = ao_clicar(target)
                    if res == "fim":
                        rodando = False
                    desenhar()
        elif ev.type == X.KeyPress:
            if ev.detail == 9:
                print("ESC"); rodando = False
            elif etapa == 2:
                if 24 <= ev.detail <= 58:
                    letra = chr(ev.detail + 93 - 32).lower()
                    if len(estado["usuario"]) < 16:
                        estado["usuario"] += letra
                        desenhar()
                elif ev.detail == 22:
                    estado["usuario"] = estado["usuario"][:-1]
                    desenhar()

    desenhar()
    time.sleep(0.5)

# ============ FIM ============
print("")
print("=== Configuracao concluida ===")
for k, v in estado.items():
    if k in ("redes", "device_info"): continue
    print(" ", k, "=", v)
print("")
print("Fechando OOBE...")
win.destroy()
d.sync()

import os
script_dir = os.path.dirname(os.path.abspath(__file__))
desktop = os.path.join(script_dir, "desktop.py")
print("Abrindo desktop...")
subprocess.run(["python3", desktop])
