#!/usr/bin/env python3
"""
Valida e corrige anotações YOLO do dataset.

Verifica:
- Coordenadas dentro de [0, 1]
- class_id entre 0-9
- Bboxes suspeitas (muito grandes ou muito pequenas)
- Imagens sem annotation correspondente
- Arquivos de annotation vazios

Uso:
    python validate_annotations.py [--fix]
"""

import argparse
import sys
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).parent.parent
ANNOTATIONS_DIR = BASE_DIR / "annotations"
IMAGES_DIR = BASE_DIR / "images"

NUM_CLASSES = 10
MIN_BBOX_AREA = 0.0001  # 0.01% da imagem
MAX_BBOX_AREA = 0.80    # 80% da imagem
MIN_BBOX_DIM = 0.005    # 0.5% do lado


def find_all_images():
    """Encontra todas as imagens no dataset."""
    extensions = {".png", ".jpg", ".jpeg"}
    images = {}
    for img_path in IMAGES_DIR.rglob("*"):
        if img_path.suffix.lower() in extensions:
            images[img_path.stem] = img_path
    return images


def validate_annotation_file(txt_path, fix=False):
    """Valida um arquivo de anotação YOLO."""
    issues = []
    fixed_lines = []
    removed = 0

    with open(txt_path) as f:
        lines = f.readlines()

    if not lines:
        issues.append(f"  VAZIO: {txt_path.name}")
        return issues, 0, 0

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) != 5:
            issues.append(f"  FORMATO: {txt_path.name}:{i+1} — {len(parts)} campos (esperado 5)")
            removed += 1
            continue

        try:
            class_id = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])
        except ValueError:
            issues.append(f"  PARSE: {txt_path.name}:{i+1} — valores não numéricos")
            removed += 1
            continue

        line_issues = []

        # Validar class_id
        if class_id < 0 or class_id >= NUM_CLASSES:
            line_issues.append(f"class_id={class_id} fora de [0,{NUM_CLASSES-1}]")
            removed += 1
            continue

        # Validar coordenadas
        needs_clamp = False
        for name, val in [("x_center", x_center), ("y_center", y_center),
                          ("width", width), ("height", height)]:
            if val < 0 or val > 1:
                line_issues.append(f"{name}={val:.6f} fora de [0,1]")
                needs_clamp = True

        # Clamp se fix
        if needs_clamp and fix:
            x_center = max(0.0, min(1.0, x_center))
            y_center = max(0.0, min(1.0, y_center))
            width = max(0.0, min(1.0, width))
            height = max(0.0, min(1.0, height))

        # Validar dimensões
        if width < MIN_BBOX_DIM or height < MIN_BBOX_DIM:
            line_issues.append(f"bbox muito pequena: {width:.4f}x{height:.4f}")
            if fix:
                removed += 1
                continue

        area = width * height
        if area > MAX_BBOX_AREA:
            line_issues.append(f"bbox muito grande: area={area:.4f} ({area*100:.1f}%)")

        if area < MIN_BBOX_AREA:
            line_issues.append(f"bbox minúscula: area={area:.6f}")
            if fix:
                removed += 1
                continue

        # Verificar se bbox não sai da imagem
        x1 = x_center - width / 2
        y1 = y_center - height / 2
        x2 = x_center + width / 2
        y2 = y_center + height / 2

        if x1 < -0.01 or y1 < -0.01 or x2 > 1.01 or y2 > 1.01:
            line_issues.append(f"bbox parcialmente fora da imagem: [{x1:.3f},{y1:.3f},{x2:.3f},{y2:.3f}]")
            if fix:
                # Ajustar para caber na imagem
                x1 = max(0.0, x1)
                y1 = max(0.0, y1)
                x2 = min(1.0, x2)
                y2 = min(1.0, y2)
                x_center = (x1 + x2) / 2
                y_center = (y1 + y2) / 2
                width = x2 - x1
                height = y2 - y1

        if line_issues:
            for issue in line_issues:
                issues.append(f"  {txt_path.name}:{i+1} — {issue}")

        fixed_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    total_original = len([l for l in lines if l.strip()])

    # Salvar correções
    if fix and (removed > 0 or any("clamp" in i or "fora" in i for i in issues)):
        with open(txt_path, "w") as f:
            f.write("\n".join(fixed_lines) + "\n" if fixed_lines else "")
        if removed > 0:
            issues.append(f"  CORRIGIDO: removidas {removed} anotações inválidas de {txt_path.name}")

    return issues, total_original, removed


