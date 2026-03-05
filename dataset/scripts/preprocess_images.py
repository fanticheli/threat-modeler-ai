#!/usr/bin/env python3
"""
Pré-processa imagens do dataset para padronizar resolução e qualidade.

- Redimensiona para max 1280px no maior lado (mantendo aspect ratio)
- Converte para RGB (remove alpha channel)
- Aplica CLAHE para normalizar contraste
- Salva em images_processed/ mantendo estrutura de subpastas

Uso:
    python preprocess_images.py [--max-size 1280] [--skip-clahe]
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError:
    print("ERRO: Pillow não instalado. Rode: pip install Pillow")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "images"
OUTPUT_DIR = BASE_DIR / "images_processed"
ANNOTATIONS_DIR = BASE_DIR / "annotations"
SPLITS_DIR = BASE_DIR / "splits"


def process_image(img_path, output_path, max_size=1280, apply_clahe=True):
    """Processa uma imagem: resize, RGB, contraste."""
    img = Image.open(img_path)

    # Converter para RGB (remover alpha)
    if img.mode != "RGB":
        if img.mode == "RGBA":
            # Criar fundo branco para imagens com transparência
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        else:
            img = img.convert("RGB")

    # Redimensionar mantendo aspect ratio
    w, h = img.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)

    # Melhorar contraste (leve)
    if apply_clahe:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)  # Aumento leve de 20%

        # Leve sharpening para diagramas
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)

    return img.size


def update_splits(old_base, new_base):
    """Atualiza arquivos de split para apontar para imagens processadas."""
    for split_name in ["train", "val", "test"]:
        split_file = SPLITS_DIR / f"{split_name}.txt"
        if not split_file.exists():
            continue

        with open(split_file) as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Trocar images/ por images_processed/
            new_line = line.replace("images/", "images_processed/")
            new_lines.append(new_line)

        output_file = SPLITS_DIR / f"{split_name}_processed.txt"
        with open(output_file, "w") as f:
            f.write("\n".join(new_lines) + "\n")

        print(f"Split atualizado: {output_file.name}")


def main():
    parser = argparse.ArgumentParser(description="Pré-processa imagens do dataset")
    parser.add_argument("--max-size", type=int, default=1280, help="Tamanho máximo do maior lado")
    parser.add_argument("--skip-clahe", action="store_true", help="Pular melhoria de contraste")
    args = parser.parse_args()

    print("=" * 60)
    print("PRÉ-PROCESSAMENTO DE IMAGENS")
    print("=" * 60)
    print(f"Input: {IMAGES_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Max size: {args.max_size}px")
    print(f"Contraste: {'desativado' if args.skip_clahe else 'ativado'}")

    # Encontrar imagens
    extensions = {".png", ".jpg", ".jpeg"}
    images = [p for p in IMAGES_DIR.rglob("*") if p.suffix.lower() in extensions]

    if not images:
        print("Nenhuma imagem encontrada!")
        return 1

    print(f"\nProcessando {len(images)} imagens...\n")

    resized = 0
    converted = 0

    for img_path in sorted(images):
        rel_path = img_path.relative_to(IMAGES_DIR)
        output_path = OUTPUT_DIR / rel_path

        original = Image.open(img_path)
        orig_size = original.size
        orig_mode = original.mode
        original.close()

        new_size = process_image(
            img_path, output_path,
            max_size=args.max_size,
            apply_clahe=not args.skip_clahe,
        )

        status = []
        if orig_size != new_size:
            status.append(f"resize {orig_size[0]}x{orig_size[1]} -> {new_size[0]}x{new_size[1]}")
            resized += 1
        if orig_mode != "RGB":
            status.append(f"{orig_mode} -> RGB")
            converted += 1

        status_str = f" ({', '.join(status)})" if status else ""
        print(f"  ✓ {rel_path}{status_str}")

    # Atualizar splits
    print(f"\nAtualizando splits...")
    update_splits(IMAGES_DIR, OUTPUT_DIR)

    print(f"\n{'=' * 60}")
    print("RESULTADO")
    print(f"{'=' * 60}")
    print(f"Imagens processadas: {len(images)}")
    print(f"Redimensionadas: {resized}")
    print(f"Convertidas para RGB: {converted}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"\n✓ Pré-processamento concluído!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
