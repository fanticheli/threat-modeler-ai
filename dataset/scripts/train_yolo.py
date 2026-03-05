#!/usr/bin/env python3
"""
Script de treinamento do modelo YOLO v8 para detecção de componentes de arquitetura.

v4: YOLOv8s (small), hiperparâmetros otimizados, auto-detect GPU,
    usa imagens pré-processadas e dados augmentados para balanceamento.

Pré-requisitos:
    pip install ultralytics

Uso:
    python train_yolo.py [--epochs 150] [--batch 16] [--device auto]
"""

import argparse
from pathlib import Path
import shutil


def detect_device(requested: str) -> str:
    """Auto-detecta GPU disponível."""
    if requested != "auto":
        return requested

    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"GPU detectada: {gpu_name}")
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            print("Apple MPS detectado")
            return "mps"
    except ImportError:
        pass

    print("Nenhuma GPU detectada, usando CPU")
    return "cpu"


def setup_yolo_structure():
    """Reorganiza o dataset para o formato esperado pelo YOLO."""
    base_dir = Path(__file__).parent.parent
    yolo_dir = base_dir / "yolo_dataset"

    # Criar estrutura YOLO
    for split in ["train", "val", "test"]:
        (yolo_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (yolo_dir / split / "labels").mkdir(parents=True, exist_ok=True)

    # Preferir imagens pré-processadas se existirem
    images_processed = base_dir / "images_processed"
    images_dir = images_processed if images_processed.exists() else base_dir / "images"
    splits_dir = base_dir / "splits"
    annotations_dir = base_dir / "annotations"

    if images_processed.exists():
        print(f"Usando imagens pré-processadas de: {images_processed}")
    else:
        print(f"Usando imagens originais de: {images_dir}")

    copied = 0
    for split in ["train", "val", "test"]:
        split_file = splits_dir / f"{split}.txt"
        if not split_file.exists():
            continue

        with open(split_file) as f:
            image_paths = [line.strip() for line in f if line.strip()]

        for img_rel_path in image_paths:
            # Tentar imagem pré-processada primeiro
            img_path = base_dir / img_rel_path
            if images_processed.exists():
                processed_path = images_processed / Path(img_rel_path).relative_to("images")
                if processed_path.exists():
                    img_path = processed_path

            if not img_path.exists():
                print(f"Warning: {img_path} not found")
                continue

            # Copiar imagem
            dest_img = yolo_dir / split / "images" / img_path.name
            shutil.copy2(img_path, dest_img)
            copied += 1

            # Copiar label (mesmo nome, extensão .txt)
            label_name = img_path.stem + ".txt"
            label_path = annotations_dir / label_name
            if label_path.exists():
                dest_label = yolo_dir / split / "labels" / label_name
                shutil.copy2(label_path, dest_label)

    print(f"Dataset prepared at: {yolo_dir} ({copied} imagens copiadas)")

    # Contar imagens augmentadas já presentes no train
    aug_images = list((yolo_dir / "train" / "images").glob("*_aug_*"))
    if aug_images:
        print(f"Imagens augmentadas encontradas no train: {len(aug_images)}")

    return yolo_dir


def create_data_yaml(yolo_dir: Path):
    """Cria o arquivo data.yaml para o YOLO."""
    yaml_content = f"""# Architecture Components Detection Dataset (10 consolidated classes)
path: {yolo_dir.absolute()}
train: train/images
val: val/images
test: test/images

# Classes (consolidated from 30 to 10 for better per-class sample density)
names:
  0: server
  1: database
  2: network
  3: storage
  4: security
  5: serverless
  6: queue
  7: monitoring
  8: user
  9: external

nc: 10
"""

    yaml_path = yolo_dir / "data.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    print(f"Created: {yaml_path}")
    return yaml_path


def train(data_yaml: Path, epochs: int = 150, batch: int = 16, device: str = "cpu"):
    """Treina o modelo YOLO v8s com hiperparâmetros otimizados."""
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Error: ultralytics not installed. Run: pip install ultralytics")
        return None

    # YOLOv8 Small — 2.5x mais parâmetros que nano
    model = YOLO("yolov8s.pt")

    print("\n" + "=" * 50)
    print("Starting YOLO Training (v5)")
    print("=" * 50)
    print(f"  Model: YOLOv8s (small)")
    print(f"  Data: {data_yaml}")
    print(f"  Epochs: {epochs}")
    print(f"  Batch size: {batch}")
    print(f"  Device: {device}")
    print("=" * 50 + "\n")

    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        batch=batch,
        imgsz=640,
        device=device,
        patience=50,       # Mais paciência para convergir (era 30)
        save=True,
        plots=True,

        # === Loss weights (rebalanceados) ===
        # cls aumentado de 0.5→1.5 para forçar aprendizado de classificação
        # (recall era ~0% no v3 por falta de ênfase em cls)
        box=5.0,            # Era 7.5 — reduzido para equilibrar com cls
        cls=1.5,            # Era 0.5 — TRIPLICADO para melhorar recall
        dfl=1.5,            # Mantido

        # === Augmentation (tuned for architecture diagrams) ===
        hsv_h=0.015,        # Hue mínima (cores importam em diagramas)
        hsv_s=0.3,
        hsv_v=0.3,
        degrees=5,
        translate=0.1,
        scale=0.3,
        flipud=0.0,         # Sem flip (diagramas têm orientação)
        fliplr=0.0,
        mixup=0.2,
        copy_paste=0.3,
        close_mosaic=10,    # Era 20 — desligar mosaic mais cedo para fine-tuning

        # === Otimização (mais agressiva) ===
        optimizer="AdamW",
        lr0=0.01,           # Era 0.001 — LR inicial mais alta
        lrf=0.01,           # Fator final de LR
        cos_lr=True,        # Era False — cosine annealing para decaimento suave
        warmup_epochs=5,    # Era 3 — warmup mais longo com dataset pequeno
        warmup_momentum=0.8,
        weight_decay=0.0005,

        # Nome do projeto
        project="runs/train",
        name="architecture_detector_v5",
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
    parser = argparse.ArgumentParser(description="Train YOLO for architecture detection (v4)")
    parser.add_argument("--epochs", type=int, default=150, help="Number of epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size (16 GPU, 8 CPU)")
    parser.add_argument("--device", type=str, default="auto", help="Device (auto/cpu/cuda/mps)")
    parser.add_argument("--eval-only", action="store_true", help="Only evaluate existing model")
    parser.add_argument("--export", type=str, help="Export model to format (onnx/torchscript)")
    args = parser.parse_args()

    # Auto-detect device
    device = detect_device(args.device)

    # Ajustar batch para CPU se necessário
    batch = args.batch
    if device == "cpu" and batch > 8:
        print(f"CPU detectada: reduzindo batch de {batch} para 8")
        batch = 8

    # Setup
    print("Setting up dataset structure...")
    yolo_dir = setup_yolo_structure()
    data_yaml = create_data_yaml(yolo_dir)

    # Check for existing model
    best_model = Path("runs/train/architecture_detector_v5/weights/best.pt")

    if args.eval_only and best_model.exists():
        evaluate(best_model, data_yaml)
    elif args.export and best_model.exists():
        export_model(best_model, args.export)
    else:
        # Train
        train(data_yaml, epochs=args.epochs, batch=batch, device=device)

        # Evaluate
        if best_model.exists():
            evaluate(best_model, data_yaml)


if __name__ == "__main__":
    main()
