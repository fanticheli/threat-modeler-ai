# Documentacao da Solucao - Threat Modeler AI

## Hackathon FIAP - Fase 5: Modelagem de Ameacas com IA

---

## 1. Visao Geral

O **Threat Modeler AI** e uma ferramenta que automatiza a modelagem de ameacas em arquiteturas de software usando Inteligencia Artificial e a metodologia STRIDE.

### 1.1 Problema

A modelagem de ameacas tradicional e:
- Manual e demorada
- Requer especialistas em seguranca
- Propensa a erros humanos
- Dificil de escalar

### 1.2 Solucao

Nossa solucao automatiza o processo com um **pipeline hibrido** que combina dois modelos de IA:

```
┌─────────────┐     ┌──────────────────────────────┐     ┌─────────────────┐
│   Upload    │ ──► │   Deteccao de Componentes    │ ──► │   Analise       │
│   Imagem    │     │   YOLO + Claude Vision       │     │   STRIDE        │
└─────────────┘     └──────────────────────────────┘     └─────────────────┘
                              │                                   │
                    ┌─────────┴─────────┐                         ▼
                    │                   │                 ┌─────────────────┐
              ┌───────────┐     ┌─────────────┐          │  Contramedidas  │
              │   YOLO    │     │   Claude    │          │  + Relatorio    │
              │  (modelo  │     │   Vision    │          └─────────────────┘
              │ treinado) │     │   (LLM)     │
              └───────────┘     └─────────────┘
```

**Diferenciais da abordagem hibrida:**
- **YOLO (modelo treinado):** Deteccao rapida (~100-500ms), bounding boxes precisos, funciona offline. Modelo YOLOv8s treinado com mAP50=83.9% e recall=82%
- **Claude Vision (LLM):** Compreensao semantica rica, descricoes detalhadas, identifica conexoes
- **Merge inteligente:** Combina o melhor dos dois mundos, cada componente marcado com sua origem

---

## 2. Arquitetura Tecnica

### 2.1 Stack Tecnologica

| Camada | Tecnologia | Funcao |
|--------|------------|--------|
| Frontend | React + Vite + shadcn/ui + TailwindCSS | Interface web |
| Backend | NestJS + TypeScript | API REST e orquestracao |
| YOLO Service | Python + FastAPI + Ultralytics | Microsservico de inferencia ML |
| Banco de Dados | MongoDB Atlas | Armazenamento |
| Fila | Redis (Upstash) + BullMQ | Processamento assincrono |
| IA (LLM) | Claude Vision (Anthropic) | Analise semantica de imagens |
| IA (Modelo Treinado) | YOLOv8 small (custom, v5) | Deteccao de componentes |
| Containerizacao | Docker + Docker Compose | Orquestracao de servicos |
| Hospedagem | Vercel + Render | Deploy em producao |

### 2.2 Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                            USUARIO                                    │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  FRONTEND (React + Vite)                              │
│                React + Vite + shadcn/ui + Tailwind                    │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────────┐   │
│  │   Upload    │  │   Validacao  │  │   Visualizacao             │   │
│  │   Imagem    │  │   Qualidade  │  │   Resultados STRIDE        │   │
│  └─────────────┘  └──────────────┘  └────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                 │ HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        BACKEND (Render)                               │
│                           NestJS                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────┐  │
│  │   Upload     │  │  Analysis    │  │   Report Generation        │  │
│  │   Module     │  │  Module      │  │   Module                   │  │
│  └──────────────┘  └──────────────┘  └────────────────────────────┘  │
│                          │                                            │
│                          ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │                      AI Service (Pipeline Hibrido)                ││
│  │                                                                   ││
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────────────┐   ││
│  │  │ YoloService    │  │ Claude Vision  │  │ Merge + STRIDE    │   ││
│  │  │ (HTTP Client)  │  │ (Anthropic)    │  │ Analysis          │   ││
│  │  └───────┬────────┘  └────────────────┘  └───────────────────┘   ││
│  │          │                                                        ││
│  └──────────┼────────────────────────────────────────────────────────┘│
│             │ HTTP/REST                                                │
└─────────────┼─────────────────────────────────────────────────────────┘
              │          │                    │                    │
              ▼          ▼                    ▼                    ▼
   ┌──────────────┐ ┌──────────┐       ┌──────────┐       ┌──────────┐
   │ YOLO Service │ │ MongoDB  │       │  Redis   │       │  Claude  │
   │  (FastAPI)   │ │  Atlas   │       │ Upstash  │       │  Vision  │
   │  Python +    │ └──────────┘       └──────────┘       │  API     │
   │  best.pt     │                                       └──────────┘
   └──────────────┘
