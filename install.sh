#!/data/data/com.termux/files/usr/bin/bash

# ============================================================
#  TinyOS - Instalador Oficial
#  Copyright (C) 2026 Afonso Miguel (@afonsomiguelito13-collab)
#  Licenca: GPL v3
#  Repo: https://github.com/afonsomiguelito13-collab/TINY-OS
# ============================================================

# Cores (se terminal suportar)
if [ -t 1 ]; then
    VERDE='\033[0;32m'
    VERMELHO='\033[0;31m'
    AMARELO='\033[0;33m'
    AZUL='\033[0;34m'
    CIANO='\033[0;36m'
    MAGENTA='\033[0;35m'
    NEGRITO='\033[1m'
    RESET='\033[0m'
else
    VERDE=''; VERMELHO=''; AMARELO=''; AZUL=''; CIANO=''; MAGENTA=''; NEGRITO=''; RESET=''
fi

REPO="https://raw.githubusercontent.com/afonsomiguelito13-collab/TINY-OS/main"
DEST="$HOME/TINY-OS"
VERSAO="v0.1-alpha"

# ============================================================
# Banner
# ============================================================
clear 2>/dev/null || true
echo ""
echo -e "${AZUL}${NEGRITO}"
cat << "BANNER"
  ╔══════════════════════════════════════════╗
  ║                                          ║
  ║   ████████╗██╗   ██╗                     ║
  ║   ╚══██╔══╝╚██╗ ██╔╝                     ║
  ║      ██║    ╚████╔╝                      ║
  ║      ██║     ╚██╔╝                       ║
  ║      ██║      ██║                        ║
  ║      ╚═╝      ╚═╝                        ║
  ║                                          ║
  ║   TinyOS - Mini OS para Android          ║
  ║   via Termux:X11                         ║
  ║                                          ║
  ╚══════════════════════════════════════════╝
BANNER
echo -e "${RESET}"
echo -e "  ${CIANO}Versao:${RESET}  $VERSAO"
echo -e "  ${CIANO}Repo:${RESET}    github.com/afonsomiguelito13-collab/TINY-OS"
echo -e "  ${CIANO}Licenca:${RESET} GPL v3"
echo ""
echo "=========================================="
echo ""

# ============================================================
# 1. Verifica se tá no Termux
# ============================================================
if [ ! -d "/data/data/com.termux" ]; then
    echo -e "${VERMELHO}[ERRO]${RESET} Este instalador e para Termux (Android)."
    echo "       Baixe em: https://f-droid.org/packages/com.termux/"
    exit 1
fi
echo -e "${VERDE}[OK]${RESET} Detectado: Termux"

# Verifica espaço
echo ""
echo -e "${CIANO}Verificando espaco em disco...${RESET}"
ESPAÇO=$(df -m "$HOME" | tail -1 | awk '{print $4}')
if [ "$ESPAÇO" -lt 300 ]; then
    echo -e "${AMARELO}[AVISO]${RESET} Pouco espaco livre: ${ESPAÇO}MB"
    echo "        Recomendado: 300MB+"
    read -p "  Continuar mesmo assim? (s/N) " resp_esp
    if [ "$resp_esp" != "s" ] && [ "$resp_esp" != "S" ]; then
        exit 1
    fi
else
    echo -e "${VERDE}[OK]${RESET} Espaco livre: ${ESPAÇO}MB"
fi

# ============================================================
# 2. Pergunta sobre dependências
# ============================================================
echo ""
echo "=========================================="
echo -e "${CIANO}${NEGRITO}  Dependencias necessarias${RESET}"
echo "=========================================="
echo ""
echo "  O TinyOS precisa dos seguintes pacotes:"
echo ""
echo "    ${NEGRITO}- python${RESET}        (~50 MB)  Linguagem base"
echo "    ${NEGRITO}- python-xlib${RESET}   (~5 MB)   Comunicacao com X11"
echo "    ${NEGRITO}- termux-x11${RESET}    (~30 MB)  Servidor grafico"
echo "    ${NEGRITO}- curl${RESET}          (~2 MB)   Download de arquivos"
echo ""
echo -e "  ${AMARELO}ATENCAO:${RESET} ~100 MB de espaco no total."
echo ""
read -p "  Baixar e instalar as dependencias? (s/N) " resp_deps

