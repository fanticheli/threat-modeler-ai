# ADR-001: Estrutura Multi-Repo

## Status
Aceito

## Contexto
Precisávamos decidir como organizar o código do projeto. As opções eram:
1. **Monorepo** - Frontend e backend no mesmo repositório
2. **Multi-repo** - Repositórios separados por stack

## Decisão
Optamos por **multi-repo** com 3 repositórios:
- `threat-modeler-ai` - Documentação e arquitetura
- `threat-modeler-ai-frontend` - Aplicação React + Vite
- `threat-modeler-ai-backend` - API NestJS

## Consequências

### Positivas
- Deploys independentes
- Times podem trabalhar separadamente
- CI/CD mais simples por repo
- Versionamento independente

### Negativas
- Precisa clonar múltiplos repos
- Sincronização de versões manual
- Mais repositórios para gerenciar
