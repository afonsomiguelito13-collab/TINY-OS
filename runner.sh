cat > ~/TINY-OS/runner.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash

# ============================================================
#  TinyOS - Launcher + Installer
#  Copyright (C) 2026 Afonso Miguel
#  Licenca: GPL v3 - Veja LICENSE
# ============================================================

REPO_URL="https://raw.githubusercontent.com/afonsomiguelito13-collab/TINY-OS/main"
DIR_SCRIPT="$(cd "$(dirname "$0")" && pwd)"
LOG="$PREFIX/tmp/x11.log"
MODO="${1:-completo}"

echo "=========================================="
echo "  TinyOS Launcher v0.1"
echo "=========================================="
echo ""

# ============================================================
# 1. Verifica/baixa dependencias
# ============================================================
echo "[1/7] Verificando arquivos..."

faltando=0

if [ ! -f "$DIR_SCRIPT/desktop.py" ]; then
    echo "  desktop.py NAO encontrado"
    faltando=1
fi

if [ ! -f "$DIR_SCRIPT/oobe.py" ]; then
    echo "  oobe.py NAO encontrado"
    faltando=1
fi

if [ $faltando -eq 1 ]; then
    echo ""
    echo "[2/7] Baixando arquivos do GitHub..."

    if ! command -v curl >/dev/null 2>&1; then
        echo "  Instalando curl..."
        pkg install curl -y
    fi

    echo "  Baixando desktop.py..."
    curl -sSL "$REPO_URL/desktop.py" -o "$DIR_SCRIPT/desktop.py"
    if [ ! -f "$DIR_SCRIPT/desktop.py" ]; then
        echo "  ERRO: falhou ao baixar desktop.py"
        exit 1
    fi

    echo "  Baixando oobe.py..."
    curl -sSL "$REPO_URL/oobe.py" -o "$DIR_SCRIPT/oobe.py"
    if [ ! -f "$DIR_SCRIPT/oobe.py" ]; then
        echo "  ERRO: falhou ao baixar oobe.py"
        exit 1
    fi

    echo "  OK - arquivos baixados"
else
    echo "  OK - todos os arquivos ja existem"
    echo "[2/7] Pulando download"
fi

# ============================================================
# 2. Verifica dependencias do sistema
# ============================================================
echo ""
echo "[3/7] Verificando dependencias do Termux..."

# python
if ! command -v python3 >/dev/null 2>&1; then
    echo "  Instalando python..."
    pkg install python -y
fi

# python-xlib
if ! python3 -c "import Xlib" 2>/dev/null; then
    echo "  Instalando python-xlib..."
    pkg install python-xlib -y 2>/dev/null || pip install python-xlib
fi

# termux-x11
if ! command -v termux-x11 >/dev/null 2>&1; then
    echo "  Instalando termux-x11-nightly..."
    pkg install termux-x11-nightly -y
fi

echo "  OK - dependencias instaladas"

# ============================================================
# 3. Limpa X11 antigo
# ============================================================
echo ""
echo "[4/7] Limpando X11 antigo..."
pkill -9 termux-x11 2>/dev/null
sleep 1
rm -f $PREFIX/tmp/.X11-unix/* 2>/dev/null
rm -f "$LOG" 2>/dev/null

# ============================================================
# 4. Pede pro user abrir o app
# ============================================================
echo ""
echo "  >>> ABRA O APP 'Termux:X11' NO ANDROID <<<"
echo "  >>> Deixe aberto (tela preta)          <<<"
echo "  >>> Depois volte pro Termux             <<<"
echo ""
read -p "  Pressione ENTER quando estiver pronto... "

# ============================================================
# 5. Sobe o servidor X11
# ============================================================
echo ""
echo "[5/7] Iniciando termux-x11..."
termux-x11 :0 -ac -listen tcp > "$LOG" 2>&1 &
X11_PID=$!

sleep 4

if ! kill -0 $X11_PID 2>/dev/null; then
    echo "  ERRO: termux-x11 morreu!"
    cat "$LOG"
    exit 1
fi
echo "  OK - PID $X11_PID"

if [ ! -S "$PREFIX/tmp/.X11-unix/X0" ]; then
    echo "  AVISO: socket X0 nao criado (mas TCP ativo)"
fi

# ============================================================
# 6. Exporta e testa conexao
# ============================================================
export DISPLAY=127.0.0.1:0
echo "  DISPLAY=$DISPLAY"

if python3 -c "from Xlib import display; d=display.Display(); s=d.screen(); print('  Tela:', s.width_in_pixels, 'x', s.height_in_pixels)" 2>/dev/null; then
    echo "[6/7] Conexao X11 OK"
else
    echo "  ERRO: Xlib nao conectou!"
    cat "$LOG"
    exit 1
fi

# ============================================================
# 7. Roda o modo escolhido
# ============================================================
cd "$DIR_SCRIPT"

case "$MODO" in
    boot)
        echo ""
        echo "[7/7] Rodando boot..."
        python3 oobe.py
        ;;
    oobe)
        echo ""
        echo "[7/7] Rodando OOBE..."
        python3 oobe.py
        ;;
    desktop)
        echo ""
        echo "[7/7] Rodando desktop..."
        python3 desktop.py
        ;;
    completo|*)
        echo ""
        echo "[7/7] Fluxo completo: OOBE -> Desktop"
        python3 oobe.py
        echo ""
        echo "OOBE fechou. Abrindo desktop..."
        python3 desktop.py
        ;;
esac

echo ""
echo "=========================================="
echo "  TinyOS encerrado"
echo "=========================================="

pkill -9 termux-x11 2>/dev/null
EOF

chmod +x ~/TINY-OS/runner.sh