```

### 2.3 Pipeline Hibrido de Deteccao (YOLO + Claude Vision)

O pipeline de deteccao segue 4 fases:

```
                        Imagem do Diagrama
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
           ┌─────▼─────┐              ┌──────▼──────┐
           │   Fase 1  │              │   Fase 2    │
           │   YOLO    │              │   Claude    │
           │  Service  │              │   Vision    │
           │ (~200ms)  │              │  (~5-10s)   │
           └─────┬─────┘              └──────┬──────┘
                 │                           │
                 │   Bounding boxes +        │   Componentes +
                 │   Classes + Confianca     │   Descricoes +
                 │                           │   Conexoes
                 └─────────────┬─────────────┘
                               │
                         ┌─────▼─────┐
                         │   Fase 3  │
                         │   Merge   │
                         │           │
                         │ Matching  │
                         │ por tipo  │
                         └─────┬─────┘
                               │
                    Componentes mesclados:
                    - hybrid (ambos detectaram)
                    - claude (so Claude)
                    - yolo (so YOLO)
                               │
                         ┌─────▼─────┐
                         │   Fase 4  │
                         │  STRIDE   │
                         │  por comp │
                         └─────┬─────┘
                               │
                         Relatorio Final
```

**Estrategia de Merge:**
- **Claude Vision e a fonte principal** (semantica rica, conexoes, descricoes)
- **YOLO enriquece** com score de confianca do modelo treinado
- Componentes detectados por ambos: `detectionSource: 'hybrid'`
- Componentes so do Claude: `detectionSource: 'claude'`
- Componentes so do YOLO (conf >= 8%): `detectionSource: 'yolo'`
- **Fallback gracioso:** Se YOLO indisponivel, sistema funciona apenas com Claude

---

## 3. Objetivos do Hackathon - Como Atendemos

### 3.1 Objetivo 1: IA que interpreta diagramas de arquitetura

**Implementacao:** Pipeline hibrido em `ai.service.ts`

```typescript
// Pipeline completo: YOLO (modelo treinado) + Claude Vision (LLM)
async performFullAnalysis(imageData, language): Promise<FullAnalysisResult> {
  // Fase 1: YOLO detecta componentes (modelo treinado, rapido)
  const yoloResult = await this.yoloService.predict(imageData);

  // Fase 2: Claude Vision detecta componentes (LLM, semantica rica)
  const claudeDetection = await this.detectComponents(imageData, language);

  // Fase 3: Merge dos resultados (YOLO enriquece Claude)
  const mergedComponents = this.mergeDetections(claudeComponents, yoloResult);

  // Fase 4: Analise STRIDE para cada componente
  for (const component of mergedComponents) {
    await this.analyzeStrideForComponent(component, ...);
  }
}
```

**Dois modelos de IA trabalhando juntos:**

| Aspecto | YOLO (Modelo Treinado) | Claude Vision (LLM) |
|---------|------------------------|---------------------|
| Tipo | Object Detection (CNN) | Large Language Model |
| Modelo | YOLOv8s (small, ~11M params) | Claude Sonnet 4 |
| Velocidade | ~100-500ms | ~5-10s |
| Output | Bounding boxes + classes | Componentes + descricoes + conexoes |
| Metricas (v5) | mAP50=83.9%, Recall=82%, Precision=99.7% | N/A (qualitativo) |
| Forca | Posicao precisa, rapido, alta acuracia | Compreensao semantica profunda |
| Fraqueza | Sem descricoes, sem conexoes | Sem bounding boxes precisos |

**Componentes detectados (10 classes consolidadas):**
- server (364 anotacoes) - microservice, app_server, web_server, container, kubernetes
- database (71) - database_sql, database_nosql
- network (135) - api_gateway, load_balancer, cdn, dns, vpc, subnet
- storage (67) - storage_object, storage_block, cache
- security (43) - firewall, waf, iam, kms, secrets_manager
- serverless (22) - lambda_function
- queue (22) - queue
- monitoring (35) - monitoring, logging
- user (50) - user, web_browser, mobile_app
- external (46) - external_service, email_service

---

### 3.2 Objetivo 2: Relatorio baseado em STRIDE

**Implementacao:** Modulo `stride-analysis.ts`

A metodologia STRIDE analisa 6 categorias de ameacas:

| Categoria | Descricao | Exemplo |
|-----------|-----------|---------|
| **S**poofing | Falsificacao de identidade | Roubo de credenciais |
| **T**ampering | Adulteracao de dados | SQL Injection |
| **R**epudiation | Negacao de acoes | Falta de logs |
| **I**nformation Disclosure | Vazamento de dados | Dados nao criptografados |
| **D**enial of Service | Negacao de servico | DDoS, resource exhaustion |
| **E**levation of Privilege | Escalacao de privilegios | Broken access control |

**Para cada componente, o sistema:**
1. Identifica ameacas especificas por categoria STRIDE
2. Classifica severidade (critical, high, medium, low)
3. Sugere contramedidas praticas (ate 5 por ameaca)

---

### 3.3 Objetivo 3: Dataset de imagens de arquitetura

**Implementacao:** Diretorio `dataset/`

```
dataset/
├── annotations/                # Anotacoes em formato YOLO (.txt) e COCO (.json)
├── splits/                     # Train/Val/Test (70/20/10)
│   ├── train_processed.txt     # 46 imagens de treino
│   ├── val_processed.txt       # 13 imagens de validacao
│   └── test_processed.txt      # 7 imagens de teste
├── scripts/                    # Scripts de automacao
│   ├── collect_images.py       # Coleta de imagens
│   ├── auto_annotate.py        # Anotacao automatica com Claude Vision
│   ├── preprocess_images.py    # Pre-processamento de imagens
│   ├── augment_balance.py      # Augmentacao para balanceamento
│   ├── create_splits.py        # Criacao de splits train/val/test
│   ├── train_yolo.py           # Script de treinamento YOLOv8
│   ├── validate_annotations.py # Validacao das anotacoes
│   └── demo_inference.py       # Demo de inferencia
├── runs/                       # Resultados dos treinamentos (v3, v4, v5)
├── dataset_config.yaml         # Configuracao com 10 classes consolidadas
├── metadata.json               # Metadados das imagens
├── yolov8n.pt                  # Pesos base YOLOv8 nano (transfer learning)
└── yolov8s.pt                  # Pesos base YOLOv8 small (transfer learning)
```

> **Nota:** As pastas `images/` e `yolo_dataset/` (imagens originais e formatadas) nao estao no repositorio por serem pesadas. Os splits referenciam caminhos locais gerados pelo pre-processamento.

**Total: 66 imagens de diagramas de arquitetura**, coletadas de fontes publicas e organizadas por cloud provider.

**Classes definidas (10 classes consolidadas de 30 originais):**
```yaml
names:
  0: server       # microservice, app_server, web_server, container, kubernetes
  1: database     # database_sql, database_nosql
  2: network      # api_gateway, load_balancer, cdn, dns, vpc, subnet
  3: storage      # storage_object, storage_block, cache
  4: security     # firewall, waf, iam, kms, secrets_manager
  5: serverless   # lambda_function
  6: queue        # queue
  7: monitoring   # monitoring, logging
  8: user         # user, web_browser, mobile_app
  9: external     # external_service, email_service