def main():
    parser = argparse.ArgumentParser(description="Valida anotações YOLO")
    parser.add_argument("--fix", action="store_true", help="Corrigir problemas automaticamente")
    args = parser.parse_args()

    print("=" * 60)
    print("VALIDAÇÃO DE ANOTAÇÕES YOLO")
    print("=" * 60)

    # Encontrar imagens e annotations
    images = find_all_images()
    annotations = {p.stem: p for p in ANNOTATIONS_DIR.glob("*.txt")}

    print(f"\nImagens encontradas: {len(images)}")
    print(f"Annotations encontradas: {len(annotations)}")

    # 1. Imagens sem annotation
    missing_annotations = set(images.keys()) - set(annotations.keys())
    if missing_annotations:
        print(f"\n⚠ {len(missing_annotations)} imagens SEM annotation:")
        for name in sorted(missing_annotations):
            print(f"  - {name}")

    # 2. Annotations sem imagem
    orphan_annotations = set(annotations.keys()) - set(images.keys())
    if orphan_annotations:
        print(f"\n⚠ {len(orphan_annotations)} annotations SEM imagem:")
        for name in sorted(orphan_annotations):
            print(f"  - {name}")

    # 3. Validar cada annotation
    print(f"\nValidando {len(annotations)} arquivos de anotação...")
    if args.fix:
        print("(modo --fix ativo: corrigindo problemas)")

    all_issues = []
    total_annotations = 0
    total_removed = 0
    class_counts = Counter()

    for name, txt_path in sorted(annotations.items()):
        issues, count, removed = validate_annotation_file(txt_path, fix=args.fix)
        all_issues.extend(issues)
        total_annotations += count
        total_removed += removed

        # Contar classes
        with open(txt_path) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    try:
                        class_counts[int(parts[0])] += 1
                    except ValueError:
                        pass

    # Relatório
    print(f"\n{'=' * 60}")
    print("RELATÓRIO")
    print(f"{'=' * 60}")
    print(f"Total de anotações: {total_annotations}")
    print(f"Problemas encontrados: {len(all_issues)}")
    if args.fix:
        print(f"Anotações removidas: {total_removed}")

    if all_issues:
        print(f"\nDetalhes dos problemas:")
        for issue in all_issues:
            print(issue)

    # Distribuição de classes
    CLASS_NAMES = {
        0: "server", 1: "database", 2: "network", 3: "storage",
        4: "security", 5: "serverless", 6: "queue", 7: "monitoring",
        8: "user", 9: "external",
    }

    print(f"\nDistribuição de classes (após validação):")
    print(f"{'Classe':<15} {'ID':>3} {'Count':>6} {'%':>7}")
    print("-" * 35)
    total = sum(class_counts.values())
    for class_id in range(NUM_CLASSES):
        count = class_counts.get(class_id, 0)
        pct = (count / total * 100) if total > 0 else 0
        name = CLASS_NAMES.get(class_id, f"class_{class_id}")
        print(f"{name:<15} {class_id:>3} {count:>6} {pct:>6.1f}%")
    print("-" * 35)
    print(f"{'TOTAL':<15} {'':>3} {total:>6}")

    if not all_issues and not missing_annotations:
        print("\n✓ Todas as anotações estão válidas!")
    elif args.fix:
        print("\n✓ Correções aplicadas!")
    else:
        print(f"\nExecute com --fix para corrigir automaticamente.")

    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
