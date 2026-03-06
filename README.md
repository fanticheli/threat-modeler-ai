# Threat Modeler AI

Sistema de modelagem de ameacas automatizada que analisa diagramas de arquitetura usando IA (pipeline hibrido YOLO + Claude Vision) e gera relatorios baseados na metodologia STRIDE.

## Visao Geral

O Threat Modeler AI e uma ferramenta que permite:

1. **Upload de Diagramas** - Envie imagens de arquitetura de software
2. **Deteccao Hibrida** - Modelo YOLO treinado + Claude Vision detectam componentes
3. **Analise STRIDE** - Cada componente e analisado por ameacas
4. **Relatorios** - Exporte em PDF, JSON ou Markdown

## Repositorios

| Repositorio | Descricao | Stack |
|-------------|-----------|-------|
| [threat-modeler-ai](https://github.com/fanticheli/threat-modeler-ai) | Documentacao, Dataset, YOLO Service | Docs, Python, FastAPI |
| [threat-modeler-ai-frontend](https://github.com/fanticheli/threat-modeler-ai-frontend) | Interface Web (Frontend) | React, Vite, shadcn/ui, TailwindCSS, Framer Motion |
| [threat-modeler-ai-backend](https://github.com/fanticheli/threat-modeler-ai-backend) | API REST | NestJS, TypeScript, MongoDB, Redis |

## Documentacao

> **Comece por aqui** — os links essenciais para entender e rodar o projeto.

### Como rodar

| Documento | Descricao |
|-----------|-----------|
| **[Guia de Provisionamento Local](./docs/GUIA-PROVISIONAMENTO-LOCAL.md)** | Passo a passo completo com Docker Compose (sobe tudo com 1 comando) |
| [Setup Manual](./README-SETUP.md) | Alternativa: subir cada servico manualmente |

### Documentacao da Solucao

| Documento | Descricao |
|-----------|-----------|
| **[Documentacao Completa da Solucao](./docs/DOCUMENTACAO-SOLUCAO.md)** | Documento principal: visao geral, decisoes, metricas, resultados |
| [Arquitetura do Sistema](./docs/architecture/README.md) | Diagrama de componentes, fluxo de dados, integracao entre servicos |
| [Documentacao da API](./docs/api/README.md) | Endpoints REST, schemas de request/response, status codes |
| [Metodologia STRIDE](./docs/stride-methodology.md) | Como a analise de ameacas STRIDE e aplicada |

### Decisoes Tecnicas e Treinamento

| Documento | Descricao |
|-----------|-----------|
| [Decisoes de Arquitetura (ADRs)](./docs/adr/README.md) | ADR-001 a ADR-006: multi-repo, YOLO microservice, pipeline hibrido, etc |
| [Plano de Dataset e Treinamento](./docs/PLANO-DATASET-TREINAMENTO.md) | Pipeline de dataset, anotacao, treinamento YOLOv8, metricas |
| [Design System](./docs/design-system/README.md) | Paleta de cores, tipografia, componentes UI |
| [Backlog Multicloud](./docs/BACKLOG-MULTICLOUD.md) | Roadmap futuro: suporte a Azure, GCP, multi-provider |

## Stack Tecnologica

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                     │
│             React + Vite + shadcn/ui + TailwindCSS              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼ HTTP/REST + SSE
┌─────────────────────────────────────────────────────────────────┐
│                           BACKEND                               │
│                     NestJS + TypeScript                         │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │   Upload     │  │  Analysis    │  │   Report Gen           │ │
│  │   Module     │  │   Module     │  │   Module               │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │            AI Service (Pipeline Hibrido)                    ││
│  │  ┌────────────────┐  ┌───────────────┐  ┌────────────────┐  ││
│  │  │ YoloService    │  │ Claude Vision │  │ Merge + STRIDE │  ││
│  │  │ (HTTP Client)  │  │ (Anthropic)   │  │ Analysis       │  ││
│  │  └───────┬────────┘  └───────────────┘  └────────────────┘  ││
│  └──────────┼──────────────────────────────────────────────────┘│
└─────────────┼───────────────────────────────────────────────────┘
              │          │                    │                │
              ▼          ▼                    ▼                ▼
   ┌──────────────┐ ┌──────────┐       ┌──────────┐    ┌──────────┐
   │ YOLO Service │ │ MongoDB  │       │  Redis   │    │  Claude  │
   │  (FastAPI)   │ │  Atlas   │       │ (BullMQ) │    │   API    │
   │  Python +    │ └──────────┘       └──────────┘    └──────────┘
   │  best.pt     │
   └──────────────┘
```

## Pipeline Hibrido (YOLO + Claude Vision)

O diferencial do sistema e o pipeline hibrido que combina dois modelos de IA:

| Fase | Modelo | O que faz | Tempo |
|------|--------|-----------|-------|
| 1 | **YOLO** (modelo treinado) | Detecta componentes com bounding boxes | ~200ms |
| 2 | **Claude Vision** (LLM) | Detecta componentes com descricoes e conexoes | ~5-10s |
| 3 | **Merge** | Combina resultados, marca como hybrid/claude/yolo | instantaneo |
| 4 | **STRIDE** (Claude) | Analisa ameacas por componente | ~2-5s/comp |

Se o YOLO service nao estiver disponivel, o sistema funciona normalmente apenas com Claude Vision (fallback gracioso).

## Quick Start

Guia completo: **[Guia de Provisionamento Local](./docs/GUIA-PROVISIONAMENTO-LOCAL.md)**

```bash
# 1. Clone os 3 repos na mesma pasta
git clone https://github.com/fanticheli/threat-modeler-ai.git
git clone https://github.com/fanticheli/threat-modeler-ai-backend.git
git clone https://github.com/fanticheli/threat-modeler-ai-frontend.git

# 2. Configure a API key
cd threat-modeler-ai
echo "ANTHROPIC_API_KEY=sua_chave_aqui" > .env

# 3. Suba tudo com Docker Compose (5 servicos)
docker compose up -d --build

# 4. Acesse http://localhost:8080
```

## Dataset e Treinamento

- **66 imagens** de diagramas de arquitetura (AWS, Azure, GCP, generic)
- **10 classes consolidadas** de componentes (server, database, network, storage, security, serverless, queue, monitoring, user, external)
- **855 anotacoes** geradas semi-automaticamente com Claude Vision
- **Treinamento YOLOv8 small (v5)** com transfer learning (150 epochs completos, mAP50=83.9%)
- **Modelo integrado** ao backend via microsservico FastAPI

Detalhes em: [Plano de Dataset e Treinamento](./docs/PLANO-DATASET-TREINAMENTO.md)

## Metodologia STRIDE

| Categoria | Descricao |
|-----------|-----------|
| **S**poofing | Falsificacao de identidade |
| **T**ampering | Adulteracao de dados |
| **R**epudiation | Negacao de acoes |
| **I**nformation Disclosure | Vazamento de informacoes |
| **D**enial of Service | Negacao de servico |
| **E**levation of Privilege | Escalacao de privilegios |

## Licenca

MIT

## Autores

- [@fanticheli](https://github.com/fanticheli)