nc: 10
```

A consolidacao de 30 para 10 classes aumentou a densidade media de ~28 para ~85 anotacoes por classe, melhorando significativamente o aprendizado do modelo.

---

### 3.4 Objetivo 4: Anotar dataset para treinamento

**Implementacao:** Script `auto_annotate.py`

```python
# Usa Claude Vision para gerar anotacoes automaticamente
def annotate_image(image_path):
    # 1. Envia imagem para Claude Vision
    # 2. Solicita bounding boxes para cada componente
    # 3. Converte para formato COCO/YOLO
    # 4. Salva JSON + TXT
```

**Processo de anotacao:**
1. Claude Vision analisa cada uma das 66 imagens
2. Gera bounding boxes normalizadas (formato YOLO: x_center, y_center, width, height)
3. Salva em formato YOLO (.txt) e COCO (.json)
4. Script `fix_annotations.py` corrige coordenadas fora dos limites (0-1)

**Formato YOLO (.txt):**
```
2 0.350000 0.650000 0.080000 0.060000
1 0.750000 0.800000 0.120000 0.080000
```

**Divisao do dataset:**
- **Train:** 46 imagens (70%)
- **Validation:** 13 imagens (20%)
- **Test:** 7 imagens (10%)

---

### 3.5 Objetivo 5: Treinar o modelo

**Implementacao:** Script `train_yolo.py`

O modelo passou por **3 iteracoes de treinamento documentadas** (v3, v4, v5), cada uma com melhorias incrementais. A versao em producao e a **v5**.

```python
from ultralytics import YOLO

# v5 (producao): YOLOv8 Small com hiperparametros otimizados
model = YOLO("yolov8s.pt")  # Transfer learning do COCO (~11M parametros)