if [ "$resp_deps" = "s" ] || [ "$resp_deps" = "S" ]; then
    INSTALAR_DEPS=1
else
    INSTALAR_DEPS=0
    echo ""
    echo -e "${AMARELO}[AVISO]${RESET} Pulando instalacao de dependencias."
    echo "        Se algo nao funcionar, rode manualmente:"
    echo "        pkg install python python-xlib termux-x11-nightly curl"
fi

# ============================================================
# 3. Instala dependências
# ============================================================
if [ $INSTALAR_DEPS -eq 1 ]; then
    echo ""
    echo "=========================================="
    echo -e "${CIANO}${NEGRITO}  Instalando dependencias${RESET}"
    echo "=========================================="

    echo -e "${CIANO}[1/5]${RESET} Atualizando repos... (pode demorar)"
    pkg update -y > /dev/null 2>&1 || true
    echo -e "     ${VERDE}OK${RESET}"

    echo -e "${CIANO}[2/5]${RESET} Instalando curl..."
    if ! command -v curl >/dev/null 2>&1; then
        pkg install curl -y > /dev/null 2>&1
    fi
    echo -e "     ${VERDE}OK${RESET}"

    echo -e "${CIANO}[3/5]${RESET} Instalando python..."
    if ! command -v python3 >/dev/null 2>&1; then
        pkg install python -y > /dev/null 2>&1
    fi
    echo -e "     ${VERDE}OK${RESET}"

    echo -e "${CIANO}[4/5]${RESET} Instalando python-xlib..."
    if ! python3 -c "import Xlib" 2>/dev/null; then
        pkg install python-xlib -y > /dev/null 2>&1 || \
            pip install python-xlib > /dev/null 2>&1
    fi
    echo -e "     ${VERDE}OK${RESET}"

    echo -e "${CIANO}[5/5]${RESET} Instalando termux-x11-nightly..."
    if ! command -v termux-x11 >/dev/null 2>&1; then
        pkg install x11-repo -y > /dev/null 2>&1
        pkg install termux-x11-nightly -y > /dev/null 2>&1
    fi
    echo -e "     ${VERDE}OK${RESET}"

    echo ""
    echo -e "${VERDE}[OK]${RESET} Todas as dependencias instaladas!"
fi

# ============================================================
# 4. Pergunta sobre Shizuku
# ============================================================
echo ""
echo "=========================================="
echo -e "${CIANO}${NEGRITO}  Shizuku (opcional, recomendado)${RESET}"
echo "=========================================="
echo ""
echo "  O Shizuku permite:"
echo "    ${VERDE}+${RESET} Scan real de Wi-Fi"
echo "    ${VERDE}+${RESET} Dados do device (modelo, bateria)"
echo "    ${VERDE}+${RESET} Painel de configuracoes completo"
echo ""
echo "  ${AMARELO}Requer o app Shizuku instalado no Android:${RESET}"
echo "    https://shizuku.rikka.app/"
echo ""
read -p "  Instalar o ADB (android-tools) pro Shizuku? (s/N) " resp_sz

if [ "$resp_sz" = "s" ] || [ "$resp_sz" = "S" ]; then
    echo ""
    echo -e "${CIANO}Instalando android-tools...${RESET}"
    pkg install android-tools -y > /dev/null 2>&1
    echo -e "${VERDE}[OK]${RESET} ADB instalado"
    echo ""
    echo -e "${CIANO}Como configurar o Shizuku:${RESET}"
    echo "  1. Instale o app Shizuku no Android"
    echo "  2. Ative Depuracao sem fio (Configuracoes -> Dev)"
    echo "  3. No Termux:"
    echo "       adb pair IP:PORTA_PAREAMENTO"
    echo "       adb connect IP:PORTA_CONEXAO"
    echo "       adb devices"
    echo ""
    echo "  ${AMARELO}Guia completo:${RESET}"
    echo "    github.com/afonsomiguelito13-collab/TINY-OS#shizuku"
