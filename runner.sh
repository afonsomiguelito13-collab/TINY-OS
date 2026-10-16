#!/data/data/com.termux/files/usr/bin/bash

# ============================================================
#  TinyOS - Launcher
#  Copyright (C) 2026 Afonso Miguel (@afonsomiguelito13-collab)
#  Licenca: GPL v3
# ============================================================

# Cores
if [ -t 1 ]; then
    VERDE='\033[0;32m'
    VERMELHO='\033[0;31m'
    AMARELO='\033[0;33m'
    AZUL='\033[0;34m'
    CIANO='\033[0;36m'
    NEGRITO='\033[1m'
    RESET='\033[0m'
else
    VERDE=''; VERMELHO=''; AMARELO=''; AZUL=''; CIANO=''; NEGRITO=''; RESET=''
fi

REPO="https://raw.githubusercontent.com/afonsomiguelito13-collab/TINY-OS/main"
DIR_SCRIPT="$(cd "$(dirname "$0")" && pwd)"
LOG="$PREFIX/tmp/x11.log"
MODO="${1:-completo}"

echo ""
echo -e "${AZUL}${NEGRITO}=========================================="
echo "  TinyOS Launcher v0.1"
echo -e "==========================================${RESET}"
echo -e "  Modo: ${CIANO}$MODO${RESET}"
echo ""

# ============================================================
# 1. Verifica arquivos (baixa se faltar)
# ============================================================
echo -e "${CIANO}[1/6]${RESET} Verificando arquivos..."

faltando=0

if [ ! -f "$DIR_SCRIPT/desktop.py" ]; then
    echo -e "     ${AMARELO}desktop.py NAO encontrado${RESET}"
    faltando=1
fi

if [ ! -f "$DIR_SCRIPT/oobe.py" ]; then
    echo -e "     ${AMARELO}oobe.py NAO encontrado${RESET}"
    faltando=1
fi

if [ $faltando -eq 1 ]; then
    echo ""
    echo -e "${CIANO}[2/6]${RESET} Baixando arquivos do GitHub..."

    if ! command -v curl >/dev/null 2>&1; then
        echo "     Instalando curl..."
        pkg install curl -y > /dev/null 2>&1
    fi

    echo "     Baixando desktop.py..."
    curl -sSL "$REPO/desktop.py" -o "$DIR_SCRIPT/desktop.py"
    if [ ! -s "$DIR_SCRIPT/desktop.py" ]; then
        echo -e "     ${VERMELHO}ERRO: falha ao baixar desktop.py${RESET}"
        exit 1
    fi
    echo -e "     ${VERDE}OK${RESET}"

    echo "     Baixando oobe.py..."
    curl -sSL "$REPO/oobe.py" -o "$DIR_SCRIPT/oobe.py"
    if [ ! -s "$DIR_SCRIPT/oobe.py" ]; then
        echo -e "     ${VERMELHO}ERRO: falha ao baixar oobe.py${RESET}"
        exit 1
    fi
    echo -e "     ${VERDE}OK${RESET}"

    echo -e "     ${VERDE}Todos os arquivos baixados!${RESET}"
else
    echo -e "     ${VERDE}Todos os arquivos ja existem${RESET}"
    echo -e "${CIANO}[2/6]${RESET} Pulando download"
fi

# ============================================================
# 2. Verifica dependências do sistema
# ============================================================
echo ""
echo -e "${CIANO}[3/6]${RESET} Verificando dependencias..."

# python
if ! command -v python3 >/dev/null 2>&1; then
    echo "     Instalando python..."
    pkg install python -y > /dev/null 2>&1
fi

# python-xlib
if ! python3 -c "import Xlib" 2>/dev/null; then
    echo "     Instalando python-xlib..."
    pkg install python-xlib -y > /dev/null 2>&1 || \
        pip install python-xlib > /dev/null 2>&1
fi

# termux-x11
if ! command -v termux-x11 >/dev/null 2>&1; then
    echo "     Instalando termux-x11-nightly..."
    pkg install x11-repo -y > /dev/null 2>&1
    pkg install termux-x11-nightly -y > /dev/null 2>&1
fi

echo -e "     ${VERDE}OK${RESET} Dependencias prontas"

# ============================================================
# 3. Limpa X11 antigo
# ============================================================
echo ""
echo -e "${CIANO}[4/6]${RESET} Limpando X11 antigo..."
pkill -9 termux-x11 2>/dev/null
sleep 1
rm -f $PREFIX/tmp/.X11-unix/* 2>/dev/null
rm -f "$LOG" 2>/dev/null
echo -e "     ${VERDE}OK${RESET}"

# ============================================================
# 4. Pede pro user abrir o app
# ============================================================
echo ""
echo "=========================================="
echo -e "${AMARELO}${NEGRITO}  >>> ABRA O APP 'Termux:X11' AGORA <<<${RESET}"
echo "=========================================="
echo ""
echo "  1. SAI do Termux (botao home)"
echo "  2. ABRE o app Termux:X11 (icone roxo)"
echo "  3. Deixa na tela preta"
echo "  4. VOLTA pro Termux"
echo ""
read -p "  Pressione ENTER quando estiver pronto... "

# ============================================================
# 5. Sobe o X11
# ============================================================
echo ""
echo -e "${CIANO}[5/6]${RESET} Iniciando termux-x11..."
termux-x11 :0 -ac -listen tcp > "$LOG" 2>&1 &
X11_PID=$!

sleep 4

if ! kill -0 $X11_PID 2>/dev/null; then
    echo -e "     ${VERMELHO}ERRO: termux-x11 morreu!${RESET}"
    echo "     Log:"
    cat "$LOG"
    exit 1
fi
echo -e "     ${VERDE}OK${RESET} PID $X11_PID"

if [ ! -S "$PREFIX/tmp/.X11-unix/X0" ]; then
    echo -e "     ${AMARELO}AVISO: socket X0 nao criado (mas TCP ativo)${RESET}"
fi

# ============================================================
# 6. Exporta e testa
# ============================================================
export DISPLAY=127.0.0.1:0
echo -e "     DISPLAY=$DISPLAY"

if python3 -c "from Xlib import display; d=display.Display(); s=d.screen(); print('     Tela:', s.width_in_pixels, 'x', s.height_in_pixels)" 2>/dev/null; then
    echo -e "${CIANO}[6/6]${RESET} ${VERDE}Conexao X11 OK${RESET}"
else
    echo -e "     ${VERMELHO}ERRO: Xlib nao conectou!${RESET}"
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
        echo "=========================================="
        echo -e "${NEGRITO}  Rodando boot...${RESET}"
        echo "=========================================="
        python3 oobe.py
        ;;
    oobe)
        echo ""
        echo "=========================================="
        echo -e "${NEGRITO}  Rodando OOBE...${RESET}"
        echo "=========================================="
        python3 oobe.py
        ;;
    desktop)
        echo ""
        echo "=========================================="
        echo -e "${NEGRITO}  Rodando desktop...${RESET}"
        echo "=========================================="
        python3 desktop.py
        ;;
    completo|*)
        echo ""
        echo "=========================================="
        echo -e "${NEGRITO}  Fluxo completo: OOBE -> Desktop${RESET}"
        echo "=========================================="
        python3 oobe.py
        echo ""
        echo -e "${CIANO}OOBE encerrou. Abrindo desktop...${RESET}"
        python3 desktop.py
        ;;
esac

# ============================================================
# Fim
# ============================================================
echo ""
echo "=========================================="
echo -e "${VERDE}  TinyOS encerrado${RESET}"
echo "=========================================="
echo ""

pkill -9 termux-x11 2>/dev/null