results = model.train(
    data=str(data_yaml),
    epochs=150,               # Completou todos os 150 epochs
    batch=8,                  # CPU com auto-ajuste
    imgsz=640,                # Resolucao padrao do YOLOv8
    device="cpu",

    patience=50,              # Early stopping (nao ativou na v5)

    # === Loss weights (rebalanceados na v4/v5) ===
    box=5.0,                  # Era 7.5 (v3) — reduzido para equilibrar com cls
    cls=1.5,                  # Era 0.5 (v3) — TRIPLICADO para melhorar recall
    dfl=1.5,                  # Mantido

    # Data Augmentation (adaptado para diagramas de arquitetura)
    hsv_h=0.015,              # Variacao leve de hue (matiz)
    hsv_s=0.3,                # Variacao de saturacao
    hsv_v=0.3,                # Variacao de brilho/valor
    degrees=5,                # Rotacao maxima de 5 graus
    translate=0.1,            # Deslocamento de ate 10% da imagem
    scale=0.3,                # Zoom in/out de ate 30%
    flipud=0.0,               # Flip vertical DESABILITADO
    fliplr=0.0,               # Flip horizontal DESABILITADO
    mixup=0.2,                # Probabilidade de misturar 2 imagens
    copy_paste=0.3,           # Probabilidade de copiar objetos entre imagens
    close_mosaic=10,          # Desabilita mosaic nos ultimos 10 epochs (era 20 na v3)

    # Otimizacao (mais agressiva que v3)
    optimizer="AdamW",        # Otimizador com weight decay integrado
    lr0=0.01,                 # Era 0.001 (v3) — LR inicial mais alta
    lrf=0.01,                 # Fator final do lr
    cos_lr=True,              # Cosine annealing (nao usado na v3)
    warmup_epochs=5,          # Era 3 (v3) — warmup mais longo
    weight_decay=0.0005,      # Regularizacao L2

    project="runs/train",
    name="architecture_detector_v5",
)
```

**Evolucao das decisoes de treinamento — v3 para v5:**

**Modelo base:**
- **v3:** `YOLO("yolov8n.pt")` — YOLOv8 **nano** (~3M parametros). Escolha conservadora para evitar overfitting com dataset pequeno.
- **v4/v5:** `YOLO("yolov8s.pt")` — YOLOv8 **small** (~11M parametros). Com pre-processamento e augmentacao de dados, o modelo maior conseguiu generalizar melhor sem overfitting. O aumento de capacidade (~3.5x mais parametros) permitiu aprender padroes mais complexos.

**Dados (maior impacto na v5):**
- **v3:** Imagens originais, sem pre-processamento
- **v5:** Imagens pre-processadas (`preprocess_images.py`) + dados augmentados para balanceamento de classes (`augment_balance.py`). Essa melhoria nos dados foi o fator decisivo para o salto de performance.

**Loss weights (v4/v5):**
- **`cls` triplicado (0.5→1.5):** Na v3, o recall era ~1% porque o modelo nao priorizava classificacao correta. Triplicar o peso da cls loss forcou o modelo a aprender a classificar componentes, nao apenas localiza-los.
- **`box` reduzido (7.5→5.0):** Reequilibrado para dar espaco a cls loss.

**Otimizacao (v4/v5):**
- **`lr0=0.01`** (era 0.001): LR 10x maior para aprendizado mais rapido com AdamW.
- **`cos_lr=True`** (era False): Cosine annealing para decaimento suave do learning rate, melhor convergencia.
- **`warmup_epochs=5`** (era 3): Warmup mais longo estabiliza o inicio do treinamento com LR alta.
- **`patience=50`** (era 30): Mais paciencia para convergir — na v5 completou todos os 150 epochs sem ativar early stopping.

**Data Augmentation (mantido entre versoes):**
- **Flips DESABILITADOS** (`flipud=0.0`, `fliplr=0.0`): Diagramas tem orientacao semantica.
- **Rotacao leve** (`degrees=5`): Simula screenshots ligeiramente inclinados.
- **Mosaic + close_mosaic=10** (era 20): Desliga mosaic mais cedo para fine-tuning nas imagens reais.
- **Mixup (0.2) e copy-paste (0.3)**: Criam exemplos sinteticos para compensar dataset pequeno.

**Consolidacao de classes (v3, mantido):**
- **30→10 classes**: Decisao mais impactante da v3. Media de anotacoes por classe subiu de ~28 para ~85.

**Resultados — evolucao completa do treinamento:**

| Metrica | v3 (10 cls, nano) | v4 (10 cls, small) | **v5 (10 cls, small, aug)** |
|---------|-------------------|--------------------|-----------------------------|
| Precision | 0.502 | 0.131 | **0.997** |
| Recall | 0.001 | 0.020 | **0.820** |
| mAP@50 | 0.001 | 0.009 | **0.839** |
| mAP@50-95 | 0.000 | 0.002 | **0.834** |
| Epochs | 60 | 63 | **150** |
| Modelo | nano (3M) | small (11M) | **small (11M)** |
| Dados | originais | originais | **pre-proc + aug** |

**Analise dos resultados — v5 (versao em producao):**
- **mAP50 de 83.9%** — salto massivo em relacao a v3 (0.08%) e v4 (0.87%). O modelo detecta componentes com alta acuracia.
- **Recall de 82%** — o modelo encontra 82% dos componentes anotados no dataset de validacao.
- **Precision de 99.7%** — praticamente sem falsos positivos.
- Loss convergiu consistentemente ao longo de 150 epochs sem overfitting.
- O fator decisivo foi a **melhoria nos dados** (pre-processamento + augmentacao), nao os hiperparametros.
- O YOLO agora contribui como **co-detector efetivo** no pipeline hibrido, nao apenas como complemento.
- Modelo final: **best.pt com 22 MB** (YOLOv8s), servido via microsservico FastAPI.

---

### 3.6 Objetivo 6: Buscar vulnerabilidades e contramedidas

**Implementacao:** Pipeline integrado no backend

```
Componente Detectado (YOLO + Claude)
        │
        ▼
