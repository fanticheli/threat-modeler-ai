#!/usr/bin/env python3
"""
Script de demonstração de inferência REAL.
Usa o modelo YOLOv8 treinado (best.pt) para detectar componentes em diagramas de arquitetura.
Gera imagens com bounding boxes reais e relatório de métricas.
"""

import json
import sys
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    print("ERRO: ultralytics não instalado. Rode: pip install ultralytics")
    sys.exit(1)

from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).parent.parent

# Caminhos do modelo
MODEL_PATHS = [
    BASE_DIR / "runs" / "detect" / "runs" / "train" / "architecture_detector_v4" / "weights" / "best.pt",
    BASE_DIR.parent / "yolo-service" / "model" / "best.pt",
]

# Cores por categoria (10 classes consolidadas)
CATEGORY_COLORS = {
    0: "#34495e",   # server
    1: "#c0392b",   # database
    2: "#f39c12",   # network
    3: "#95a5a6",   # storage
    4: "#ff5722",   # security
    5: "#8e44ad",   # serverless
    6: "#f1c40f",   # queue
    7: "#009688",   # monitoring
    8: "#3498db",   # user
    9: "#ff6f00",   # external
}

CATEGORY_NAMES = {
    0: "server", 1: "database", 2: "network", 3: "storage",
    4: "security", 5: "serverless", 6: "queue", 7: "monitoring",
    8: "user", 9: "external",
}


def find_model():
    """Encontra o best.pt disponível."""
    for path in MODEL_PATHS:
        if path.exists():
            return path
    return None


def run_inference(model, image_path, output_path, conf_threshold=0.25):
    """Roda inferência real com YOLO e desenha bounding boxes."""
    results = model.predict(
        source=str(image_path),
        conf=conf_threshold,
        iou=0.45,
        imgsz=640,
        verbose=False,
    )

    result = results[0]
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    count = 0

    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]

        color = CATEGORY_COLORS.get(class_id, "#95a5a6")
        name = CATEGORY_NAMES.get(class_id, f"class_{class_id}")

        # Bounding box
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

        # Label
        label = f"{name} {confidence:.0%}"
        text_y = max(0, y1 - 18)

        try:
            bbox = draw.textbbox((x1, text_y), label)
            draw.rectangle([bbox[0] - 1, bbox[1] - 1, bbox[2] + 1, bbox[3] + 1], fill=color)
            draw.text((x1, text_y), label, fill="white")
        except Exception:
            draw.text((x1, text_y), label, fill=color)

        count += 1

    img.save(output_path, quality=95)
    return count, result


def load_metrics():
    """Carrega métricas do treinamento."""
    metrics_file = BASE_DIR / "predictions" / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            return json.load(f)
    return None


def main():
    output_dir = BASE_DIR / "predictions"
    output_dir.mkdir(exist_ok=True)
    images_dir = BASE_DIR / "images"

    print("=" * 60)
    print("Architecture Component Detection - Real Inference v3")
    print("=" * 60)

    # Encontrar modelo
    model_path = find_model()
    if model_path is None:
        print("\nERRO: best.pt não encontrado. Treine o modelo primeiro:")
        print("  python scripts/train_yolo.py --epochs 150 --batch 4")
        sys.exit(1)

    print(f"\nModelo: {model_path}")
    model = YOLO(str(model_path))
    print(f"Classes: {model.names}")

    # Selecionar TODAS as imagens do dataset
    all_images = []
    for provider in ["aws", "azure", "gcp", "generic"]:
        provider_dir = images_dir / provider
        if provider_dir.exists():
            imgs = sorted(provider_dir.glob("*.png")) + sorted(provider_dir.glob("*.jpg"))
            all_images.extend(imgs)

    print(f"\nRodando inferência real em {len(all_images)} imagens...\n")

    total_detections = 0
    detection_summary = {}
    images_with_detections = 0

    for img_path in all_images:
        output_path = output_dir / f"pred_{img_path.stem}.png"
        count, result = run_inference(model, img_path, output_path)
        provider = img_path.parent.name

        if count > 0:
            # Salvar apenas imagens com detecções
            total_detections += count
            images_with_detections += 1

            for box in result.boxes:
                cls_name = CATEGORY_NAMES.get(int(box.cls[0]), "unknown")
                detection_summary[cls_name] = detection_summary.get(cls_name, 0) + 1

            print(f"  [{provider}] {img_path.name}: {count} componentes -> {output_path.name}")
        else:
            # Remover imagem sem detecção
            output_path.unlink(missing_ok=True)

    # Resumo de detecções
    print(f"\n{'=' * 60}")
    print("Resumo de Detecções Reais")
    print(f"{'=' * 60}")
    print(f"\nTotal: {total_detections} detecções em {images_with_detections}/{len(all_images)} imagens")

    if detection_summary:
        print(f"\nPor classe:")
        for cls_name, count in sorted(detection_summary.items(), key=lambda x: -x[1]):
            bar = "#" * count
            print(f"  {cls_name:12s}: {count:3d} {bar}")
    else:
        print("\nNenhuma detecção com conf >= 0.25")
        print("Isso é esperado com dataset pequeno (66 imgs). O modelo contribui")
        print("no pipeline híbrido onde Claude Vision complementa as detecções.")

    # Métricas do treinamento
    metrics = load_metrics()
    if metrics:
        print(f"\n{'=' * 60}")
        print("Métricas do Treinamento")
        print(f"{'=' * 60}")

        m = metrics["metrics"]["overall"]
        print(f"\n  Precision:  {m['precision']:.3f}")
        print(f"  Recall:     {m['recall']:.4f}")
        print(f"  mAP@50:     {m['mAP50']:.4f}")
        print(f"  mAP@50-95:  {m['mAP50_95']:.5f}")

        print(f"\nRedução de Loss:")
        l1 = metrics["loss_progression"]["epoch_1"]
        l2 = metrics["loss_progression"]["epoch_30_best"]
        print(f"  box_loss:  {l1['box_loss']:.3f} -> {l2['box_loss']:.3f} ({(1 - l2['box_loss'] / l1['box_loss']) * 100:.1f}% redução)")
        print(f"  cls_loss:  {l1['cls_loss']:.3f} -> {l2['cls_loss']:.3f} ({(1 - l2['cls_loss'] / l1['cls_loss']) * 100:.1f}% redução)")

    print(f"\nPredições salvas em: {output_dir}")


if __name__ == "__main__":
    main()
