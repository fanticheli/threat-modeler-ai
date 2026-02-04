# API Documentation

Base URL: `http://localhost:3001/api`

## Endpoints

### Upload

#### POST /upload

Faz upload de uma imagem de arquitetura e inicia análise.

**Request:**
```
Content-Type: multipart/form-data

image: File (required) - Imagem PNG, JPG, JPEG, GIF ou WebP
language: string (optional) - "pt-BR" ou "en-US" (default: "pt-BR")
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "imageUrl": "/uploads/abc123.jpg",
  "imageName": "arquitetura.jpg",
  "status": "processing"
}
```

---

### Analysis

#### GET /analysis

Lista todas as análises.

**Response:**
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "imageName": "arquitetura.jpg",
    "status": "completed",
    "summary": {
      "totalComponents": 15,
      "totalThreats": 45,
      "criticalThreats": 2,
      "highThreats": 10,
      "mediumThreats": 20,
      "lowThreats": 13
    },
    "createdAt": "2024-02-03T10:00:00.000Z"
  }
]
```

#### GET /analysis/:id

Busca uma análise específica com todos os detalhes.

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "imageUrl": "/uploads/abc123.jpg",
  "imageName": "arquitetura.jpg",
  "language": "pt-BR",
  "status": "completed",
  "detectedProvider": "aws",
  "existingMitigations": ["AWS WAF", "AWS Shield"],
  "components": [
    {
      "id": "alb",
      "name": "Application Load Balancer",
      "type": "load_balancer",
      "provider": "aws",
      "description": "Distribui tráfego entre instâncias",
      "existingSecurityControls": ["SSL/TLS"]
    }
  ],
  "connections": [
    {
      "from": "cloudfront",
      "to": "alb",
      "protocol": "HTTPS",
      "port": "443",
      "description": "Tráfego de usuários",
      "encrypted": true
    }
  ],
  "strideAnalysis": [
    {
      "componentId": "alb",
      "threats": [
        {
          "category": "Denial of Service",
          "description": "Ataque DDoS pode sobrecarregar o load balancer",
          "severity": "high",
          "severityJustification": "Impacto direto na disponibilidade",
          "existingMitigation": "AWS Shield Standard",
          "countermeasures": [
            "Habilitar AWS Shield Advanced",
            "Configurar Auto Scaling"
          ]
        }
      ]
    }
  ],
  "summary": { ... },
  "createdAt": "2024-02-03T10:00:00.000Z"
}
```

#### POST /analysis/:id/process

Inicia ou reinicia o processamento de uma análise.

**Response:**
```json
{
  "message": "Análise iniciada",
  "jobId": "507f1f77bcf86cd799439011",
  "status": "processing"
}
```

#### GET /analysis/:id/progress

Retorna o progresso atual da análise.

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "status": "processing",
  "progress": {
    "step": "analyzing_stride",
    "message": "Analisando STRIDE: Application Load Balancer",
    "percentage": 45,
    "currentComponent": 5,
    "totalComponents": 15
  }
}
```

#### GET /analysis/:id/progress/stream

Stream SSE para acompanhar progresso em tempo real.

**Response (SSE):**
```
data: {"status":"processing","progress":{"step":"analyzing_stride","percentage":45}}

data: {"status":"processing","progress":{"step":"analyzing_stride","percentage":50}}

data: {"status":"completed","progress":{"step":"completed","percentage":100}}
```

#### DELETE /analysis/:id

Remove uma análise.

**Response:**
```json
{
  "message": "Análise excluída com sucesso"
}
```

---

### Reports

#### GET /report/:id/pdf

Baixa relatório em PDF.

**Response:** `application/pdf`

#### GET /report/:id/json

Baixa dados em JSON.

**Response:** `application/json`

#### GET /report/:id/markdown

Baixa relatório em Markdown.

**Response:** `text/markdown`

---

## Status Codes

| Code | Descrição |
|------|-----------|
| 200 | Sucesso |
| 201 | Criado |
| 400 | Bad Request |
| 404 | Não encontrado |
| 500 | Erro interno |

## Erros

```json
{
  "statusCode": 404,
  "message": "Análise com ID xxx não encontrada",
  "error": "Not Found"
}
```
