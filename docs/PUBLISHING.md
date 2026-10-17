# 🌍 Publicando seu App no TinyOS

Quer que o seu app apareça na loja oficial do TinyOS (`getapp.sh`)? Siga os passos abaixo!

### Passo 1: Crie o pacote `.ty`
Siga o [Guia de Desenvolvimento](APPS.md) para criar o seu app e o arquivo `.ty` (não esqueça do `manifest.json` e do `icon.png`).

### Passo 2: Suba no seu GitHub
1. Crie um repositório público no GitHub para o seu app.
2. Faça upload do arquivo `.ty` (ex: `meu_app.ty`) para a branch principal (`main`).
3. Pegue o link **Raw** do arquivo. Ele vai ser algo como: 
   `https://raw.githubusercontent.com/SEU_USER/SEU_REPO/main/meu_app.ty`

### Passo 3: Abra um Pull Request (PR)
1. Faça um Fork do repositório oficial do [TINY-OS](https://github.com/afonsomiguelito13-collab/TINY-OS).
2. Abra o arquivo `repo.json` e adicione o seu app na lista:
```json
{
    "name": "meu_app",
    "version": "1.0.0",
    "author": "Seu Nome",
    "description": "Descricao curta do app.",
    "url": "https://raw.githubusercontent.com/SEU_USER/SEU_REPO/main/meu_app.ty"
}
