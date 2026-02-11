# Arquitetura do Sistema

## Visao Geral

O Threat Modeler AI e composto por quatro servicos principais que se comunicam via REST API:

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Browser    │ ──────► │   Frontend   │ ──────► │   Backend    │
│              │   HTTP  │ (React+Vite) │   REST  │   (NestJS)   │
└──────────────┘         └──────────────┘         └──────┬───────┘
                                                         │
                         ┌───────────────┬───────────────┼───────────────┐
                         │               │               │               │
                         ▼               ▼               ▼               ▼
                  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                  │ YOLO Service │ │   MongoDB    │ │    Redis     │ │   Claude     │
                  │  (FastAPI)   │ │   (dados)    │ │   (filas)    │ │    API       │
                  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

## Componentes

### Frontend (React + Vite)

**Responsabilidades:**
- Interface de upload de imagens
- Visualizacao de analises
- Acompanhamento de progresso em tempo real (SSE)
- Exportacao de relatorios

**Tecnologias:**
- React 18 + Vite
- TypeScript
- shadcn/ui + TailwindCSS
- Framer Motion (animacoes)
- React Query (cache/fetching)
- React Dropzone

### Backend (NestJS)

**Responsabilidades:**
- Receber e armazenar imagens
- Orquestrar pipeline hibrido de analise (YOLO + Claude)
- Processar filas de jobs
- Gerar relatorios

**Modulos:**
| Modulo | Responsabilidade |
|--------|------------------|
| Upload | Recebe imagens e cria analise |
| Analysis | CRUD de analises |
| AI | Pipeline hibrido: YoloService + Claude Vision + Merge + STRIDE |
| Queue | Processamento assincrono (BullMQ) |
| Report | Geracao de PDF/JSON/Markdown |

### YOLO Service (FastAPI)

**Responsabilidades:**
- Carregar modelo YOLO treinado (best.pt) no startup
- Executar inferencia em imagens recebidas via HTTP
- Retornar deteccoes com bounding boxes, classes e confianca
- Mapear classes YOLO para tipos do backend

**Tecnologias:**
- Python 3.11
- FastAPI + Uvicorn
- Ultralytics (YOLOv8)
- Pillow (processamento de imagens)

**Endpoints:**
| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/health` | Health check (modelo carregado?) |
| POST | `/predict` | Inferencia YOLO na imagem |

### Banco de Dados (MongoDB)

**Collections:**
- `analyses` - Armazena todas as analises com componentes, conexoes, threats e detectionMeta

### Fila de Jobs (Redis + BullMQ)

**Filas:**
- `analysis-queue` - Processa analises de forma assincrona

## Fluxo de Dados

### 1. Upload de Imagem

```
User ──► Frontend ──► POST /api/upload ──► Backend
                                              │
                                              ├── Salva imagem em Base64 no MongoDB
                                              ├── Cria documento no MongoDB
                                              └── Adiciona job na fila
```

### 2. Processamento de Analise (Pipeline Hibrido)

```
Queue Worker (analysis.processor.ts)
      │
      ├── Fase 1: YOLO Service (HTTP POST /predict)
      │   └── Retorna bounding boxes + classes + confianca (~200ms)
      │
      ├── Fase 2: Claude Vision (Anthropic API)
      │   └── Retorna componentes + descricoes + conexoes (~5-10s)
      │
      ├── Fase 3: Merge (ai.service.ts → mergeDetections)
      │   ├── Matching por tipo (YOLO backend_type == Claude type)
      │   ├── Componentes confirmados por ambos → 'hybrid'
      │   ├── Componentes so Claude → 'claude'
      │   └── Componentes so YOLO (conf >= 8%) → 'yolo'
      │
      ├── Fase 4: STRIDE por componente (Claude API)
      │   └── Para cada componente: ameacas + contramedidas
      │
      └── Salva resultado no MongoDB (inclui detectionMeta)
```

### 3. Acompanhamento de Progresso

```
Frontend ◄──── SSE ────► GET /api/analysis/:id/progress/stream
                              │
                              └── Le progresso do MongoDB
```

### 4. Fallback (YOLO Indisponivel)

```
Queue Worker
      │
      ├── isAvailable() → false (YOLO fora do ar)
      │
      ├── Pula Fase 1 (YOLO)
      ├── Executa Fase 2 (Claude Vision) normalmente
      ├── Merge: todos componentes marcados como 'claude'
      └── Fase 4 (STRIDE) normalmente
```

## Decisoes de Arquitetura

Ver [ADRs](../adr/README.md) para detalhes sobre decisoes tecnicas.

## Diagramas

- [Diagrama de Contexto](./context-diagram.md)
- [Diagrama de Containers](./container-diagram.md)
- [Fluxo de Dados](./data-flow.md)
