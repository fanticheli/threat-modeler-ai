# Arquitetura do Sistema

## Visão Geral

O Threat Modeler AI é composto por dois serviços principais que se comunicam via REST API:

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Browser    │ ──────► │   Frontend   │ ──────► │   Backend    │
│              │   HTTP  │   (Next.js)  │   REST  │   (NestJS)   │
└──────────────┘         └──────────────┘         └──────────────┘
                                                         │
                              ┌───────────────────────────┼───────────────────────────┐
                              │                           │                           │
                              ▼                           ▼                           ▼
                       ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
                       │   MongoDB    │           │    Redis     │           │   Claude     │
                       │   (dados)    │           │   (filas)    │           │    API       │
                       └──────────────┘           └──────────────┘           └──────────────┘
```

## Componentes

### Frontend (Next.js 14)

**Responsabilidades:**
- Interface de upload de imagens
- Visualização de análises
- Acompanhamento de progresso em tempo real (SSE)
- Exportação de relatórios

**Tecnologias:**
- Next.js 14 (App Router)
- TypeScript
- TailwindCSS
- React Dropzone

### Backend (NestJS)

**Responsabilidades:**
- Receber e armazenar imagens
- Orquestrar análise com IA
- Processar filas de jobs
- Gerar relatórios

**Módulos:**
| Módulo | Responsabilidade |
|--------|------------------|
| Upload | Recebe imagens e cria análise |
| Analysis | CRUD de análises |
| AI | Integração com Claude Vision |
| Queue | Processamento assíncrono (BullMQ) |
| Report | Geração de PDF/JSON/Markdown |

### Banco de Dados (MongoDB)

**Collections:**
- `analyses` - Armazena todas as análises com componentes, conexões e threats

### Fila de Jobs (Redis + BullMQ)

**Filas:**
- `analysis-queue` - Processa análises de forma assíncrona

## Fluxo de Dados

### 1. Upload de Imagem

```
User ──► Frontend ──► POST /api/upload ──► Backend
                                              │
                                              ├── Salva imagem em disco
                                              ├── Cria documento no MongoDB
                                              └── Adiciona job na fila
```

### 2. Processamento de Análise

```
Queue Worker ──► Detecta componentes (Claude Vision)
      │
      ├── Para cada componente:
      │   └── Análise STRIDE (Claude)
      │
      └── Salva resultado no MongoDB
```

### 3. Acompanhamento de Progresso

```
Frontend ◄──── SSE ────► GET /api/analysis/:id/progress/stream
                              │
                              └── Lê progresso do MongoDB
```

## Decisões de Arquitetura

Ver [ADRs](../adr/README.md) para detalhes sobre decisões técnicas.

## Diagramas

- [Diagrama de Contexto](./context-diagram.md)
- [Diagrama de Containers](./container-diagram.md)
- [Fluxo de Dados](./data-flow.md)