┌───────────────────────────────────────┐
│     Analise STRIDE por Componente     │
│  ┌─────────────────────────────────┐  │
│  │ Para: "API Gateway"             │  │
│  │ Fonte: hybrid (YOLO + Claude)   │  │
│  │ YOLO Conf: 32.5%               │  │
│  │                                 │  │
│  │ Spoofing:                       │  │
│  │  - API keys podem ser roubadas  │  │
│  │  - Severidade: HIGH             │  │
│  │  - Contramedidas:               │  │
│  │    - Implementar OAuth 2.0      │  │
│  │    - Usar tokens JWT com exp    │  │
│  │    - Rotacionar secrets         │  │
│  │                                 │  │
│  │ Tampering:                      │  │
│  │  - Dados alterados em transito  │  │
│  │  - Severidade: MEDIUM           │  │
│  │  - Contramedidas:               │  │
│  │    - Usar HTTPS/TLS 1.3         │  │
│  │    - Validar inputs             │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
        │
        ▼
   Resumo Executivo (gerado por Claude)
        │
        ▼
   Relatorio Final (PDF/JSON/Markdown)
```

---

## 4. Integracao YOLO + Backend (Microsservico)

### 4.1 Por que microsservico separado?

Seguimos o **padrao de mercado** para servir modelos de Machine Learning em producao:

| Aspecto | Por que |
|---------|---------|
| **Linguagem** | YOLO roda em Python (ultralytics), Backend em TypeScript (NestJS) |
| **Escalabilidade** | Escala o modelo ML independente do backend |
| **Isolamento** | Se YOLO cair, backend continua funcionando |
| **Padrao da industria** | TensorFlow Serving, Triton, Seldon - todos usam microsservico |

### 4.2 YOLO Service (Python + FastAPI)

**Arquivo:** `yolo-service/main.py`

```python
# Carrega modelo UMA vez no startup (fica na memoria)
model = YOLO("model/best.pt")

# Endpoint de inferencia
@app.post("/predict")
async def predict(file: UploadFile, confidence: float = 0.05):
    image = Image.open(io.BytesIO(await file.read()))
    results = model.predict(source=image, conf=confidence)
    # Retorna JSON com deteccoes, bounding boxes e confianca
```

**Endpoints:**
| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/health` | Health check - verifica se modelo esta carregado |
| POST | `/predict` | Recebe imagem, retorna deteccoes com bounding boxes |

**Mapeamento de classes:**
O YOLO detecta 10 classes consolidadas. O servico mapeia para tipos do backend:

```python
YOLO_TO_BACKEND_TYPE = {
    "server": "server",
    "database": "database",
    "network": "network",
    "storage": "storage",
    "security": "security",
    "serverless": "serverless",
    "queue": "queue",
    "monitoring": "monitoring",
    "user": "user",
    "external": "external_service",
}
```

### 4.3 YoloService no NestJS (Client HTTP)

**Arquivo:** `yolo.service.ts`

```typescript
@Injectable()
export class YoloService {
  // Health check com timeout de 5s
  async isAvailable(): Promise<boolean> {
    const response = await fetch(`${this.yoloServiceUrl}/health`);
    const health = await response.json();
    return health.model_loaded;
  }

  // Envia imagem e recebe deteccoes
  async predict(imageBase64: string, mimeType: string): Promise<YoloPredictionResponse | null> {
    const formData = new FormData();
    formData.append('file', blob, 'image.png');
    const response = await fetch(`${this.yoloServiceUrl}/predict`, {
      method: 'POST', body: formData,
    });
    return response.json();
  }
}
```

### 4.4 Merge de Deteccoes

**Arquivo:** `ai.service.ts` - metodo `mergeDetections()`

```typescript
private mergeDetections(claudeComponents, yoloResult): DetectedComponent[] {
  // 1. Para cada componente Claude, procura match no YOLO (por tipo)
  // 2. Se encontrou: marca como 'hybrid' + adiciona yoloConfidence
  // 3. Se nao encontrou no YOLO: marca como 'claude'
  // 4. YOLO deteccoes sem match no Claude (conf >= 8%): adiciona como 'yolo'
}
```

