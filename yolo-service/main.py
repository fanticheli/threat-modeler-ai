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
from collections import Counter
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
    / "architecture_detector_v5"
    / "weights"
    / "best.pt"
)

CATEGORY_NAMES = {
    0: "server",
    1: "database",
    2: "network",
    3: "storage",
    4: "security",
    5: "serverless",
    6: "queue",
    7: "monitoring",
    8: "user",
    9: "external",
}

# Mapeamento de classes YOLO -> tipos do backend
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
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
    status = "healthy" if model is not None else "model_not_loaded"
    logger.info(f"[Health] status={status}, model_loaded={model is not None}, classes={len(CATEGORY_NAMES)}")
    return HealthResponse(
        status=status,
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
    logger.info(f"[Predict] Recebida imagem: {file.filename} (confidence>={confidence})")

    if model is None:
        logger.error("[Predict] Modelo YOLO nao carregado — retornando 503")
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

    # Log deteccoes agrupadas por classe
    class_counts = Counter(d.class_name for d in detections)
    breakdown = ", ".join(f"{name}={count}" for name, count in class_counts.most_common())
    logger.info(f"[Predict] Inferencia: {round(inference_time, 2)}ms | Imagem: {img_width}x{img_height}")
    logger.info(f"[Predict] Deteccoes: {breakdown} | Total: {len(detections)}")

    return PredictionResponse(
        model="architecture-detector-yolov8s-v5",
        inference_time_ms=round(inference_time, 2),
        image_size={"width": img_width, "height": img_height},
        detections=detections,
        total_detections=len(detections),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
