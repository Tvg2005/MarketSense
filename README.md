# NFE Analyser

O **NFE Analyser** é uma aplicação web que extrai e estrutura dados de Notas Fiscais de Consumidor Eletrônica (NFC-e) do portal da SEFAZ-DF. O usuário insere a chave de acesso (44 dígitos) ou envia uma foto do QR Code da nota, e o sistema faz o scraping completo dos dados, salvando em PostgreSQL para análise futura.

## 🚀 Funcionalidades

- **Bypass de Cloudflare**: SeleniumBase em modo undetected para contornar o Turnstile
- **Leitura de QR Code**: ZXing no browser + OpenCV/pyzbar no backend (10 estratégias de pré-processamento)
- **Frontend React**: Interface moderna com status em tempo real via WebSocket
- **Persistência PostgreSQL**: Dados normalizados (emitentes, notas, produtos, histórico de preços)
- **Consolidação de Produtos**: Agrupa itens duplicados somando quantidades e valores

## 🛠️ Stack

- **Backend**: Python, Flask, Flask-SocketIO, SeleniumBase, BeautifulSoup, OpenCV, SQLAlchemy
- **Frontend**: React, Vite, Socket.IO Client, ZXing
- **Banco**: PostgreSQL 16 (Docker)

## 📦 Instalação

### 1. Clone e crie o ambiente virtual

```bash
git clone <URL_DO_REPOSITORIO>
cd NFE_Analyser
python -m venv venv
```

Ative o venv:
```bash
# Windows
.\venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 2. Instale as dependências Python

```bash
pip install -r requirements.txt
```

### 3. Instale as dependências do frontend

```bash
cd frontend
npm install
cd ..
```

### 4. Suba o banco de dados

```bash
docker compose up -d
```

### 5. Crie as tabelas

```bash
python backend/models.py
```

### 6. Configure o `.env`

Copie o exemplo e ajuste se necessário:
```bash
cp .env.example .env
```

## ▶️ Rodando

Você precisa de **dois terminais**:

**Terminal 1 — Backend (Flask):**
```bash
python backend/app.py
```
Roda na porta `5000`.

**Terminal 2 — Frontend (React/Vite):**
```bash
cd frontend
npm run dev
```
Roda na porta `3000`.

Acesse: **http://localhost:3000**

## 🗂️ Estrutura do Projeto

```
NFE_Analyser/
├── backend/               # Código Python do servidor
│   ├── app.py             # Entry point Flask + SocketIO
│   ├── models.py          # Modelos SQLAlchemy (PostgreSQL)
│   ├── db_service.py      # Serviço de persistência
│   ├── auth_routes.py     # Blueprint de autenticação (register/login/refresh)
│   ├── me_routes.py       # Blueprint protegido (notas, carrinho recorrente)
│   └── auth_middleware.py # Decorator token_required
├── frontend/              # React + Vite
│   ├── src/
│   │   ├── App.jsx
│   │   ├── contexts/AuthContext.jsx
│   │   ├── components/
│   │   │   ├── QRScanner.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   ├── StatusPanel.jsx
│   │   │   └── ResultPanel.jsx
│   │   └── pages/
│   │       ├── LoginPage.jsx
│   │       ├── SignupPage.jsx
│   │       ├── DashboardPage.jsx
│   │       ├── ExtractorPage.jsx
│   │       └── RecurringCartPage.jsx
│   └── package.json
├── docker-compose.yml     # PostgreSQL 16
├── requirements.txt       # Dependências Python
├── .env.example           # Template de configuração
└── trash/                 # Arquivos legados (pode deletar)
```

## ⚠️ Observações

- Você precisa de Docker instalado para o PostgreSQL
- Se já tem PostgreSQL local na porta 5432, o Docker usa a porta **5433** (configurado no docker-compose.yml)
- No Windows, o `pyzbar` pode precisar de `pip install pyzbar[scripts]` para baixar a DLL do zbar
- Devido às atualizações de segurança da SEFAZ, pode ser necessário ajustar seletores ou tempos de espera no futuro
