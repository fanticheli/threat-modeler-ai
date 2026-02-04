# ADR-002: NestJS para Backend

## Status
Aceito

## Contexto
Precisávamos escolher um framework para a API REST. Opções consideradas:
- Express.js puro
- Fastify
- NestJS
- Koa

## Decisão
Escolhemos **NestJS** pelos seguintes motivos:
- Arquitetura modular (módulos, controllers, services)
- Suporte nativo a TypeScript
- Dependency Injection built-in
- Integração fácil com BullMQ, Mongoose
- Documentação excelente

## Consequências

### Positivas
- Código organizado e padronizado
- Fácil de testar (DI facilita mocks)
- Muitos decorators úteis (@Controller, @Injectable, etc.)
- Boa integração com ferramentas de fila

### Negativas
- Curva de aprendizado maior que Express puro
- Mais boilerplate
- Bundle maior
