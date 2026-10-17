# 📦 TinyOS Application Packaging Guide

Este documento especifica o formato oficial de empacotamento de software para o **TinyOS** (`.ty`). 

O TinyOS utiliza o gerenciador de pacotes **`ty`** (TinyOS Package Manager), que foi projetado para ser simples, portátil e seguro. O formato `.ty` é essencialmente um arquivo `.zip` com uma estrutura de diretórios pré-definida e um manifesto JSON.

---

## 📑 Índice

1. [Estrutura do Pacote](#1-estrutura-do-pacote)
2. [O Arquivo `manifest.json`](#2-o-arquivo-manifestjson)
3. [O Arquivo de Ícone `icon.png`](#3-o-arquivo-de-ícone-iconpng)
4. [Ponto de Entrada (Entrypoint)](#4-ponto-de-entrada-entrypoint)
5. [Suporte a Múltiplas Linguagens](#5-suporte-a-múltiplas-linguagens)
6. [Empacotamento e Distribuição](#6-empacotamento-e-distribuição)
7. [Instalação via `ty`](#7-instalação-via-ty)
8. [Boas Práticas e Padrões](#8-boas-práticas-e-padrões)

---

## 1. Estrutura do Pacote

Todo pacote `.ty` **deve** conter, no mínimo, os seguintes arquivos na raiz do arquivo `.zip`:

```text
nome_do_app.ty
 ├── manifest.json    (Obrigatório) - Metadados do aplicativo
 ├── icon.png         (Obrigatório) - Ícone do Menu Iniciar (64x64 ou 128x128)
 └── [entrypoint]     (Obrigatório) - O código do app (app.py, index.html, etc)
