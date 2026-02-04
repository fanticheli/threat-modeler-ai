# ADR-004: Processamento Assíncrono com BullMQ

## Status
Aceito

## Contexto
A análise de uma imagem envolve múltiplas chamadas à API do Claude:
1. Detecção de componentes (1 chamada)
2. Análise STRIDE por componente (N chamadas)

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
