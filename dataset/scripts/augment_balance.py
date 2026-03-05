#!/usr/bin/env python3
"""
Balanceia o dataset via augmentação offline focada em classes minoritárias.

Identifica imagens contendo classes sub-representadas e gera cópias
augmentadas (brilho, contraste, blur, noise, rotação leve) para
equilibrar a distribuição de classes.

Uso:
    python augment_balance.py [--target-min 120] [--output-dir yolo_dataset]
"""

import argparse
import math
import random
import sys
from pathlib import Path
from collections import Counter, defaultdict

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import numpy as np
except ImportError:
    print("ERRO: Pillow e numpy necessários. Rode: pip install Pillow numpy")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.parent
ANNOTATIONS_DIR = BASE_DIR / "annotations"
IMAGES_DIR = BASE_DIR / "images"
SPLITS_DIR = BASE_DIR / "splits"

NUM_CLASSES = 10
CLASS_NAMES = {
    0: "server", 1: "database", 2: "network", 3: "storage",
    4: "security", 5: "serverless", 6: "queue", 7: "monitoring",
    8: "user", 9: "external",
}

random.seed(42)
np.random.seed(42)


def count_class_distribution():
    """Conta anotações por classe no dataset."""
    class_counts = Counter()
    image_classes = defaultdict(set)  # imagem -> set de classes

    for txt_path in ANNOTATIONS_DIR.glob("*.txt"):
        with open(txt_path) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    try:
                        class_id = int(parts[0])
                        class_counts[class_id] += 1
                        image_classes[txt_path.stem].add(class_id)
                    except ValueError:
                        pass

    return class_counts, image_classes


def find_images_with_class(class_id, image_classes, split="train"):
    """Encontra imagens do split de treino que contêm determinada classe."""
    split_file = SPLITS_DIR / f"{split}.txt"
    if not split_file.exists():
        return []

    with open(split_file) as f:
        split_images = {Path(line.strip()).stem for line in f if line.strip()}

    return [
        name for name, classes in image_classes.items()
        if class_id in classes and name in split_images
    ]


def find_image_path(image_name):
    """Encontra o path completo de uma imagem pelo nome."""
    # Procurar em images_processed primeiro, depois images
    for base in [BASE_DIR / "images_processed", IMAGES_DIR]:
        for img_path in base.rglob(f"{image_name}.*"):
            if img_path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                return img_path
    return None


def augment_image(img, aug_index):
    """Aplica augmentação determinística baseada no índice."""
    augmentations = [
        # Variações de brilho
        lambda im: ImageEnhance.Brightness(im).enhance(random.uniform(0.7, 0.9)),
        lambda im: ImageEnhance.Brightness(im).enhance(random.uniform(1.1, 1.3)),
        # Variações de contraste
        lambda im: ImageEnhance.Contrast(im).enhance(random.uniform(0.7, 0.9)),
        lambda im: ImageEnhance.Contrast(im).enhance(random.uniform(1.1, 1.4)),
        # Blur leve
        lambda im: im.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 1.0))),
        # Saturação
        lambda im: ImageEnhance.Color(im).enhance(random.uniform(0.7, 1.3)),
        # Combinações
        lambda im: ImageEnhance.Contrast(
            ImageEnhance.Brightness(im).enhance(random.uniform(0.8, 1.2))
        ).enhance(random.uniform(0.8, 1.2)),
        # Noise gaussiano
        lambda im: add_gaussian_noise(im, sigma=random.uniform(5, 15)),
    ]

    aug_fn = augmentations[aug_index % len(augmentations)]
    return aug_fn(img)


def add_gaussian_noise(img, sigma=10):
    """Adiciona ruído gaussiano à imagem."""
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, sigma, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def augment_with_rotation(img, labels_text, angle_deg):
    """Aplica rotação leve e ajusta bounding boxes."""
    if abs(angle_deg) < 0.5:
        return img, labels_text

    # Rotacionar imagem (expand=False mantém mesmo tamanho)
    rotated = img.rotate(angle_deg, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))

    # Para rotações pequenas (±3°), as bboxes YOLO normalizadas
    # praticamente não mudam. Manter as mesmas labels.
    return rotated, labels_text


