# Plano de Implementação - Dataset e Treinamento de Modelo

> **Nota:** Este documento foi o plano ORIGINAL do projeto. A implementacao real evoluiu significativamente:
> - **Classes:** Plano previa 24+ classes granulares. Implementacao consolidou para **10 classes semanticas** para aumentar densidade de anotacoes por classe.
> - **Modelo:** Plano previa YOLOv8m (medio). Implementacao comecou com **YOLOv8n (nano)** na v3 e evoluiu para **YOLOv8s (small)** na v5.
> - **Dataset:** Plano previa 500+ imagens. Resultado real: **66 imagens**, anotadas semi-automaticamente com Claude Vision, com **pre-processamento e augmentacao** para balanceamento.
> - **Metricas:** Targets do plano (mAP50 > 0.80) foram **ALCANCADOS na v5**: mAP50=**83.9%**, recall=**82%**, precision=**99.7%**. A chave foi iterar (4 versoes) e melhorar os dados.
> - Para os dados reais, consulte: `dataset/runs/detect/runs/train/` e `docs/DOCUMENTACAO-SOLUCAO.md`

## Visão Geral

Este documento detalha o planejamento para implementar os seguintes objetivos do hackathon:

1. Construir ou buscar um Dataset de imagens de Arquitetura de Software
2. Anotar o Dataset para treinar modelo supervisionado
3. Treinar o modelo para identificar componentes
4. Buscar vulnerabilidades e contramedidas por componente

---

## 1. Dataset de Imagens de Arquitetura

### 1.1 Fontes de Dados

| Fonte | Tipo | Quantidade Estimada | Licença |
|-------|------|---------------------|---------|
| AWS Architecture Icons | Diagramas oficiais | 50+ exemplos | Uso permitido |
| Azure Architecture Center | Diagramas oficiais | 50+ exemplos | Uso permitido |
| GCP Architecture Diagrams | Diagramas oficiais | 30+ exemplos | Uso permitido |
| Draw.io Templates | Templates públicos | 100+ exemplos | MIT/Apache |
| Lucidchart Gallery | Diagramas públicos | 50+ exemplos | Verificar |
| GitHub Repos | READMEs com diagramas | 200+ exemplos | Varia |
| Criação própria | Diagramas sintéticos | 50+ exemplos | Própria |

### 1.2 Estrutura do Dataset

```
dataset/
├── images/
│   ├── aws/
│   │   ├── arch_001.png
│   │   ├── arch_002.png
│   │   └── ...
│   ├── azure/
│   ├── gcp/
│   ├── generic/
│   └── multi-cloud/
├── annotations/
│   ├── arch_001.json
│   ├── arch_002.json
│   └── ...
├── splits/
│   ├── train.txt      # 70%
│   ├── validation.txt # 15%
│   └── test.txt       # 15%
└── metadata.json
```

### 1.3 Script de Coleta

```python
# scripts/collect_dataset.py

import requests
import os
from pathlib import Path

SOURCES = {
    'aws': [
        'https://aws.amazon.com/architecture/reference-architecture-diagrams/',
        # ... mais URLs
    ],
    'azure': [
        'https://docs.microsoft.com/en-us/azure/architecture/',
        # ... mais URLs
    ]
}

def collect_images():
    """Coleta imagens das fontes definidas"""
    pass

def validate_image(image_path):
    """Valida qualidade da imagem (resolução, formato)"""
    pass

def deduplicate(images):
    """Remove imagens duplicadas usando hash perceptual"""
    pass
```

---

## 2. Anotação do Dataset

### 2.1 Schema de Anotação (COCO Format)

```json
{
  "image_id": "arch_001",
  "file_name": "aws/arch_001.png",
  "width": 1920,
  "height": 1080,
  "annotations": [
    {
      "id": 1,
      "category": "ec2_instance",
      "bbox": [100, 200, 150, 100],
      "segmentation": [[100, 200, 250, 200, 250, 300, 100, 300]],
      "attributes": {
        "label": "Web Server",
        "provider": "aws",
        "service": "EC2"
      }
    },
    {
      "id": 2,
      "category": "database",
      "bbox": [400, 300, 120, 80],
      "attributes": {
        "label": "RDS MySQL",
        "provider": "aws",
        "service": "RDS"
      }
    }
  ],
  "connections": [
    {
      "from": 1,
      "to": 2,
      "protocol": "TCP",
      "port": "3306"
    }
  ]
}
```