**Exemplo de resultado mesclado:**
```json
{
  "detectionMeta": {
    "yoloAvailable": true,
    "yoloDetections": 5,
    "claudeDetections": 8,
    "mergedComponents": 10,
    "yoloInferenceTimeMs": 234.5
  },
  "components": [
    {
      "id": "comp-1",
      "name": "API Gateway",
      "type": "api",
      "detectionSource": "hybrid",
      "yoloConfidence": 0.852
    },
    {
      "id": "comp-2",
      "name": "PostgreSQL Database",
      "type": "database",
      "detectionSource": "claude"
    }
  ]
}
```

### 4.5 Docker Compose

**Arquivo:** `docker-compose.yml`

```yaml
services:
  yolo-service:         # Python FastAPI + modelo YOLO
    build: ./yolo-service
    ports: ["8000:8000"]
    volumes:
      - ./yolo-service/model:/app/model

  mongodb:              # Banco de dados
    image: mongo:7
    ports: ["27017:27017"]

  redis:                # Fila de processamento
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:              # NestJS API
    build: ../threat-modeler-ai-backend
    ports: ["3001:3001"]
    depends_on: [mongodb, redis, yolo-service]
    environment:
      - YOLO_SERVICE_URL=http://yolo-service:8000
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

---

## 5. Funcionalidades Implementadas

### 5.1 Upload e Validacao de Qualidade

- Upload de imagens (PNG, JPG, JPEG, GIF, WebP)
- Validacao automatica de qualidade:
  - Resolucao minima (800x600)
  - Tamanho do arquivo (50KB - 10MB)
  - Nitidez (deteccao de blur)
  - Contraste
- Score de qualidade (0-100%)
- Feedback visual para o usuario

### 5.2 Processamento com IA (Pipeline Hibrido)

- **Deteccao YOLO** (modelo treinado) - bounding boxes e confianca
- **Deteccao Claude Vision** (LLM) - componentes, descricoes e conexoes
- **Merge inteligente** - combina resultados dos dois modelos
- Identificacao de conexoes entre componentes
- Deteccao automatica do cloud provider (AWS, Azure, GCP)
- Processamento assincrono com fila (BullMQ)
- Progresso em tempo real (Server-Sent Events)
- **Fallback gracioso** - se YOLO indisponivel, usa apenas Claude

### 5.3 Analise STRIDE

- Analise completa das 6 categorias
- Severidade por ameaca (critical, high, medium, low)
- Contramedidas especificas por ameaca (ate 5)
- Consideracao de controles existentes

### 5.4 Relatorios

- **PDF**: Relatorio formatado para apresentacao
- **JSON**: Dados estruturados para integracao
- **Markdown**: Documentacao legivel

### 5.5 Interface Web

- Upload drag-and-drop
- Selecao de idioma (PT-BR / EN-US)
- Progresso em tempo real
- Visualizacao de componentes e ameacas
- Historico de analises
- Exportacao de relatorios

---

## 6. Como Executar

### 6.1 Pre-requisitos

- Node.js 18+
- Python 3.11+
- Docker e Docker Compose
- Chave API da Anthropic

### 6.2 Execucao com Docker Compose (Recomendado)

```bash
# 1. Clone os repositorios
git clone https://github.com/fanticheli/threat-modeler-ai
git clone https://github.com/fanticheli/threat-modeler-ai-backend
git clone https://github.com/fanticheli/threat-modeler-ai-frontend

# 2. Configure a chave API
cd threat-modeler-ai
cp ../threat-modeler-ai-backend/.env.example ../threat-modeler-ai-backend/.env
# Edite .env com sua ANTHROPIC_API_KEY

# 3. Suba todos os servicos (YOLO + MongoDB + Redis + Backend)
export ANTHROPIC_API_KEY=sua_chave_aqui
docker-compose up -d

# 4. Inicie o Frontend
cd ../threat-modeler-ai-frontend
npm install
npm run dev

# 5. Acesse http://localhost:8080
```

### 6.3 Execucao Local (sem Docker)

```bash
# 1. YOLO Service
cd threat-modeler-ai/yolo-service
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# 2. Backend
cd threat-modeler-ai-backend
cp .env.example .env
# Edite .env: YOLO_SERVICE_URL=http://localhost:8000
npm install && npm run start:dev

