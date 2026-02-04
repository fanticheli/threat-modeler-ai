# Threat Modeler AI

Sistema de modelagem de ameaças automatizada que analisa diagramas de arquitetura usando IA (Claude Vision) e gera relatórios baseados na metodologia STRIDE.

## Visão Geral

O Threat Modeler AI é uma ferramenta que permite:

1. **Upload de Diagramas** - Envie imagens de arquitetura de software
2. **Detecção Automática** - IA identifica componentes e conexões
3. **Análise STRIDE** - Cada componente é analisado por ameaças
4. **Relatórios** - Exporte em PDF, JSON ou Markdown

## Repositórios

| Repositório | Descrição | Stack |
|-------------|-----------|-------|
| [threat-modeler-ai](https://github.com/fanticheli/threat-modeler-ai) | Documentação e Arquitetura | Docs |
| [threat-modeler-ai-frontend](https://github.com/fanticheli/threat-modeler-ai-frontend) | Interface Web | Next.js 14, TypeScript, TailwindCSS |
| [threat-modeler-ai-backend](https://github.com/fanticheli/threat-modeler-ai-backend) | API REST | NestJS, TypeScript, MongoDB, Redis |

## Documentação

- [Arquitetura do Sistema](./docs/architecture/README.md)
- [Design System](./docs/design-system/README.md)
- [Decisões de Arquitetura (ADRs)](./docs/adr/README.md)
- [Documentação da API](./docs/api/README.md)

## Stack Tecnológica

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│              Next.js 14 + TypeScript + TailwindCSS          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/REST + SSE
┌─────────────────────────────────────────────────────────────┐
│                         BACKEND                              │
│                   NestJS + TypeScript                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Upload    │  │  Analysis   │  │   Report Gen        │  │
│  │   Module    │  │   Module    │  │   Module            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              AI Service (Claude Vision)                  ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
    ┌──────────┐        ┌──────────┐        ┌──────────┐
    │ MongoDB  │        │  Redis   │        │ Claude   │
    │          │        │ (BullMQ) │        │   API    │
    └──────────┘        └──────────┘        └──────────┘
```

## Quick Start

### Pré-requisitos
- Docker e Docker Compose
- Node.js 18+
- Chave API da Anthropic

### 1. Clone os repositórios
```bash
git clone https://github.com/fanticheli/threat-modeler-ai-backend.git
git clone https://github.com/fanticheli/threat-modeler-ai-frontend.git
```

### 2. Configure o Backend
```bash
cd threat-modeler-ai-backend
cp .env.example .env
# Edite .env e adicione ANTHROPIC_API_KEY
docker-compose up -d
```

### 3. Configure o Frontend
```bash
cd threat-modeler-ai-frontend
npm install
npm run dev
```

### 4. Acesse
- Frontend: http://localhost:3000
- Backend: http://localhost:3001

## Metodologia STRIDE

| Categoria | Descrição |
|-----------|-----------|
| **S**poofing | Falsificação de identidade |
| **T**ampering | Adulteração de dados |
| **R**epudiation | Negação de ações |
| **I**nformation Disclosure | Vazamento de informações |
| **D**enial of Service | Negação de serviço |
| **E**levation of Privilege | Escalação de privilégios |

## Licença

MIT

## Autores

- [@fanticheli](https://github.com/fanticheli)
