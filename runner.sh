#!/data/data/com.termux/files/usr/bin/bash

# ============================================================
#  TinyOS Launcher v3
#  - Limpa X11
#  - Sobe X11 com TCP (sem -geometry)
#  - Roda OOBE
# ============================================================

LOG="$PREFIX/tmp/x11.log"

echo "=========================================="
echo "  TinyOS Launcher v3"
echo "=========================================="
echo ""

# 1. Limpa
echo "[1/5] Limpando X11 antigo..."
pkill -9 termux-x11 2>/dev/null
sleep 1
rm -f $PREFIX/tmp/.X11-unix/* 2>/dev/null
rm -f $LOG 2>/dev/null

# 2. Avisa resolucao
echo ""
echo "  NOTA: A resolucao 480p e definida no APP Termux:X11"
echo "  (Preferences -> Output -> 854x480)"
echo ""

# 3. Pede pro user abrir o app
echo "  >>> ABRA O APP 'Termux:X11' NO ANDROID <<<"
echo "  >>> Deixe aberto (tela preta)          <<<"
echo "  >>> Depois volte pro Termux             <<<"
echo ""
read -p "  Pressione ENTER quando estiver pronto... "

# 4. Sobe servidor COM TCP (SEM -geometry!)
echo ""
echo "[2/5] Iniciando termux-x11 (TCP)..."
termux-x11 :0 -ac -listen tcp > "$LOG" 2>&1 &
X11_PID=$!

sleep 4

# 5. Verifica
echo "[3/5] Verificando X11..."

if ! kill -0 $X11_PID 2>/dev/null; then
    echo "  ERRO: termux-x11 morreu!"
    cat "$LOG"
    exit 1
fi
echo "  OK - PID $X11_PID"

if [ ! -S "$PREFIX/tmp/.X11-unix/X0" ]; then
    echo "  AVISO: socket X0 nao criado"
fi

# 6. Exporta e testa
export DISPLAY=127.0.0.1:0
echo "  DISPLAY=$DISPLAY"

if python3 -c "from Xlib import display; d=display.Display(); s=d.screen(); print('  Tela:', s.width_in_pixels, 'x', s.height_in_pixels)" 2>/dev/null; then
    echo "[4/5] Conexao X11 OK"
else
    echo "  ERRO: Xlib nao conectou!"
    cat "$LOG"
    exit 1
fi

# 7. Roda OOBE
echo ""
echo "[5/5] Iniciando OOBE..."
echo ""
cd ~/tinyos
python3 oobe.py

echo ""
echo "=========================================="
echo "  OOBE encerrado"
echo "=========================================="

pkill -9 termux-x11 2>/dev/null