else
    echo ""
    echo -e "${AMARELO}[AVISO]${RESET} Pulando Shizuku."
    echo "        Voce pode instalar depois com:"
    echo "        pkg install android-tools"
fi

# ============================================================
# 5. Baixa o TinyOS
# ============================================================
echo ""
echo "=========================================="
echo -e "${CIANO}${NEGRITO}  Baixando TinyOS${RESET}"
echo "=========================================="
echo ""

mkdir -p "$DEST"
cd "$DEST" || exit 1

# Baixa runner.sh
echo -e "${CIANO}[1/3]${RESET} Baixando runner.sh..."
curl -sSL "$REPO/runner.sh" -o runner.sh

if [ ! -s "$DEST/runner.sh" ]; then
    echo -e "${VERMELHO}[ERRO]${RESET} Falha ao baixar runner.sh"
    echo "       Verifique sua conexao e tente novamente."
    exit 1
fi
chmod +x runner.sh
echo -e "     ${VERDE}OK${RESET}"

# Baixa README
echo -e "${CIANO}[2/3]${RESET} Baixando README.md..."
curl -sSL "$REPO/README.md" -o README.md 2>/dev/null || true
echo -e "     ${VERDE}OK${RESET}"

# Baixa LICENSE
echo -e "${CIANO}[3/3]${RESET} Baixando LICENSE..."
curl -sSL "$REPO/LICENSE" -o LICENSE 2>/dev/null || true
echo -e "     ${VERDE}OK${RESET}"

echo ""
echo -e "${VERDE}[OK]${RESET} TinyOS instalado em:"
echo "     $DEST"

# ============================================================
# 6. Instruções finais
# ============================================================
echo ""
echo "=========================================="
echo -e "${VERDE}${NEGRITO}  INSTALACAO CONCLUIDA!${RESET}"
echo "=========================================="
echo ""
echo -e "${CIANO}Localizacao:${RESET}  $DEST"
echo ""
echo -e "${CIANO}Arquivos:${RESET}"
ls -1 "$DEST" 2>/dev/null | sed 's/^/  - /'
echo ""
echo "=========================================="
echo -e "${NEGRITO}  COMO RODAR${RESET}"
echo "=========================================="
echo ""
echo -e "  ${AZUL}cd ~/TINY-OS${RESET}"
echo -e "  ${AZUL}bash runner.sh${RESET}"
echo ""
echo "=========================================="
echo -e "${NEGRITO}  MODOS DE EXECUCAO${RESET}"
echo "=========================================="
echo ""
echo "  ${AZUL}bash runner.sh${RESET}           # fluxo completo"
echo "  ${AZUL}bash runner.sh oobe${RESET}      # so config inicial"
echo "  ${AZUL}bash runner.sh desktop${RESET}   # so o desktop"
echo ""
echo "=========================================="
echo -e "${NEGRITO}  ANTES DE RODAR${RESET}"
echo "=========================================="
echo ""
echo "  1. Instale o app Termux:X11:"
echo "     ${CIANO}https://github.com/termux/termux-x11/releases${RESET}"
echo ""
echo "  2. Abra ele ANTES de rodar o runner.sh"
echo ""
echo "  3. Configurar resolucao 480p (opcional):"
echo "     App Termux:X11 -> 3 dedos -> Preferences -> Output"
echo "     Resolution: custom 854x480"
echo ""
echo "=========================================="
echo ""

read -p "  Rodar o TinyOS agora? (s/N) " resp_run

if [ "$resp_run" = "s" ] || [ "$resp_run" = "S" ]; then
    cd "$DEST"
    bash runner.sh
else
    echo ""
    echo -e "${VERDE}OK!${RESET} Pra rodar depois:"
    echo "  ${AZUL}cd ~/TINY-OS && bash runner.sh${RESET}"
    echo ""
fi