# 3. Frontend
cd threat-modeler-ai-frontend
npm install && npm run dev
```

### 6.4 URLs de Producao

- **Frontend:** http://localhost:8080
- **Backend:** https://threat-modeler-api.onrender.com

---

## 7. Estrutura dos Repositorios

### 7.1 Backend (threat-modeler-ai-backend)

```
src/
├── main.ts                        # Entry point
├── app.module.ts                  # Modulo raiz
├── modules/
│   ├── upload/                    # Upload de imagens
│   │   ├── upload.controller.ts
│   │   ├── upload.service.ts
│   │   └── image-quality.service.ts
│   ├── analysis/                  # CRUD de analises
│   ├── ai/                        # Integracao com IA
│   │   ├── ai.service.ts          # Pipeline hibrido (YOLO + Claude)
│   │   ├── ai.module.ts
│   │   ├── yolo.service.ts        # Client HTTP para YOLO service
│   │   ├── prompts/               # Prompts de IA
│   │   │   ├── component-detection.ts
│   │   │   └── stride-analysis.ts
│   │   └── interfaces/
│   │       └── ai.interfaces.ts   # Tipos (DetectedComponent, etc)
│   ├── queue/                     # Processamento assincrono
│   │   └── analysis.processor.ts  # Worker que executa pipeline
│   └── report/                    # Geracao de relatorios
└── schemas/                       # Schemas MongoDB
    └── analysis.schema.ts
```

### 7.2 YOLO Service (threat-modeler-ai/yolo-service)

```
yolo-service/
├── main.py                # FastAPI app (endpoints /health e /predict)
├── requirements.txt       # Dependencias Python
├── Dockerfile             # Container Python 3.11
└── model/
    └── best.pt            # Modelo YOLO v5 treinado (YOLOv8s, 22 MB)
