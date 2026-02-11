#!/usr/bin/env python3
"""
Script de treinamento do modelo YOLO v8 para detecção de componentes de arquitetura.

Pré-requisitos:
    pip install ultralytics

Uso:
    python train_yolo.py [--epochs 100] [--batch 16] [--device cuda]
"""

import argparse
from pathlib import Path
import shutil
import os

def setup_yolo_structure():
    """Reorganiza o dataset para o formato esperado pelo YOLO."""
    base_dir = Path(__file__).parent.parent
    yolo_dir = base_dir / "yolo_dataset"

    # Criar estrutura YOLO
    for split in ["train", "val", "test"]:
        (yolo_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (yolo_dir / split / "labels").mkdir(parents=True, exist_ok=True)

    # Copiar imagens e labels para cada split
    splits_dir = base_dir / "splits"
    images_dir = base_dir / "images"
    annotations_dir = base_dir / "annotations"

    for split in ["train", "val", "test"]:
        split_file = splits_dir / f"{split}.txt"
        if not split_file.exists():
            continue

        with open(split_file) as f:
            image_paths = [line.strip() for line in f if line.strip()]

        for img_rel_path in image_paths:
            img_path = base_dir / img_rel_path
            if not img_path.exists():
                print(f"Warning: {img_path} not found")
                continue

            # Copiar imagem
            dest_img = yolo_dir / split / "images" / img_path.name
            if not dest_img.exists():
                shutil.copy2(img_path, dest_img)

            # Copiar label (mesmo nome, extensão .txt)
            label_name = img_path.stem + ".txt"
            label_path = annotations_dir / label_name
            if label_path.exists():
                dest_label = yolo_dir / split / "labels" / label_name
                if not dest_label.exists():
                    shutil.copy2(label_path, dest_label)

    print(f"Dataset prepared at: {yolo_dir}")
    return yolo_dir


def create_data_yaml(yolo_dir: Path):
    """Cria o arquivo data.yaml para o YOLO."""
    yaml_content = f"""# Architecture Components Detection Dataset
path: {yolo_dir.absolute()}
train: train/images
val: val/images
test: test/images

# Classes
names:
  0: user
  1: web_browser
  2: mobile_app
  3: api_gateway
  4: load_balancer
  5: web_server
  6: app_server
  7: microservice
  8: container
  9: kubernetes
  10: lambda_function
  11: database_sql
  12: database_nosql
  13: cache
  14: queue
  15: storage_object
  16: storage_block
  17: cdn
  18: firewall
  19: waf
  20: vpc
  21: subnet
  22: iam
  23: kms
  24: secrets_manager
  25: monitoring
  26: logging
  27: external_service
  28: dns
  29: email_service

nc: 30
"""

    yaml_path = yolo_dir / "data.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    print(f"Created: {yaml_path}")
    return yaml_path


def train(data_yaml: Path, epochs: int = 100, batch: int = 16, device: str = "cpu"):
    """Treina o modelo YOLO v8."""
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Error: ultralytics not installed. Run: pip install ultralytics")
        return None

    # Usar modelo pré-treinado como base
    model = YOLO("yolov8n.pt")  # nano model (mais rápido para teste)

    print("\n" + "=" * 50)
    print("Starting YOLO Training")
    print("=" * 50)
    print(f"  Data: {data_yaml}")
    print(f"  Epochs: {epochs}")
    print(f"  Batch size: {batch}")
    print(f"  Device: {device}")
    print("=" * 50 + "\n")

    # Treinar
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        batch=batch,
        imgsz=640,
        device=device,
        patience=20,  # Early stopping
        save=True,
        plots=True,

        # Augmentation (reduzido para diagramas)
        hsv_h=0.015,
        hsv_s=0.3,
        hsv_v=0.3,
        degrees=5,
        translate=0.1,
        scale=0.3,
        flipud=0.0,  # Não flipar (diagramas têm orientação)
        fliplr=0.0,

        # Otimização
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        weight_decay=0.0005,

        # Nome do projeto
        project="runs/train",
        name="architecture_detector",
    )

    print("\n" + "=" * 50)
    print("Training Complete!")
    print("=" * 50)

    return results


def evaluate(model_path: Path, data_yaml: Path):
    """Avalia o modelo treinado."""
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Error: ultralytics not installed")
        return

    model = YOLO(str(model_path))
    results = model.val(data=str(data_yaml))

    print("\nEvaluation Results:")
    print(f"  mAP50: {results.box.map50:.4f}")
    print(f"  mAP50-95: {results.box.map:.4f}")
    print(f"  Precision: {results.box.mp:.4f}")
    print(f"  Recall: {results.box.mr:.4f}")


def export_model(model_path: Path, format: str = "onnx"):
    """Exporta o modelo para produção."""
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Error: ultralytics not installed")
        return

    model = YOLO(str(model_path))
    model.export(format=format)
    print(f"Model exported to {format} format")


def main():
    parser = argparse.ArgumentParser(description="Train YOLO for architecture detection")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--batch", type=int, default=8, help="Batch size")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu/cuda/mps)")
    parser.add_argument("--eval-only", action="store_true", help="Only evaluate existing model")
    parser.add_argument("--export", type=str, help="Export model to format (onnx/torchscript)")
    args = parser.parse_args()

    # Setup
    print("Setting up dataset structure...")
    yolo_dir = setup_yolo_structure()
    data_yaml = create_data_yaml(yolo_dir)

    # Check for existing model
    best_model = Path("runs/train/architecture_detector/weights/best.pt")

    if args.eval_only and best_model.exists():
        evaluate(best_model, data_yaml)
    elif args.export and best_model.exists():
        export_model(best_model, args.export)
    else:
        # Train
        train(data_yaml, epochs=args.epochs, batch=args.batch, device=args.device)

        # Evaluate
        if best_model.exists():
            evaluate(best_model, data_yaml)


if __name__ == "__main__":
    main()