### 2.2 Categorias de Componentes (Classes)

```python
COMPONENT_CATEGORIES = {
    # Compute
    "ec2_instance": {"id": 1, "supercategory": "compute"},
    "lambda_function": {"id": 2, "supercategory": "compute"},
    "container": {"id": 3, "supercategory": "compute"},
    "kubernetes_pod": {"id": 4, "supercategory": "compute"},

    # Database
    "database_relational": {"id": 10, "supercategory": "database"},
    "database_nosql": {"id": 11, "supercategory": "database"},
    "database_cache": {"id": 12, "supercategory": "database"},

    # Network
    "load_balancer": {"id": 20, "supercategory": "network"},
    "api_gateway": {"id": 21, "supercategory": "network"},
    "cdn": {"id": 22, "supercategory": "network"},
    "firewall": {"id": 23, "supercategory": "network"},
    "vpc": {"id": 24, "supercategory": "network"},

    # Storage
    "object_storage": {"id": 30, "supercategory": "storage"},
    "block_storage": {"id": 31, "supercategory": "storage"},
    "file_storage": {"id": 32, "supercategory": "storage"},

    # Security
    "iam": {"id": 40, "supercategory": "security"},
    "kms": {"id": 41, "supercategory": "security"},
    "waf": {"id": 42, "supercategory": "security"},

    # Messaging
    "queue": {"id": 50, "supercategory": "messaging"},
    "topic": {"id": 51, "supercategory": "messaging"},
    "event_bus": {"id": 52, "supercategory": "messaging"},

    # User/External
    "user": {"id": 60, "supercategory": "external"},
    "external_service": {"id": 61, "supercategory": "external"},
    "mobile_app": {"id": 62, "supercategory": "external"},
    "web_browser": {"id": 63, "supercategory": "external"},
}
```

### 2.3 Ferramenta de Anotação

**Opção 1: Label Studio (Recomendado)**
```bash
# Instalar
pip install label-studio

# Iniciar
label-studio start --port 8080

# Importar dataset
# Configurar projeto para Object Detection + Connections
```

**Opção 2: CVAT**
```bash
docker-compose -f cvat/docker-compose.yml up -d
```

**Opção 3: Script Semi-automático**
```python
# scripts/auto_annotate.py
# Usa Claude Vision para gerar anotações iniciais
# Humano revisa e corrige

def auto_annotate_with_llm(image_path):
    """Gera anotações usando Claude Vision"""
    prompt = """
    Analyze this architecture diagram and return bounding boxes
    for each component in COCO format...
    """
    # Chama Claude Vision
    # Retorna anotações para revisão humana
```

---

## 3. Treinamento do Modelo

### 3.1 Arquitetura do Modelo

**Opção A: YOLO v8 (Object Detection)**
```
Entrada: Imagem 640x640
    ↓
Backbone: CSPDarknet53
    ↓
Neck: PANet
    ↓
Head: Detect (multi-scale)
    ↓
Saída: Bounding boxes + classes
```

**Opção B: Detectron2 (Instance Segmentation)**
```
Entrada: Imagem variável
    ↓
Backbone: ResNet-101-FPN
    ↓
Region Proposal Network
    ↓
ROI Heads
    ↓
Saída: Masks + boxes + classes
```

### 3.2 Script de Treinamento (YOLOv8) - Implementacao Real (v5 - producao)

