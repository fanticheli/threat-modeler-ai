#!/usr/bin/env python3
"""
Corrige anotações YOLO com coordenadas fora do range [0, 1].
- Clamp valores para [0, 1]
- Remove anotações com centro muito fora da imagem (>0.95 após clamp)
- Ajusta bounding boxes que ultrapassam bordas
"""

from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ANNOTATIONS_DIR = BASE_DIR / "annotations"


def fix_annotation_file(filepath: Path) -> dict:
    """Corrige um arquivo de anotação YOLO."""
    stats = {"total": 0, "fixed": 0, "removed": 0, "ok": 0}

    lines = filepath.read_text().strip().split("\n")
    fixed_lines = []

    for line in lines:
        if not line.strip():
            continue

        stats["total"] += 1
        parts = line.strip().split()
        if len(parts) != 5:
            stats["removed"] += 1
            continue

        class_id = parts[0]
        x_center = float(parts[1])
        y_center = float(parts[2])
        width = float(parts[3])
        height = float(parts[4])

        # Verificar se o centro está muito fora da imagem
        if x_center > 1.15 or y_center > 1.15 or x_center < -0.15 or y_center < -0.15:
            stats["removed"] += 1
            continue

        # Clamp centro para [0, 1]
        original = (x_center, y_center, width, height)
        x_center = max(0.0, min(1.0, x_center))
        y_center = max(0.0, min(1.0, y_center))

        # Ajustar largura/altura para não ultrapassar bordas
        # x_min = x_center - width/2 >= 0
        # x_max = x_center + width/2 <= 1
        half_w = width / 2
        half_h = height / 2

        if x_center - half_w < 0:
            width = x_center * 2
        if x_center + half_w > 1:
            width = (1 - x_center) * 2
        if y_center - half_h < 0:
            height = y_center * 2
        if y_center + half_h > 1:
            height = (1 - y_center) * 2

        # Mínimo de tamanho
        width = max(0.01, min(1.0, width))
        height = max(0.01, min(1.0, height))

        clamped = (x_center, y_center, width, height)
        if original != clamped:
            stats["fixed"] += 1
        else:
            stats["ok"] += 1

        fixed_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    # Salvar
    filepath.write_text("\n".join(fixed_lines))
    return stats


def main():
    print("=" * 50)
    print("Fixing YOLO Annotations")
    print("=" * 50)

    total_stats = {"total": 0, "fixed": 0, "removed": 0, "ok": 0}
    files_with_issues = 0

    txt_files = sorted(ANNOTATIONS_DIR.glob("*.txt"))
    print(f"\nProcessando {len(txt_files)} arquivos...\n")

    for filepath in txt_files:
        stats = fix_annotation_file(filepath)

        for key in total_stats:
            total_stats[key] += stats[key]

        if stats["fixed"] > 0 or stats["removed"] > 0:
            files_with_issues += 1
            print(f"  {filepath.name}: {stats['fixed']} fixed, {stats['removed']} removed (de {stats['total']})")

    print(f"\n{'=' * 50}")
    print(f"Resumo:")
    print(f"  Anotações totais: {total_stats['total']}")
    print(f"  OK (sem mudança):  {total_stats['ok']}")
    print(f"  Corrigidas:        {total_stats['fixed']}")
    print(f"  Removidas:         {total_stats['removed']}")
    print(f"  Arquivos afetados: {files_with_issues}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
