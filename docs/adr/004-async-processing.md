# ADR-004: Processamento Assíncrono com BullMQ

## Status
Aceito

## Contexto
A analise de uma imagem envolve multiplas operacoes de IA:
1. Deteccao de componentes via YOLO Service (~200ms) e Claude Vision (~5-10s) em paralelo
2. Merge dos resultados (YOLO + Claude)
3. Analise STRIDE por componente (N chamadas ao Claude)

Isso pode levar de 30 segundos a vários minutos. Não podemos bloquear a request HTTP.

## Decisão
Implementar **processamento assíncrono** usando:
- **BullMQ** - Biblioteca de filas para Node.js
- **Redis** - Backend para persistência das filas
- **SSE (Server-Sent Events)** - Para notificar progresso ao frontend

### Fluxo
1. Upload cria análise + adiciona job na fila
2. Worker processa job em background
3. Frontend acompanha via SSE ou polling
4. Quando completo, resultado está no MongoDB

## Consequências

### Positivas
- Requests não bloqueiam
- Retry automático em caso de falha
- Escalável (múltiplos workers)
- Usuário vê progresso em tempo real

### Negativas
- Mais complexidade (Redis necessário)
- Mais infraestrutura para gerenciar
- Debugging mais difícil
