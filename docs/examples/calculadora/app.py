#!/usr/bin/env python3
from Xlib import X, display
import time

# Configuracoes da Janela
W, H = 300, 400

# Cores (Formato RGB)
COR_BG     = (0x20, 0x24, 0x2A) # Fundo
COR_DISP   = (0x10, 0x14, 0x18) # Display
COR_BTN    = (0x35, 0x3B, 0x43) # Botoes normais
COR_OP     = (0x00, 0x78, 0xD4) # Botoes de operacao (Azul)
COR_IGUAL  = (0x33, 0xCC, 0x66) # Botao igual (Verde)
COR_TXT    = (0xE0, 0xE0, 0xE0) # Texto
COR_TXT_D  = (0x99, 0x99, 0x99) # Texto display

d = display.Display()
s = d.screen()
cmap = s.default_colormap

def cor(rgb):
    return cmap.alloc_color(rgb[0]*257, rgb[1]*257, rgb[2]*257).pixel

# Criar janela
win = s.root.create_window(
    50, 50, W, H, 1,
    s.root_depth, X.InputOutput, X.CopyFromParent,
    background_pixel=cor(COR_BG),
    event_mask=X.ExposureMask | X.ButtonPressMask
)
win.set_wm_name("Calculadora TinyOS")
win.map()
d.sync()

gc = win.create_gc()

# Layout dos botoes (Texto, X, Y, Largura, Altura, Tipo)
botoes = [
    ("C",  10, 110, 60, 50, "op"), ("<",  80, 110, 60, 50, "op"), ("/", 150, 110, 60, 50, "op"), ("*", 220, 110, 60, 50, "op"),
    ("7",  10, 170, 60, 50, "num"), ("8",  80, 170, 60, 50, "num"), ("9", 150, 170, 60, 50, "num"), ("-", 220, 170, 60, 50, "op"),
    ("4",  10, 230, 60, 50, "num"), ("5",  80, 230, 60, 50, "num"), ("6", 150, 230, 60, 50, "num"), ("+", 220, 230, 60, 50, "op"),
    ("1",  10, 290, 60, 50, "num"), ("2",  80, 290, 60, 50, "num"), ("3", 150, 290, 60, 50, "num"), ("=", 220, 290, 60, 50, "eq"),
    ("0",  10, 350, 130, 40, "num"), (".", 150, 350, 60, 40, "num")
]

expressao = ""
resultado = ""

def desenhar():
    # Fundo
    gc.change(foreground=cor(COR_BG))
    win.fill_rectangle(gc, 0, 0, W, H)

    # Display
    gc.change(foreground=cor(COR_DISP))
    win.fill_rectangle(gc, 10, 10, 280, 80)
    
    # Texto da expressao
    gc.change(foreground=cor(COR_TXT))
    txt_expressao = expressao[-20:] if len(expressao) > 20 else expressao
    win.draw_text(gc, 20, 50, txt_expressao.encode('latin-1'), len(txt_expressao))
    
    # Texto do resultado
    gc.change(foreground=cor(COR_TXT_D))
    txt_res = resultado[-15:] if len(resultado) > 15 else resultado
    win.draw_text(gc, 20, 80, txt_res.encode('latin-1'), len(txt_res))

    # Botoes
    for (txt, x, y, w, h, tipo) in botoes:
        if tipo == "num": c = cor(COR_BTN)
        elif tipo == "op": c = cor(COR_OP)
        else: c = cor(COR_IGUAL)

        gc.change(foreground=c)
        win.fill_rectangle(gc, x, y, w, h)
        
        # Texto do botao
        gc.change(foreground=cor(COR_TXT))
        win.draw_text(gc, x + (w//2) - 4, y + (h//2) + 5, txt.encode('latin-1'), len(txt))

    d.sync()

def clicar_botao(x, y):
    global expressao, resultado
    for (txt, bx, by, bw, bh, tipo) in botoes:
        if bx <= x <= bx+bw and by <= y <= by+bh:
            if txt == "C":
                expressao = ""
                resultado = ""
            elif txt == "<":
                expressao = expressao[:-1]
            elif txt == "=":
                try:
                    # Substitui simbolos visuais por operadores Python
                    exp_py = expressao.replace('x', '*').replace('÷', '/')
                    resultado = str(eval(exp_py))
                except:
                    resultado = "Erro"
            else:
                expressao += txt
            desenhar()
            return

desenhar()

# Loop de eventos
while True:
    ev = d.next_event()
    if ev.type == X.Expose:
        desenhar()
    elif ev.type == X.ButtonPress:
        clicar_botao(ev.event_x, ev.event_y)
