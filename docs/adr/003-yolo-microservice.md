# ADR-003: YOLO como Microsservico FastAPI

## Status
Aceito

## Contexto
O modelo YOLO treinado (YOLOv8 small, v5 - mAP50=83.9%) precisa ser servido em producao para realizar inferencia em imagens de arquitetura. O backend principal e escrito em NestJS (TypeScript), mas o YOLO roda em Python (Ultralytics). Precisavamos decidir como integrar o modelo:

1. **Embutido no backend** - Chamar Python via child process ou binding
2. **Microsservico separado** - Servico Python independente com API HTTP
3. **Serverless** - Lambda/Cloud Function com modelo empacotado

## Decisao
Optamos por **microsservico separado** usando Python + FastAPI:
- `yolo-service/main.py` - App FastAPI que carrega best.pt no startup
- Endpoint `POST /predict` recebe imagem e retorna deteccoes em JSON
- Endpoint `GET /health` para monitoramento
- Containerizado via Docker (Python 3.11 slim)
- Orquestrado via Docker Compose junto com MongoDB, Redis e Backend

Segue o padrao de mercado de model serving (TensorFlow Serving, Triton Inference Server).

## Consequencias

### Positivas
- Separacao de concerns: Python para ML, TypeScript para API
- Escala independente do backend
- Se YOLO cair, backend continua funcionando (fallback gracioso)
- Deploy simples via Docker
- Modelo carregado uma vez na memoria (rapido: ~200ms por inferencia)

### Negativas
- Mais um servico para gerenciar
- Latencia de rede entre backend e YOLO service
- Requer Docker ou ambiente Python separado
