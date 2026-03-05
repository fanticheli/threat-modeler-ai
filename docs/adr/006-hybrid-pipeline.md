# ADR-006: Pipeline Hibrido YOLO + Claude Vision

## Status
Aceito

## Contexto
Para detectar componentes em diagramas de arquitetura, tinhamos duas opcoes de IA disponiveis:

1. **So YOLO (modelo treinado)**: Rapido (~200ms), com metricas solidas apos evolucao (v5: mAP50=83.9%, recall=82%). Porem limitado a 10 classes, sem descricoes semanticas ou conexoes.
2. **So Claude Vision (LLM)**: Compreensao semantica excelente, descricoes ricas e identifica conexoes. Porem lento (~5-10s) e depende de API externa.

Cada modelo tem forcas complementares:
- YOLO tem alta precisao em deteccao (precision=99.7%) mas nao descreve componentes nem identifica conexoes
- Claude Vision gera descricoes ricas e conexoes mas nao produz bounding boxes precisos e nao funciona offline

## Decisao
Implementamos um **pipeline hibrido** que combina os dois modelos em `ai.service.ts`:

1. **YOLO Service** (Fase 1) e **Claude Vision** (Fase 2) executam sequencialmente
2. **Merge inteligente** combina resultados por tipo de componente:
   - Ambos detectaram o mesmo tipo: marca como `hybrid`
   - So Claude detectou: marca como `claude`
   - So YOLO detectou (conf >= 8%): marca como `yolo`
3. **Fallback gracioso**: se YOLO estiver indisponivel, pipeline continua so com Claude
4. Para cada componente merged: analise STRIDE com contramedidas

Claude Vision e a fonte principal (semantica rica, conexoes, descricoes). YOLO enriquece com deteccao rapida e score de confianca do modelo treinado.

## Consequencias

### Positivas
- Melhor cobertura que qualquer modelo isolado
- Cada componente marcado com sua origem (hybrid/claude/yolo) para rastreabilidade
- Sistema funciona mesmo sem YOLO (fallback gracioso)
- YOLO v5 contribui com deteccao de alta qualidade (mAP50=83.9%, recall=82%)
- YOLO adiciona velocidade (~200ms) ao pipeline
- Arquitetura permitiu iterar o modelo (v3→v5) sem mudar o pipeline

### Negativas
- Complexidade do merge (matching por tipo)
- Custo de manter dois modelos
- Resultado final depende da qualidade do merge