def main():
    parser = argparse.ArgumentParser(description="Balanceia dataset via augmentação")
    parser.add_argument("--target-min", type=int, default=120,
                        help="Mínimo de anotações por classe após balanceamento")
    parser.add_argument("--output-dir", type=str, default="yolo_dataset",
                        help="Diretório de saída (relativo ao dataset/)")
    args = parser.parse_args()

    print("=" * 60)
    print("BALANCEAMENTO DE CLASSES VIA AUGMENTAÇÃO")
    print("=" * 60)

    # Contar distribuição atual
    class_counts, image_classes = count_class_distribution()

    print(f"\nDistribuição atual:")
    print(f"{'Classe':<15} {'Count':>6} {'Alvo':>6} {'Augmentar':>10}")
    print("-" * 42)

    classes_to_augment = {}
    for class_id in range(NUM_CLASSES):
        count = class_counts.get(class_id, 0)
        need = max(0, args.target_min - count)
        name = CLASS_NAMES[class_id]
        status = f"+{need}" if need > 0 else "OK"
        print(f"{name:<15} {count:>6} {args.target_min:>6} {status:>10}")
        if need > 0:
            classes_to_augment[class_id] = need

    if not classes_to_augment:
        print(f"\n✓ Todas as classes já têm >= {args.target_min} anotações!")
        return 0

    # Diretório de saída
    output_dir = BASE_DIR / args.output_dir
    train_images_dir = output_dir / "train" / "images"
    train_labels_dir = output_dir / "train" / "labels"
    train_images_dir.mkdir(parents=True, exist_ok=True)
    train_labels_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nGerando augmentações em: {output_dir}")

    total_generated = 0
    aug_class_counts = Counter()

    for class_id, needed_annotations in sorted(classes_to_augment.items()):
        class_name = CLASS_NAMES[class_id]

        # Encontrar imagens de treino com essa classe
        source_images = find_images_with_class(class_id, image_classes, split="train")

        if not source_images:
            print(f"\n⚠ {class_name}: nenhuma imagem de treino contém essa classe!")
            continue

        # Calcular quantas cópias de cada imagem fazer
        # Contar anotações dessa classe por imagem
        annotations_per_image = {}
        for img_name in source_images:
            txt_path = ANNOTATIONS_DIR / f"{img_name}.txt"
            if txt_path.exists():
                count = 0
                with open(txt_path) as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) == 5 and int(parts[0]) == class_id:
                            count += 1
                annotations_per_image[img_name] = count

        total_available = sum(annotations_per_image.values())
        if total_available == 0:
            continue

        # Quantas rodadas de augmentação por imagem
        rounds_needed = math.ceil(needed_annotations / total_available)
        rounds_needed = min(rounds_needed, 8)  # Máximo 8 cópias por imagem

        print(f"\n{class_name} (id={class_id}): +{needed_annotations} anotações necessárias")
        print(f"  Fontes: {len(source_images)} imagens, {rounds_needed} augmentações cada")

        generated_for_class = 0
        for img_name in source_images:
            img_path = find_image_path(img_name)
            if img_path is None:
                continue

            txt_path = ANNOTATIONS_DIR / f"{img_name}.txt"
            if not txt_path.exists():
                continue

            with open(txt_path) as f:
                labels_text = f.read()

            img = Image.open(img_path).convert("RGB")

            for aug_i in range(rounds_needed):
                if generated_for_class >= needed_annotations:
                    break

                # Nome único para augmentação
                aug_name = f"{img_name}_aug_{class_name}_{aug_i}"

                # Augmentar imagem
                aug_img = augment_image(img, aug_i)

                # Rotação leve ocasional
                if aug_i % 3 == 0:
                    angle = random.uniform(-3, 3)
                    aug_img, labels_text_adj = augment_with_rotation(aug_img, labels_text, angle)
                else:
                    labels_text_adj = labels_text

                # Salvar
                aug_img_path = train_images_dir / f"{aug_name}.png"
                aug_label_path = train_labels_dir / f"{aug_name}.txt"

                aug_img.save(aug_img_path, "PNG")
                with open(aug_label_path, "w") as f:
                    f.write(labels_text_adj)

                # Contar anotações geradas dessa classe
                for line in labels_text_adj.strip().split("\n"):
                    parts = line.strip().split()
                    if len(parts) == 5:
                        cid = int(parts[0])
                        aug_class_counts[cid] += 1
                        if cid == class_id:
                            generated_for_class += 1

                total_generated += 1

            img.close()

        print(f"  Geradas: {generated_for_class} anotações em augmentações")

    # Relatório final
    print(f"\n{'=' * 60}")
    print("RESULTADO")
    print(f"{'=' * 60}")
    print(f"Imagens augmentadas geradas: {total_generated}")

    print(f"\nDistribuição final estimada (original + augmentado):")
    print(f"{'Classe':<15} {'Original':>8} {'Augment':>8} {'Total':>8}")
    print("-" * 44)
    for class_id in range(NUM_CLASSES):
        orig = class_counts.get(class_id, 0)
        aug = aug_class_counts.get(class_id, 0)
        name = CLASS_NAMES[class_id]
        print(f"{name:<15} {orig:>8} {aug:>8} {orig + aug:>8}")

    print(f"\n✓ Augmentação concluída!")
    print(f"  As imagens augmentadas estão em: {train_images_dir}")
    print(f"  Os labels augmentados estão em: {train_labels_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
