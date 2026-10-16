#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  TinyOS - Instalador
#  Copyright (C) 2026 Afonso Miguel
#  Licenca: GPL v3
# ============================================================

REPO="https://raw.githubusercontent.com/afonsomiguelito13-collab/TINY-OS/main"
DEST="$HOME/TINY-OS"

echo "=========================================="
echo "  TinyOS - Instalador"
echo "=========================================="
echo ""

# Cria pasta
mkdir -p "$DEST"
cd "$DEST"

echo "[1/3] Baixando runner.sh..."
curl -sSL "$REPO/runner.sh" -o runner.sh

if [ ! -s "$DEST/runner.sh" ]; then
    echo "  ERRO: nao consegui baixar runner.sh"
    exit 1
fi

echo "[2/3] Dando permissao de execucao..."
chmod +x runner.sh

echo "[3/3] Pronto!"
echo ""
echo "=========================================="
echo "  TinyOS instalado em: $DEST"
echo "=========================================="
echo ""
echo "Pra rodar depois:"
echo "  cd ~/TINY-OS"
echo "  bash runner.sh"
echo ""
echo "Rodando agora? (s/N)"
read -r resp
if [ "$resp" = "s" ] || [ "$resp" = "S" ]; then
    bash runner.sh
fi