# 📱 Guia de Desenvolvimento de Apps para o TinyOS

Bem-vindo ao guia oficial para criar aplicativos para o **TinyOS**! 

O TinyOS usa o seu próprio gerenciador de pacotes, o **`ty`**. Todos os aplicativos são distribuídos em um formato único de arquivo: o **`.ty`** (que é um arquivo ZIP renomeado).

---

## 📦 Requisitos do Pacote `.ty`

Para que o seu app funcione, o arquivo `.ty` **precisa** seguir esta estrutura básica:

```text
meu_app.ty (arquivo zip)
 ├── manifest.json    (Obrigatório - Metadados)
 ├── icon.png         (Obrigatório - Ícone 64x64 pro Menu Iniciar)
 └── [app.py | app.sh | index.html]  (Obrigatório - O app em si)