```python
# scripts/train_yolo.py (simplificado - ver arquivo real para detalhes)

from ultralytics import YOLO

# 10 classes consolidadas (de 30 originais)
CLASS_NAMES = [
    "server", "database", "network", "storage", "security",
    "serverless", "queue", "monitoring", "user", "external",
]

model = YOLO('yolov8s.pt')  # small (~11M params) - evoluiu de nano na v3

results = model.train(
    data='data.yaml',
    epochs=150,           # completou todos os 150 na v5
    imgsz=640,
    batch=8,              # CPU com auto-ajuste
    patience=50,          # early stopping (nao ativou na v5)
    device='cpu',

    # Loss weights (rebalanceados na v4/v5)
    box=5.0,              # era 7.5 (v3) - reduzido
    cls=1.5,              # era 0.5 (v3) - TRIPLICADO para melhorar recall
    dfl=1.5,

    # Augmentation adaptado para diagramas
    hsv_h=0.015, hsv_s=0.3, hsv_v=0.3,
    degrees=5,            # rotacao leve
    translate=0.1,
    scale=0.3,
    flipud=0.0,           # sem flip (diagramas tem orientacao semantica)
    fliplr=0.0,
    mixup=0.2,            # mistura 2 imagens
    copy_paste=0.3,       # copia objetos entre imagens
    close_mosaic=10,      # era 20 (v3) - desliga mosaic mais cedo

    # Otimizacao (mais agressiva que v3)
    optimizer='AdamW',
    lr0=0.01,             # era 0.001 (v3) - 10x maior
    lrf=0.01,
    cos_lr=True,          # cosine annealing (novo na v4/v5)
    warmup_epochs=5,      # era 3 (v3)
    weight_decay=0.0005,
)
```

### 3.3 Script de Treinamento (Detectron2)

```python
# scripts/train_detectron2.py

from detectron2.config import get_cfg
from detectron2.engine import DefaultTrainer
from detectron2 import model_zoo

cfg = get_cfg()
cfg.merge_from_file(model_zoo.get_config_file(
    "COCO-InstanceSegmentation/mask_rcnn_R_101_FPN_3x.yaml"
))

cfg.DATASETS.TRAIN = ("architecture_train",)
cfg.DATASETS.TEST = ("architecture_val",)
cfg.DATALOADER.NUM_WORKERS = 4

cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(
    "COCO-InstanceSegmentation/mask_rcnn_R_101_FPN_3x.yaml"
)
cfg.MODEL.ROI_HEADS.NUM_CLASSES = len(COMPONENT_CATEGORIES)

cfg.SOLVER.IMS_PER_BATCH = 4
cfg.SOLVER.BASE_LR = 0.0025
cfg.SOLVER.MAX_ITER = 10000
cfg.SOLVER.STEPS = (7000, 9000)

cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128

trainer = DefaultTrainer(cfg)
trainer.resume_or_load(resume=False)
trainer.train()
```

### 3.4 Métricas de Avaliação

| Métrica | Descrição | Target (plano) | v3 (nano) | **v5 (producao)** |
|---------|-----------|----------------|-----------|-------------------|
| mAP@50 | Mean Average Precision IoU 0.5 | > 0.80 | 0.005 | **0.839** |
| mAP@50-95 | Mean AP IoU 0.5-0.95 | > 0.60 | 0.001 | **0.834** |
| Precision | True Positives / Predictions | > 0.85 | 0.529 | **0.997** |
| Recall | True Positives / Ground Truth | > 0.80 | 0.014 | **0.820** |

> **Nota:** Os targets do plano foram **alcancados na v5** com 66 imagens + pre-processamento + augmentacao. A chave foi iterar 4 versoes e investir na qualidade dos dados.

---

## 4. Integração com Sistema de Vulnerabilidades

### 4.1 Mapeamento Componente → Ameaças STRIDE