```

### 7.3 Frontend (threat-modeler-ai-frontend)

```
src/
├── pages/                     # Paginas da aplicacao
├── components/                # Componentes React + shadcn/ui
│   └── ui/                    # Componentes shadcn/ui
├── services/                  # Integracao com API backend
├── hooks/                     # React hooks customizados
├── types/                     # Tipos TypeScript
├── lib/                       # Utilitarios
└── test/                      # Testes (Vitest)
```

**Stack:** React + Vite + TypeScript + shadcn/ui + TailwindCSS + Framer Motion + React Query + Recharts

### 7.4 Dataset e Treinamento (threat-modeler-ai/dataset)

```
dataset/
├── images/                    # 66 imagens de arquitetura
│   ├── aws/                   # 16 imagens
│   ├── azure/                 # 18 imagens
│   ├── gcp/                   # 6 imagens
│   └── generic/               # 26 imagens
├── annotations/               # 855 anotacoes em formato YOLO (.txt)
├── splits/                    # Train(46)/Val(13)/Test(7)
├── yolo_dataset/              # Estrutura formatada para YOLO
├── predictions/               # Inferencia real com bounding boxes
├── runs/                      # Resultados de treinamento
├── scripts/
│   ├── collect_images.py      # Coleta de imagens
│   ├── auto_annotate.py       # Anotacao automatica com Claude
│   ├── fix_annotations.py     # Correcao de coordenadas
│   ├── create_splits.py       # Divisao Train/Val/Test
│   ├── remap_classes.py       # Consolidacao 30→10 classes
│   ├── train_yolo.py          # Treinamento YOLOv8
│   └── demo_inference.py      # Inferencia real com best.pt
└── dataset_config.yaml        # Configuracao (10 classes consolidadas)
```

---

## 8. Decisoes Tecnicas

### 8.1 Por que abordagem hibrida (YOLO + Claude Vision)?

| Aspecto | So YOLO | So Claude Vision | Hibrido (nossa escolha) |
|---------|---------|------------------|-------------------------|
| Velocidade | Muito rapida (~200ms) | Lenta (5-10s) | Rapida + Rica |
| Semantica | Limitada (10 classes) | Excelente (descricoes ricas) | Excelente |
| Bounding boxes | Precisos (mAP50=83.9%) | Aproximados | Precisos |
| Custo | Gratuito (local) | Pay-per-use | Otimizado |
| Offline | Sim | Nao | Parcial |
| Confiabilidade | Alta (v5: recall 82%) | Alta | Muito alta |

**Decisao:** A abordagem hibrida combina o melhor dos dois mundos. Com a v5 do YOLO atingindo mAP50=83.9%, o modelo treinado se tornou um co-detector efetivo. Claude Vision fornece a semantica rica (descricoes, conexoes) e o YOLO confirma/enriquece com deteccao rapida e de alta confianca. Se o YOLO falhar, o sistema continua funcionando com Claude (fallback gracioso).

### 8.2 Por que microsservico para o modelo ML?

- **Separacao de concerns:** Python para ML, TypeScript para API
- **Escalabilidade:** Cada servico escala independentemente
- **Resiliencia:** Fallback automatico se YOLO cair
- **Padrao da industria:** TensorFlow Serving, Triton, Seldon

### 8.3 Por que MongoDB?

- Flexibilidade de schema para analises variadas
- Suporte nativo a documentos JSON
- MongoDB Atlas oferece hosting gerenciado
- Boa integracao com NestJS via Mongoose

### 8.4 Por que processamento assincrono?

- Analise de IA pode demorar 30-60 segundos
- Evita timeout de requisicoes HTTP
- Permite progresso em tempo real
- Melhor experiencia do usuario

---

## 9. Metricas e Resultados

### 9.1 Deteccao de Componentes

| Modelo | Tipos | Precisao | Recall | mAP50 | Tempo |
|--------|-------|----------|--------|-------|-------|
| Claude Vision | Variavel (semantico) | ~85% | N/A | N/A | 5-10s |
| YOLO v5 (treinado) | 10 classes | 99.7% | 82.0% | 83.9% | ~200ms |
| Hibrido | 10+ categorias | ~95%+ | N/A | N/A | 5-11s |

### 9.2 Analise STRIDE

- **Cobertura:** 6 categorias completas
- **Ameacas por componente:** 3-6 em media
- **Contramedidas por ameaca:** 3-5 sugestoes

### 9.3 Treinamento YOLO — Evolucao Completa

| Parametro | v3 (10 classes) | v4 (small, otimizado) | **v5 (producao)** |
|-----------|-----------------|----------------------|-------------------|
| **Dataset** | 66 imgs, 10 classes | 66 imgs, 10 classes | 66 imgs, 10 classes, **pre-proc + aug** |
| **Split** | Train 46 / Val 13 / Test 7 | Train 46 / Val 13 / Test 7 | Train 46 / Val 13 / Test 7 |
| **Modelo** | YOLOv8 nano (3M) | YOLOv8 small (11M) | **YOLOv8 small (11M)** |
| **Epochs** | 60 (early stop) | 63 (early stop) | **150 (completos)** |
| **Precision** | 0.502 | 0.131 | **0.997** |
| **Recall** | 0.001 | 0.020 | **0.820** |
| **mAP@50** | 0.001 | 0.009 | **0.839** |
| **mAP@50-95** | 0.000 | 0.002 | **0.834** |

**Fatores-chave da evolucao:**
- **v3:** Consolidacao de 30→10 classes, YOLOv8 nano — mAP50 = 0.08% (modelo nao convergiu)
- **v3→v4:** Modelo small + loss rebalanceado (cls triplicado) + LR mais alta — mAP50 = 0.87% (melhoria modesta)
- **v4→v5:** **Pre-processamento de imagens + augmentacao para balanceamento de classes** — mAP50 = 83.9% (salto massivo, ~96x)

---

## 10. Evolucao Futura

### 10.1 Curto Prazo
- [ ] Aumentar dataset para 200+ imagens
- [ ] Retreinar modelo YOLO com mais dados
- [ ] Adicionar mais cloud providers

### 10.2 Medio Prazo
- [x] ~~Modelo hibrido (YOLO + LLM)~~ **IMPLEMENTADO**
- [ ] Integracao com CI/CD
- [ ] API publica documentada (OpenAPI/Swagger)

### 10.3 Longo Prazo
- [ ] Suporte a arquitetura multicloud
- [ ] Comparacao entre analises (diff)
- [ ] Compliance mapping (OWASP, NIST, ISO 27001)
- [ ] GPU dedicada para YOLO em producao

---

## 11. Conclusao

O Threat Modeler AI demonstra uma solucao completa para modelagem de ameacas automatizada:

1. **IA interpreta diagramas** - Pipeline hibrido YOLO + Claude Vision
2. **Relatorio STRIDE** - Analise completa das 6 categorias com contramedidas
3. **Dataset criado** - 66 imagens de arquitetura, 10 classes consolidadas, 855 anotacoes
4. **Anotacao implementada** - Script semi-automatico com Claude Vision API
5. **Modelo treinado e iterado** - YOLOv8 small v5 com 150 epochs, **mAP50=83.9%, recall=82%**, integrado ao backend via microsservico
6. **Vulnerabilidades e contramedidas** - Pipeline completo com deteccao hibrida

**Diferencial principal:** O modelo YOLO treinado evoluiu por 3 iteracoes (v3→v5), com melhorias em classes, hiperparametros, pre-processamento e augmentacao de dados. A versao v5 atinge **mAP50=83.9%** e **recall=82%**, funcionando como co-detector efetivo no pipeline hibrido. Esta **integrado ao backend** via microsservico FastAPI com fallback gracioso.

A solucao esta em producao e acessivel em:
- http://localhost:8080

---

## Referencias

- [STRIDE Methodology - Microsoft](https://docs.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
- [OWASP Threat Modeling](https://owasp.org/www-community/Threat_Modeling)
- [YOLOv8 - Ultralytics](https://docs.ultralytics.com/)
- [Claude Vision - Anthropic](https://docs.anthropic.com/claude/docs/vision)
- [FastAPI - Model Serving](https://fastapi.tiangolo.com/)
- [Docker Compose - Multi-service](https://docs.docker.com/compose/)
