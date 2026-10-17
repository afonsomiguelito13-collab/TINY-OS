cat > ~/getapp.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash

REPO_MAIN="https://raw.githubusercontent.com/afonsomiguelito13-collab/TINY-OS/main"
VERDE='\033[0;32m'
VERMELHO='\033[0;31m'
CIANO='\033[0;36m'
NEGRITO='\033[1m'
RESET='\033[0m'

APP_NAME="$1"
TMP_JSON="$PREFIX/tmp/tinyos_repo.json"

echo -e "${CIANO}Buscando lista de apps no servidor...${RESET}"

# Tenta buscar na raiz
curl -sSL "$REPO_MAIN/repo.json" -o "$TMP_JSON"

# Se não achar na raiz, tenta na pasta docs
if grep -q "404: Not Found" "$TMP_JSON" || [ ! -s "$TMP_JSON" ]; then
    curl -sSL "$REPO_MAIN/docs/repo.json" -o "$TMP_JSON"
fi

# Se ainda não achou, dá erro
if grep -q "404: Not Found" "$TMP_JSON" || [ ! -s "$TMP_JSON" ]; then
    echo -e "${VERMELHO}Erro: Nao foi possivel encontrar o repo.json no servidor.${RESET}"
    rm -f "$TMP_JSON"
    exit 1
fi

# Se não passou o nome do app, LISTA os apps
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
except: pass
")

if [ -z "$APP_URL" ]; then
    echo -e "${VERMELHO}Erro: App '$APP_NAME' nao encontrado na loja.${RESET}"
    rm -f "$TMP_JSON"
    exit 1
fi

echo -e "${VERDE}Encontrado! Baixando...${RESET}"
ARQUIVO_LOCAL="$HOME/TINY-OS/$APP_NAME.ty"
curl -sSL "$APP_URL" -o "$ARQUIVO_LOCAL"

if [ ! -s "$ARQUIVO_LOCAL" ] || grep -q "404: Not Found" "$ARQUIVO_LOCAL"; then
    echo -e "${VERMELHO}Erro: Falha no download do pacote .ty.${RESET}"
    echo "O link no repo.json pode estar errado."
    rm -f "$ARQUIVO_LOCAL" "$TMP_JSON"
    exit 1
fi

cd "$HOME/TINY-OS" || exit 1
./ty install "$ARQUIVO_LOCAL"
rm -f "$ARQUIVO_LOCAL" "$TMP_JSON"

echo ""
read -p "Deseja rodar '$APP_NAME' agora? (s/N) " resp
if [ "$resp" = "s" ] || [ "$resp" = "S" ]; then
    ./ty run "$APP_NAME"
fi
EOF

chmod +x ~/getapp.sh