```typescript
// src/modules/ai/threat-mapping.ts

interface ThreatMapping {
  componentType: string;
  strideThreats: {
    spoofing: string[];
    tampering: string[];
    repudiation: string[];
    informationDisclosure: string[];
    denialOfService: string[];
    elevationOfPrivilege: string[];
  };
  commonVulnerabilities: string[];  // CVE patterns
  countermeasures: string[];
}

const THREAT_DATABASE: ThreatMapping[] = [
  {
    componentType: 'api_gateway',
    strideThreats: {
      spoofing: [
        'API keys podem ser comprometidas',
        'Tokens JWT podem ser forjados se mal configurados',
      ],
      tampering: [
        'Requisições podem ser modificadas em trânsito',
        'Headers podem ser manipulados',
      ],
      repudiation: [
        'Falta de logging pode impedir auditoria',
      ],
      informationDisclosure: [
        'Mensagens de erro podem expor stack traces',
        'Headers podem revelar versões de software',
      ],
      denialOfService: [
        'Falta de rate limiting permite flood',
        'Payloads grandes podem esgotar recursos',
      ],
      elevationOfPrivilege: [
        'Broken access control permite acesso não autorizado',
        'IDOR pode expor recursos de outros usuários',
      ],
    },
    commonVulnerabilities: [
      'CVE-*-SSRF',
      'CVE-*-injection',
      'OWASP API Security Top 10',
    ],
    countermeasures: [
      'Implementar OAuth 2.0 / OpenID Connect',
      'Configurar rate limiting por IP/usuário',
      'Validar todos os inputs',
      'Usar HTTPS com TLS 1.3',
      'Implementar logging centralizado',
      'Configurar WAF',
    ],
  },
  {
    componentType: 'database_relational',
    strideThreats: {
      spoofing: [
        'Credenciais fracas podem ser adivinhadas',
        'Conexões não autenticadas',
      ],
      tampering: [
        'SQL Injection pode modificar dados',
        'Falta de integridade referencial',
      ],
      repudiation: [
        'Audit logs desabilitados',
        'Falta de tracking de mudanças',
      ],
      informationDisclosure: [
        'Dados sensíveis não criptografados',
        'Backups não protegidos',
        'Query results podem vazar dados',
      ],
      denialOfService: [
        'Queries não otimizadas podem travar o banco',
        'Connection pool exhaustion',
      ],
      elevationOfPrivilege: [
        'Usuário com privilégios excessivos',
        'Stored procedures com DEFINER privilegiado',
      ],
    },
    commonVulnerabilities: [
      'CWE-89: SQL Injection',
      'CWE-312: Cleartext Storage',
      'CWE-522: Weak Credentials',
    ],
    countermeasures: [
      'Usar prepared statements / parameterized queries',
      'Criptografar dados sensíveis (AES-256)',
      'Configurar TDE (Transparent Data Encryption)',
      'Implementar RBAC (Role-Based Access Control)',
      'Habilitar audit logging',
      'Configurar backups criptografados',
      'Usar connection pooling com limites',
    ],
  },
  // ... mais mapeamentos para cada tipo de componente
];
```

### 4.2 Base de Conhecimento de Vulnerabilidades

```typescript
// src/modules/ai/vulnerability-database.ts

interface Vulnerability {
  id: string;
  name: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  affectedComponents: string[];
  references: string[];
  countermeasures: string[];
}

const VULNERABILITY_DATABASE: Vulnerability[] = [
  {
    id: 'STRIDE-S-001',
    name: 'Weak Authentication',
    description: 'Sistema permite autenticação com credenciais fracas ou sem MFA',
    severity: 'high',
    affectedComponents: ['api_gateway', 'web_server', 'user'],
    references: [
      'OWASP A07:2021 - Identification and Authentication Failures',
      'CWE-287: Improper Authentication',
    ],
    countermeasures: [
      'Implementar política de senhas fortes',
      'Habilitar MFA (Multi-Factor Authentication)',
      'Usar OAuth 2.0 / SAML para SSO',
      'Implementar account lockout após tentativas falhas',
    ],
  },
  // ... centenas de vulnerabilidades mapeadas
];
```

---

## 5. Pipeline Completo

