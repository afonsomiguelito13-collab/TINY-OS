#!/data/data/com.termux/files/usr/bin/bash

# ============================================================
#  TinyOS - App Store CLI (getapp.sh)
#  Localizado em: docs/getapp.sh
# ============================================================

# URL base do GitHub (apontando pra pasta docs)
REPO_JSON_URL="https://raw.githubusercontent.com/afonsomiguelito13-collab/TINY-OS/main/docs/repo.json"
TINYOS_DIR="$HOME/TINY-OS"

VERDE='\033[0;32m'
VERMELHO='\033[0;31m'
CIANO='\033[0;36m'
NEGRITO='\033[1m'
RESET='\033[0m'

APP_NAME="$1"
TMP_JSON="$PREFIX/tmp/tinyos_repo.json"

# Verifica se o TinyOS tá instalado
if [ ! -d "$TINYOS_DIR" ]; then
    echo -e "${VERMELHO}Erro: TinyOS nao encontrado em $TINYOS_DIR.${RESET}"
    echo "Instale o TinyOS primeiro rodando o install.sh"
    exit 1
fi

echo -e "${CIANO}Buscando lista de apps no servidor...${RESET}"
curl -sSL "$REPO_JSON_URL" -o "$TMP_JSON"

if [ ! -s "$TMP_JSON" ] || grep -q "404: Not Found" "$TMP_JSON"; then
    echo -e "${VERMELHO}Erro: Nao foi possivel conectar a App Store.${RESET}"
    rm -f "$TMP_JSON"
    exit 1
fi

# Se nao passou o nome do app, LISTA todos
if [ -z "$APP_NAME" ]; then
    echo -e "${NEGRITO}"
    echo "=========================================="
    echo "  TinyOS App Store"
    echo "=========================================="
    echo -e "${RESET}"
    
    python3 -c "
import json
with open('$TMP_JSON') as f:
    data = json.load(f)
    for app in data['apps']:
        print(f\"  {app['name']} (v{app['version']})\")
        print(f\"    Autor: {app['author']}\")
        print(f\"    {app['description']}\")
        print()
"
    echo -e "Para instalar: ${CIANO}bash getapp.sh <nome_do_app>${RESET}"
    rm -f "$TMP_JSON"
    exit 0
fi

# Se passou o nome, BUSCA e INSTALA
echo -e "${CIANO}Procurando '$APP_NAME'...${RESET}"

APP_URL=$(python3 -c "
import json
try:
    with open('$TMP_JSON') as f:
        data = json.load(f)
        for app in data['apps']:
            if app['name'] == '$APP_NAME':
                print(app['url'])
                break
except:
    pass
")

if [ -z "$APP_URL" ]; then
    echo -e "${VERMELHO}Erro: App '$APP_NAME' nao encontrado na loja.${RESET}"
    rm -f "$TMP_JSON"
    exit 1
fi

echo -e "${VERDE}Encontrado! Baixando...${RESET}"
ARQUIVO_LOCAL="$TINYOS_DIR/$APP_NAME.ty"
curl -sSL "$APP_URL" -o "$ARQUIVO_LOCAL"

if [ ! -s "$ARQUIVO_LOCAL" ]; then
    echo -e "${VERMELHO}Erro: Falha no download do pacote.${RESET}"
    rm -f "$ARQUIVO_LOCAL" "$TMP_JSON"
    exit 1
fi

# Entra na pasta do TinyOS pra rodar o ty
cd "$TINYOS_DIR" || exit 1

# Instala e roda
./ty install "$ARQUIVO_LOCAL"
rm -f "$ARQUIVO_LOCAL" "$TMP_JSON"

echo ""
read -p "Deseja rodar '$APP_NAME' agora? (s/N) " resp
if [ "$resp" = "s" ] || [ "$resp" = "S" ]; then
    ./ty run "$APP_NAME"
fi
