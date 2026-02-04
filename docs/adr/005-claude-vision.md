# ADR-005: Claude Vision para Análise de Imagens

## Status
Aceito

## Contexto
Precisávamos de uma IA capaz de:
1. Analisar imagens de arquitetura
2. Identificar componentes e conexões
3. Realizar análise de segurança STRIDE
4. Gerar texto em múltiplos idiomas

Opções consideradas:
- OpenAI GPT-4 Vision
- Claude Vision (Anthropic)
- Google Gemini Pro Vision

## Decisão
Escolhemos **Claude Vision** (modelo claude-sonnet-4-20250514) porque:
- Excelente compreensão de diagramas técnicos
- Seguir instruções complexas (prompts de STRIDE)
- Bom suporte a português
- Context window grande (permite prompts detalhados)

## Consequências

### Positivas
- Alta qualidade na detecção de componentes
- Análises STRIDE detalhadas e contextuais
- Suporte nativo a múltiplos idiomas
- API simples de usar

### Negativas
- Custo por token (API paga)
- Dependência de serviço externo
- Latência de rede
- Rate limits
