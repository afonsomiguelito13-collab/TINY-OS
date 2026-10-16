<div align="center">

# 🖥️ TinyOS

### Um mini sistema operacional para Android

**Roda dentro do Termux:X11 — boot screen, setup inicial e desktop completo em Python puro.**

[![Autor](https://img.shields.io/badge/autor-Afonso%20Miguel-blue?style=for-the-badge)](https://github.com/afonsomiguelito13-collab)
[![License](https://img.shields.io/badge/licen%C3%A7a-GPL--3.0-green?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/status-alpha-orange?style=for-the-badge)](#-status)
[![Python](https://img.shields.io/badge/python-3.11%2B-yellow?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/plataforma-Android%208%2B-3DDC84?style=for-the-badge&logo=android&logoColor=white)](#-requisitos)

[📖 Sobre](#-sobre) • [🚀 Instalação](#-instalação-rápida) • [🎮 Uso](#-uso) • [🔮 Shizuku](#-configurar-shizuku-opcional) • [🐛 Problemas](#-problemas-comuns)

</div>

---

## 📖 Sobre

**TinyOS** é um ambiente gráfico completo que roda dentro do **Termux** no Android, usando o **Termux:X11** como servidor gráfico. Ele simula uma experiência de sistema operacional de verdade:

- 🚀 **Boot screen** animada com barra de progresso
- ⚙️ **OOBE** (configuração inicial) com 6 etapas navegáveis
- 🖥️ **Desktop** com wallpaper, ícones e barra de tarefas
- 📊 **Painel de configurações** com dados reais do device
- 🔗 **Integração com Android** via ADB + Shizuku

Tudo escrito em **Python puro** com `python-xlib`, **sem frameworks pesados** e **sem root**.

---

## ✨ Funcionalidades

### 🎬 Boot Screen
- Animação de boot estilo sistema operacional
- Barra de progresso com mensagens dinâmicas
- Logo "T" customizada

### ⚙️ OOBE (Configuração Inicial)
6 etapas navegáveis com validação:
- 🌐 **Idioma e região** — Português, English, Español
- 👤 **Conta de usuário** — nome com validação (2-16 caracteres)
- 🔒 **Senha** — opcional, com botão "Pular"
- 📡 **Rede** — scan real de Wi-Fi via ADB
- 🎨 **Aparência** — tema escuro/claro, animações
- 📋 **Resumo** — mostra dados reais do device

### 🖥️ Desktop
- 🎨 Wallpaper gradiente com estrelas
- 📊 Barra inferior: hora, Wi-Fi, bateria
- 🖱️ Painéis clicáveis (Wi-Fi, bateria, hora)
- ⚙️ Painel de Configurações do sistema completo
- 🔍 Detecção automática de Shizuku vs PC
- 📈 CPU meter ao vivo (estilo xfce4-cpugraph)

### 🔗 Integração Android (via ADB)
- Scan de redes Wi-Fi próximas
- Nível e temperatura da bateria
- Modelo, fabricante e versão do Android
- Hostname do device
- Uptime do sistema

---

## 🚀 Instalação Rápida

### ⚡ Um comando (recomendado)

```bash
curl -sSL https://raw.githubusercontent.com/afonsomiguelito13-collab/TINY-OS/main/install.sh -o install.sh && bash install.sh
