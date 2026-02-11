#!/usr/bin/env python3
"""
Cria splits train/val/test para o dataset YOLO.
Divisão: 70% train, 20% val, 10% test.
Garante que as imagens são diferentes em cada split.
"""

import random
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "images"
ANNOTATIONS_DIR = BASE_DIR / "annotations"
SPLITS_DIR = BASE_DIR / "splits"
SPLITS_DIR.mkdir(exist_ok=True)

# Seed para reprodutibilidade
random.seed(42)


def find_annotated_images():
    """Encontra imagens que possuem anotação YOLO (.txt)."""
    annotated = []
    extensions = [".png", ".jpg", ".jpeg"]

    for ext in extensions:
        for img_path in IMAGES_DIR.rglob(f"*{ext}"):
            if "_svg_temp" in str(img_path):
                continue
            # Verificar se tem anotação correspondente
            annotation_path = ANNOTATIONS_DIR / f"{img_path.stem}.txt"
            if annotation_path.exists():
                # Caminho relativo a partir do diretório base do dataset
                rel_path = img_path.relative_to(BASE_DIR)
                annotated.append(str(rel_path))

    return sorted(set(annotated))


def create_splits():
    """Cria splits train/val/test."""
    images = find_annotated_images()
    print(f"Total de imagens anotadas: {len(images)}")

    # Shuffle
    random.shuffle(images)

    # Calcular tamanhos
    total = len(images)
    train_size = int(total * 0.70)
    val_size = int(total * 0.20)
    # test fica com o resto

    train = images[:train_size]
    val = images[train_size:train_size + val_size]
    test = images[train_size + val_size:]

    print(f"\nDistribuição:")
    print(f"  Train: {len(train)} imagens ({len(train)/total*100:.0f}%)")
    print(f"  Val:   {len(val)} imagens ({len(val)/total*100:.0f}%)")
    print(f"  Test:  {len(test)} imagens ({len(test)/total*100:.0f}%)")

    # Salvar splits
    for name, split in [("train", train), ("val", val), ("test", test)]:
        split_file = SPLITS_DIR / f"{name}.txt"
        with open(split_file, "w") as f:
            f.write("\n".join(split))
        print(f"  Saved: {split_file.name}")

    return train, val, test


if __name__ == "__main__":
    print("=" * 50)
    print("Creating Dataset Splits")
    print("=" * 50)
    create_splits()
    print("\nDone!")
