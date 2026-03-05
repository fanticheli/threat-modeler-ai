# Guia de Provisionamento Local

Passo a passo para subir todos os servicos do Threat Modeler AI localmente.

---

## Pre-requisitos

| Ferramenta | Versao minima | Verificar |
|------------|---------------|-----------|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | v2.0+ | `docker compose version` |
| Git | 2.0+ | `git --version` |

Voce tambem precisa de uma **chave da API Anthropic** ([console.anthropic.com](https://console.anthropic.com/)).

> **Nota:** Node.js e Python **nao sao necessarios** se usar Docker Compose (Opcao 1). So sao necessarios para desenvolvimento local sem Docker (Opcao 2).

---

## Estrutura de repositorios

Os 3 repositorios devem ficar na **mesma pasta pai**:

```
meu-workspace/
  ├── threat-modeler-ai/          # Dataset, YOLO Service, Docker Compose
  ├── threat-modeler-ai-backend/  # Backend NestJS
  └── threat-modeler-ai-frontend/ # Frontend React
```

### 1. Clonar os repos

```bash
mkdir threat-modeler && cd threat-modeler

git clone https://github.com/fanticheli/threat-modeler-ai.git
git clone https://github.com/fanticheli/threat-modeler-ai-backend.git
git clone https://github.com/fanticheli/threat-modeler-ai-frontend.git
```

---

## Opcao 1: Docker Compose (recomendado)

Sobe **todos os 5 servicos** com um unico comando: YOLO Service + MongoDB + Redis + Backend + Frontend.

### 1.1 Configurar a API Key

Crie um arquivo `.env` no diretorio do `threat-modeler-ai` (onde esta o `docker-compose.yml`):

```bash
cd threat-modeler-ai
echo "ANTHROPIC_API_KEY=sk-ant-api03-SUA_CHAVE_AQUI" > .env
```

> O `.env` ja esta no `.gitignore` — nao sera commitado.

### 1.2 Subir todos os servicos

```bash
docker compose up -d --build
```

Isso vai buildar e subir:

| # | Servico | Tecnologia | Porta |
|---|---------|------------|-------|
| 1 | YOLO Service | Python 3.11 + FastAPI + ultralytics | 8000 |
| 2 | MongoDB | Mongo 7 (volume persistente) | 27017 |
| 3 | Redis | Redis 7 Alpine | 6379 |
| 4 | Backend | Node 20 + NestJS | 3001 |
| 5 | Frontend | Nginx (build React+Vite) | 8080 |

### 1.3 Verificar se subiu

```bash
# Status dos containers
docker compose ps

# Logs em tempo real (todos)
docker compose logs -f

# Logs de um servico especifico
docker compose logs -f backend
docker compose logs -f yolo-service
```

### 1.4 Health checks

```bash
# YOLO Service
curl http://localhost:8000/health
# Esperado: {"status":"healthy","model_loaded":true,"model_path":"...","total_classes":10}

# Backend
curl http://localhost:3001/api/analysis
# Esperado: [] (lista vazia)

# Frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080
# Esperado: 200
```

### 1.5 Acessar a aplicacao

Abra no navegador: **http://localhost:8080**

### 1.6 Comandos uteis

```bash
# Acompanhar logs do pipeline em tempo real
docker compose logs -f backend

# Limpar todas as analises do banco
docker compose exec mongodb mongosh threat-modeler --eval "db.analyses.deleteMany({})"

# Reiniciar apenas o backend (apos mudancas de codigo)
docker compose build --no-cache backend && docker compose up -d backend

# Parar tudo (dados do MongoDB persistem no volume)
docker compose down

# Parar tudo e apagar dados do MongoDB
docker compose down -v
```

---

## Opcao 2: Subir manualmente (sem Docker)

Util para desenvolvimento ou debugging. Cada servico roda em um terminal separado.

### Pre-requisitos adicionais

| Ferramenta | Versao minima | Verificar |
|------------|---------------|-----------|
| Python | 3.11+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| MongoDB | 7+ | `mongosh --eval "db.version()"` |
| Redis | 7+ | `redis-cli ping` |

### Terminal 1: YOLO Service (porta 8000)

```bash
cd threat-modeler-ai/yolo-service
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Verifique: `curl http://localhost:8000/health`

### Terminal 2: Backend NestJS (porta 3001)

```bash
cd threat-modeler-ai-backend
cp .env.example .env
```

Edite `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-api03-SUA_CHAVE_AQUI
MONGODB_URI=mongodb://localhost:27017/threat-modeler
REDIS_HOST=localhost
REDIS_PORT=6379
YOLO_SERVICE_URL=http://localhost:8000
YOLO_TIMEOUT_MS=30000
```

```bash
npm install
npm run start:dev
```

Verifique: `curl http://localhost:3001/api/analysis`

### Terminal 3: Frontend React (porta 8080)

```bash
cd threat-modeler-ai-frontend
npm install
npm run dev
```

Acesse: **http://localhost:8080**

---

## Teste completo (ponta a ponta)

1. Acesse **http://localhost:8080**
2. Faca upload de uma imagem de diagrama de arquitetura (PNG/JPG)
3. Acompanhe o progresso em tempo real (SSE)
4. Verifique nos logs do backend as fases do pipeline:
   - `[Pipeline] ▶ Fase 1: YOLO Service...`
   - `[Pipeline] ▶ Fase 2: Claude Vision...`
   - `[Pipeline] ▶ Fase 3: Merge...`
   - `[Pipeline] ▶ Fase 4: STRIDE...`
   - `[Pipeline] ✓ Analise completa!`
5. Veja os componentes detectados e a analise STRIDE
6. Exporte o relatorio em PDF, JSON ou Markdown

---

## Troubleshooting

### YOLO Service nao carrega o modelo

```bash
# Verificar se o modelo existe
ls -lh threat-modeler-ai/yolo-service/model/best.pt
# Esperado: ~22 MB (YOLOv8s small, v5)
```

Se nao existir, o modelo `best.pt` precisa estar em `yolo-service/model/`.

### Backend nao conecta no MongoDB

- **Docker:** verifique se o container mongo esta rodando: `docker compose ps`
- **Local:** verifique se o MongoDB esta rodando: `mongosh`
- **Atlas:** verifique se o IP esta liberado no Network Access

### Backend nao conecta no Redis

- **Docker:** verifique se o container redis esta rodando: `docker compose ps`
- **Local:** verifique se o Redis esta rodando: `redis-cli ping`
- **Erro TLS/ETIMEDOUT:** verifique se `REDIS_TLS=false` no Docker Compose (Redis local nao usa TLS)

### Frontend nao conecta no Backend

- Verifique se o backend esta rodando na porta 3001
- **Docker:** o frontend ja aponta para `http://localhost:3001` (build arg)
- **Local:** verifique `VITE_API_URL=http://localhost:3001` no `.env` do frontend

### Analise trava em "Detectando componentes"

- Verifique se a `ANTHROPIC_API_KEY` esta correta: `docker compose logs -f backend`
- Verifique creditos da API: [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing)
- Erro 529 (Overloaded): aguarde alguns minutos e tente novamente

### Sistema funciona sem o YOLO Service?

Sim. O backend detecta que o YOLO esta indisponivel e usa apenas o Claude Vision (fallback gracioso). A unica diferenca e que todos os componentes serao marcados como `claude` em vez de `hybrid` ou `yolo`.