### 5.1 Fluxo de Processamento

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE DE ANÁLISE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. UPLOAD                                                       │
│     └─→ Validação de qualidade (Sharp)                          │
│                                                                  │
│  2. DETECÇÃO DE COMPONENTES                                      │
│     ├─→ Opção A: YOLO v8 (modelo treinado)                      │
│     └─→ Opção B: Claude Vision (LLM)                            │
│                                                                  │
│  3. CLASSIFICAÇÃO                                                │
│     └─→ Mapear detecções para categorias conhecidas             │
│                                                                  │
│  4. ANÁLISE STRIDE                                               │
│     ├─→ Consultar THREAT_DATABASE por componente                │
│     └─→ Enriquecer com Claude (contexto específico)             │
│                                                                  │
│  5. BUSCA DE VULNERABILIDADES                                    │
│     ├─→ Consultar VULNERABILITY_DATABASE                        │
│     └─→ Cross-reference com CVE/CWE databases                   │
│                                                                  │
│  6. GERAÇÃO DE CONTRAMEDIDAS                                     │
│     ├─→ Contramedidas padrão do database                        │
│     └─→ Contramedidas customizadas via Claude                   │
│                                                                  │
│  7. RELATÓRIO                                                    │
│     └─→ PDF / JSON / Markdown                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Arquitetura Híbrida (Modelo + LLM)

```typescript
// src/modules/ai/hybrid-analyzer.ts

class HybridAnalyzer {
  private yoloModel: YOLOModel;
  private claudeService: ClaudeService;
  private threatDatabase: ThreatDatabase;

  async analyze(image: Buffer): Promise<AnalysisResult> {
    // 1. Detecção com modelo treinado (rápido, offline)
    const detections = await this.yoloModel.detect(image);

    // 2. Enriquecer com LLM (contexto, conexões)
    const enrichedComponents = await this.claudeService.enrichDetections(
      image,
      detections,
    );

    // 3. Buscar ameaças no database local
    const baseThreats = this.threatDatabase.getThreatsForComponents(
      enrichedComponents,
    );

    // 4. Customizar ameaças com LLM (contexto específico)
    const customizedThreats = await this.claudeService.customizeThreats(
      enrichedComponents,
      baseThreats,
    );

    // 5. Gerar contramedidas
    const countermeasures = await this.generateCountermeasures(
      customizedThreats,
    );

    return {
      components: enrichedComponents,
      threats: customizedThreats,
      countermeasures,
    };
  }
}
```

---

## 6. Cronograma de Implementação

| Fase | Tarefa | Duração |
|------|--------|---------|
| 1 | Coleta de imagens (500+) | 1 semana |
| 2 | Setup ferramenta de anotação | 2 dias |
| 3 | Anotação do dataset | 2 semanas |
| 4 | Treinamento YOLO v8 | 3 dias |
| 5 | Avaliação e ajustes | 1 semana |
| 6 | Integração com backend | 3 dias |
| 7 | Base de vulnerabilidades | 1 semana |
| 8 | Testes end-to-end | 3 dias |
| **Total** | | **~6 semanas** |

---

## 7. Recursos Necessários

| Recurso | Especificação | Custo Estimado |
|---------|---------------|----------------|
| GPU para treinamento | NVIDIA RTX 3080+ ou Cloud | $50-200 |
| Armazenamento dataset | 10-50 GB | $5/mês |
| Label Studio hosting | Self-hosted ou Cloud | $0-50/mês |
| Tempo de anotação | 20h (500 imagens) | - |

---

## 8. Conclusão

Este plano permite implementar completamente os objetivos do hackathon:

1. ✅ **Dataset**: 66 imagens coletadas de fontes publicas (GitHub, Azure Architecture Center)
2. ✅ **Anotação**: Semi-automatica com Claude Vision API (855 anotacoes)
3. ✅ **Treinamento**: 3 iteracoes (v3→v5), YOLOv8s com 10 classes consolidadas, 150 epochs, **mAP50=83.9%**
4. ✅ **Vulnerabilidades**: Analise STRIDE por componente via Claude
5. ✅ **Contramedidas**: Sugestoes especificas por ameaca via Claude

A abordagem híbrida (modelo treinado + LLM) oferece o melhor dos dois mundos:
- **Modelo treinado (YOLO v5)**: Rapido (~200ms), bounding boxes, mAP50=83.9%, funciona offline
- **LLM (Claude Vision)**: Compreensao semantica, descricoes, conexoes entre componentes
- **Fallback gracioso**: Se YOLO indisponivel, sistema funciona apenas com Claude
