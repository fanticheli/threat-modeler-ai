#!/usr/bin/env python3
"""
Remapeia as anotações YOLO de 30 classes para 10 classes consolidadas.

Mapeamento:
  0: server     <- microservice(7), app_server(6), web_server(5), container(8), kubernetes(9)
  1: database   <- database_sql(11), database_nosql(12)
  2: network    <- api_gateway(3), load_balancer(4), cdn(17), dns(28), vpc(20), subnet(21)
  3: storage    <- storage_object(15), storage_block(16), cache(13)
  4: security   <- firewall(18), waf(19), iam(22), kms(23), secrets_manager(24)
  5: serverless <- lambda_function(10)
  6: queue      <- queue(14)
  7: monitoring <- monitoring(25), logging(26)
  8: user       <- user(0), web_browser(1), mobile_app(2)
  9: external   <- external_service(27), email_service(29)
"""

from pathlib import Path
from typing import Tuple
from collections import Counter

ANNOTATIONS_DIR = Path(__file__).parent.parent / "annotations"

# old_class_id -> new_class_id
REMAP = {
    # 0: server
    7: 0, 6: 0, 5: 0, 8: 0, 9: 0,
    # 1: database
    11: 1, 12: 1,
    # 2: network
    3: 2, 4: 2, 17: 2, 28: 2, 20: 2, 21: 2,
    # 3: storage
    15: 3, 16: 3, 13: 3,
    # 4: security
    18: 4, 19: 4, 22: 4, 23: 4, 24: 4,
    # 5: serverless
    10: 5,
    # 6: queue
    14: 6,
    # 7: monitoring
    25: 7, 26: 7,
    # 8: user
    0: 8, 1: 8, 2: 8,
    # 9: external
    27: 9, 29: 9,
}

NEW_CLASS_NAMES = {
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


def remap_file(txt_path: Path) -> Tuple[int, int]:
    """Remapeia um arquivo .txt de anotação. Retorna (total, remapped)."""
    lines = txt_path.read_text().strip().splitlines()
    if not lines:
        return 0, 0

    new_lines = []
    remapped = 0
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        old_id = int(parts[0])
        new_id = REMAP.get(old_id)
        if new_id is None:
            print(f"  WARNING: class {old_id} not in remap table, skipping: {txt_path.name}")
            continue
        parts[0] = str(new_id)
        new_lines.append(" ".join(parts))
        remapped += 1

    txt_path.write_text("\n".join(new_lines) + ("\n" if new_lines else ""))
    return len(lines), remapped


def main():
    print("=" * 50)
    print("Remapeando anotações: 30 classes -> 10 classes")
    print("=" * 50)

    txt_files = sorted(ANNOTATIONS_DIR.glob("*.txt"))
    print(f"\nEncontrados {len(txt_files)} arquivos .txt\n")

    total_annotations = 0
    total_remapped = 0
    new_class_counts = Counter()

    for txt_path in txt_files:
        total, remapped = remap_file(txt_path)
        total_annotations += total
        total_remapped += remapped

        # Contar distribuição nova
        for line in txt_path.read_text().strip().splitlines():
            parts = line.strip().split()
            if parts:
                new_class_counts[int(parts[0])] += 1

    print(f"\nTotal anotações processadas: {total_annotations}")
    print(f"Total remapeadas: {total_remapped}")
    print(f"\nDistribuição das novas classes:")
    print("-" * 40)
    for class_id in sorted(new_class_counts.keys()):
        name = NEW_CLASS_NAMES.get(class_id, f"unknown_{class_id}")
        count = new_class_counts[class_id]
        bar = "#" * (count // 5)
        print(f"  {class_id}: {name:12s} -> {count:4d} {bar}")

    # Verificar que não há IDs fora de 0-9
    invalid = [k for k in new_class_counts if k < 0 or k > 9]
    if invalid:
        print(f"\nERRO: IDs inválidos encontrados: {invalid}")
    else:
        print(f"\nOK: Todas as anotações estão no range 0-9")


if __name__ == "__main__":
    main()
