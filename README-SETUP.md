# Como Subir o Projeto Local

Guia passo a passo para rodar o Threat Modeler AI no seu ambiente local.

---

## Pre-requisitos

- **Python 3.8+** (para o YOLO Service)
- **Node.js 18+** (para Backend e Frontend)
- **npm**
- **Chave API da Anthropic** ([console.anthropic.com](https://console.anthropic.com/))
- **MongoDB** rodando (local ou [Atlas](https://www.mongodb.com/atlas))
- **Redis** rodando (local ou [Upstash](https://upstash.com/))

---

## Opcao 1 - Docker Compose (mais facil)

Sobe YOLO + MongoDB + Redis + Backend de uma vez. So o frontend fica separado.

```bash
# 1. Clone os 3 repos na mesma pasta
git clone https://github.com/fanticheli/threat-modeler-ai.git
git clone https://github.com/fanticheli/threat-modeler-ai-backend.git
git clone https://github.com/fanticheli/threat-modeler-ai-frontend.git

# 2. Configure o backend
cp threat-modeler-ai-backend/.env.example threat-modeler-ai-backend/.env
# Edite threat-modeler-ai-backend/.env e adicione sua ANTHROPIC_API_KEY

# 3. Suba YOLO + MongoDB + Redis + Backend
cd threat-modeler-ai
export ANTHROPIC_API_KEY=sk-ant-api03-SUA_CHAVE_AQUI
docker-compose up -d

# 4. Suba o frontend
cd ../threat-modeler-ai-frontend
npm install
npm run dev
```

Acesse: http://localhost:8080

---

## Opcao 2 - Subir cada servico manualmente (sem Docker)

Util para desenvolvimento ou se nao tiver Docker. Cada servico roda em um terminal separado.

### Passo 1 - Clone os repos

```bash
git clone https://github.com/fanticheli/threat-modeler-ai.git
git clone https://github.com/fanticheli/threat-modeler-ai-backend.git
git clone https://github.com/fanticheli/threat-modeler-ai-frontend.git
```

### Passo 2 - YOLO Service (porta 8000)

```bash
cd threat-modeler-ai/yolo-service
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Teste: http://localhost:8000/health deve retornar:
```json
{"status":"healthy","model_loaded":true,"model_path":"...","total_classes":30}
```

### Passo 3 - Backend NestJS (porta 3001)

Abra outro terminal:

```bash
cd threat-modeler-ai-backend
cp .env.example .env
```

Edite o `.env` com suas credenciais:

```env
# Obrigatorio
ANTHROPIC_API_KEY=sk-ant-api03-SUA_CHAVE_AQUI

# MongoDB (local ou Atlas)
MONGODB_URI=mongodb://localhost:27017/threat-modeler
# ou Atlas: mongodb+srv://user:pass@cluster.mongodb.net/threat-modeler

# Redis (local ou Upstash)
REDIS_HOST=localhost
REDIS_PORT=6379
# Se Upstash, adicione tambem:
# REDIS_PASSWORD=sua_senha
# REDIS_TLS=true

# YOLO Service
YOLO_SERVICE_URL=http://localhost:8000
YOLO_TIMEOUT_MS=30000
```

```bash
npm install
npm run start:dev
```

Teste: http://localhost:3001/api/analysis deve retornar `[]`.

### Passo 4 - Frontend (porta 8080)

Abra outro terminal:

```bash
cd threat-modeler-ai-frontend
npm install
npm run dev
```

Acesse: http://localhost:8080

---

## Verificando se tudo esta funcionando

| Servico | URL | O que esperar |
|---------|-----|---------------|
| YOLO Service | http://localhost:8000/health | `{"status":"healthy","model_loaded":true}` |
| Backend API | http://localhost:3001/api/analysis | `[]` (lista vazia ou com analises) |
| Frontend | http://localhost:8080 | Interface web com upload |

### Teste completo

1. Acesse http://localhost:8080
2. Faca upload de uma imagem de diagrama de arquitetura (PNG/JPG)
3. Aguarde o processamento (progresso em tempo real)
4. Veja os componentes detectados e a analise STRIDE
5. Exporte o relatorio em PDF, JSON ou Markdown

---

## Se o YOLO Service nao estiver rodando

O sistema funciona normalmente. O backend detecta que o YOLO esta indisponivel e usa apenas o Claude Vision (fallback gracioso). A unica diferenca e que todos os componentes serao marcados como `claude` em vez de `hybrid` ou `yolo`.

---

## Troubleshooting

### Backend nao conecta no MongoDB
- **Local:** Verifique se o MongoDB esta rodando (`mongosh` ou `mongod`)
- **Atlas:** Verifique se o IP esta liberado no Network Access do Atlas

### Backend nao conecta no Redis
- **Local:** Verifique se o Redis esta rodando (`redis-cli ping`)
- **Upstash:** Verifique REDIS_PASSWORD e REDIS_TLS=true no .env

### YOLO Service nao carrega o modelo
- Verifique se o arquivo `yolo-service/model/best.pt` existe (6.26 MB)
- Verifique se as dependencias foram instaladas: `pip install -r requirements.txt`

### Frontend nao conecta no backend
- Verifique se o backend esta rodando na porta 3001
- Verifique o arquivo `.env` do frontend: `VITE_API_URL=http://localhost:3001`

### Analise trava em "Detectando componentes"
- Verifique se a `ANTHROPIC_API_KEY` esta correta no .env do backend
- Verifique os logs do backend no terminal (erros de API)

---

## Portas utilizadas

| Porta | Servico |
|-------|---------|
| 8000 | YOLO Service (FastAPI) |
| 3001 | Backend (NestJS) |
| 8080 | Frontend (Vite) |
| 27017 | MongoDB (se local) |
| 6379 | Redis (se local) |
