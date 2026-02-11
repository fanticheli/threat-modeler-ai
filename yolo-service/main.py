"""
Microsservico FastAPI para inferencia do modelo YOLO treinado.

Padrao de mercado: modelo ML em servico Python separado,
comunicando com o backend principal (NestJS) via HTTP REST.

Uso:
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

import io
import time
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Dict, Optional

from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

# ---------------------------------------------------------------------------
# Configuracao
# ---------------------------------------------------------------------------

MODEL_PATH = Path(__file__).parent / "model" / "best.pt"
FALLBACK_MODEL_PATH = (
    Path(__file__).parent.parent
    / "dataset"
    / "runs"
    / "detect"
    / "runs"
    / "train"
    / "architecture_detector"
    / "weights"
    / "best.pt"
)

CATEGORY_NAMES = {
    0: "user",
    1: "web_browser",
    2: "mobile_app",
    3: "api_gateway",
    4: "load_balancer",
    5: "web_server",
    6: "app_server",
    7: "microservice",
    8: "container",
    9: "kubernetes",
    10: "lambda_function",
    11: "database_sql",
    12: "database_nosql",
    13: "cache",
    14: "queue",
    15: "storage_object",
    16: "storage_block",
    17: "cdn",
    18: "firewall",
    19: "waf",
    20: "vpc",
    21: "subnet",
    22: "iam",
    23: "kms",
    24: "secrets_manager",
    25: "monitoring",
    26: "logging",
    27: "external_service",
    28: "dns",
    29: "email_service",
}

# Mapeamento de classes YOLO -> tipos do backend
YOLO_TO_BACKEND_TYPE = {
    "user": "user",
    "web_browser": "user",
    "mobile_app": "user",
    "api_gateway": "api",
    "load_balancer": "load_balancer",
    "web_server": "server",
    "app_server": "server",
    "microservice": "server",
    "container": "server",
    "kubernetes": "server",
    "lambda_function": "serverless",
    "database_sql": "database",
    "database_nosql": "database",
    "cache": "cache",
    "queue": "queue",
    "storage_object": "storage",
    "storage_block": "storage",
    "cdn": "cdn",
    "firewall": "security",
    "waf": "waf",
    "vpc": "network",
    "subnet": "network",
    "iam": "security",
    "kms": "security",
    "secrets_manager": "security",
    "monitoring": "monitoring",
    "logging": "monitoring",
    "external_service": "external_service",
    "dns": "network",
    "email_service": "email",
}

logger = logging.getLogger("yolo-service")

# ---------------------------------------------------------------------------
# Modelo global (carregado uma unica vez no startup)
# ---------------------------------------------------------------------------
model = None


def load_model():
    """Carrega o modelo YOLO treinado."""
    global model
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("ultralytics nao instalado. Execute: pip install ultralytics")
        return

    # Tentar carregar modelo local primeiro, depois fallback
    model_path = MODEL_PATH if MODEL_PATH.exists() else FALLBACK_MODEL_PATH

    if not model_path.exists():
        logger.error(f"Modelo nao encontrado em {MODEL_PATH} nem em {FALLBACK_MODEL_PATH}")
        return

    logger.info(f"Carregando modelo YOLO de: {model_path}")
    model = YOLO(str(model_path))
    logger.info("Modelo YOLO carregado com sucesso!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: carrega modelo no startup, libera no shutdown."""
    load_model()
    yield
    logger.info("Shutting down YOLO service")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="YOLO Architecture Detector",
    description="Microsservico de inferencia para deteccao de componentes de arquitetura",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas de resposta
# ---------------------------------------------------------------------------

class BoundingBox(BaseModel):
    x_center: float
    y_center: float
    width: float
    height: float


class BoundingBoxPixels(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class Detection(BaseModel):
    class_id: int
    class_name: str
    backend_type: str
    confidence: float
    bbox_normalized: BoundingBox
    bbox_pixels: BoundingBoxPixels


class PredictionResponse(BaseModel):
    model: str
    inference_time_ms: float
    image_size: Dict[str, int]
    detections: List[Detection]
    total_detections: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str
    total_classes: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check - verifica se o modelo esta carregado."""
    model_path = MODEL_PATH if MODEL_PATH.exists() else FALLBACK_MODEL_PATH
    return HealthResponse(
        status="healthy" if model is not None else "model_not_loaded",
        model_loaded=model is not None,
        model_path=str(model_path),
        total_classes=len(CATEGORY_NAMES),
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(..., description="Imagem do diagrama de arquitetura"),
    confidence: float = Query(0.05, ge=0.01, le=1.0, description="Threshold minimo de confianca"),
):
    """
    Executa inferencia YOLO na imagem enviada.

    Retorna lista de componentes detectados com bounding boxes
    e scores de confianca.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo YOLO nao carregado")

    # Ler imagem
    image_bytes = await file.read()
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Imagem invalida: {e}")

    img_width, img_height = image.size

    # Inferencia
    start_time = time.time()
    results = model.predict(
        source=image,
        conf=confidence,
        verbose=False,
    )
    inference_time = (time.time() - start_time) * 1000  # ms

    # Processar resultados
    detections: List[Detection] = []
    for result in results:
        if result.boxes is None:
            continue
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = CATEGORY_NAMES.get(class_id, f"class_{class_id}")

            # Coordenadas normalizadas (0-1) - formato YOLO
            xywhn = box.xywhn[0]
            x_center = float(xywhn[0])
            y_center = float(xywhn[1])
            w = float(xywhn[2])
            h = float(xywhn[3])

            # Coordenadas em pixels
            xyxy = box.xyxy[0]
            x1 = int(xyxy[0])
            y1 = int(xyxy[1])
            x2 = int(xyxy[2])
            y2 = int(xyxy[3])

            detections.append(
                Detection(
                    class_id=class_id,
                    class_name=class_name,
                    backend_type=YOLO_TO_BACKEND_TYPE.get(class_name, "external_service"),
                    confidence=round(float(box.conf[0]), 4),
                    bbox_normalized=BoundingBox(
                        x_center=round(x_center, 6),
                        y_center=round(y_center, 6),
                        width=round(w, 6),
                        height=round(h, 6),
                    ),
                    bbox_pixels=BoundingBoxPixels(x1=x1, y1=y1, x2=x2, y2=y2),
                )
            )

    # Ordenar por confianca (maior primeiro)
    detections.sort(key=lambda d: d.confidence, reverse=True)

    return PredictionResponse(
        model="architecture-detector-yolov8n-v2",
        inference_time_ms=round(inference_time, 2),
        image_size={"width": img_width, "height": img_height},
        detections=detections,
        total_detections=len(detections),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
