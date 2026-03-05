#!/usr/bin/env python3
"""
Gerador de diagramas de arquitetura sintéticos com anotações YOLO automáticas.

Usa PIL para desenhar diagramas programaticamente — sem dependências externas
como graphviz. Cada componente desenhado tem posição exata, gerando anotações
100% precisas.

Saída:
    dataset/images/synthetic/  → imagens PNG geradas
    dataset/annotations/       → labels YOLO .txt correspondentes

Uso:
    python generate_synthetic.py [--count 500] [--seed 42]
"""

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERRO: Pillow não instalado. Rode: pip install Pillow")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.parent
OUTPUT_IMAGES_DIR = BASE_DIR / "images" / "synthetic"
OUTPUT_ANNOTATIONS_DIR = BASE_DIR / "annotations"

# ─── Classes YOLO ──────────────────────────────────────────────────────────────

CLASS_ID = {
    "server": 0,
    "database": 1,
    "network": 2,
    "storage": 3,
    "security": 4,
    "serverless": 5,
    "queue": 6,
    "monitoring": 7,
    "user": 8,
    "external": 9,
}

# ─── Aparência dos componentes ─────────────────────────────────────────────────

COMPONENT_STYLE = {
    "server": {
        "fill": [(220, 230, 255), (200, 215, 255), (210, 225, 250)],
        "border": [(60, 100, 200), (40, 80, 180), (70, 110, 210)],
        "symbol": "▪ SERVER",
        "shape": "rect",
    },
    "database": {
        "fill": [(220, 255, 220), (200, 245, 205), (210, 250, 215)],
        "border": [(30, 140, 60), (20, 120, 50), (40, 150, 70)],
        "symbol": "◉ DB",
        "shape": "cylinder",
    },
    "network": {
        "fill": [(255, 240, 200), (255, 235, 190), (250, 238, 205)],
        "border": [(200, 140, 20), (180, 120, 10), (210, 150, 30)],
        "symbol": "◈ NET",
        "shape": "diamond",
    },
    "storage": {
        "fill": [(255, 220, 200), (250, 215, 195), (255, 225, 205)],
        "border": [(200, 80, 30), (180, 60, 20), (210, 90, 40)],
        "symbol": "▦ STORAGE",
        "shape": "rect",
    },
    "security": {
        "fill": [(255, 200, 200), (250, 195, 195), (255, 205, 205)],
        "border": [(180, 30, 30), (160, 20, 20), (190, 40, 40)],
        "symbol": "⬡ SEC",
        "shape": "hexagon",
    },
    "serverless": {
        "fill": [(230, 200, 255), (225, 195, 250), (235, 205, 255)],
        "border": [(120, 40, 200), (100, 30, 180), (130, 50, 210)],
        "symbol": "λ FN",
        "shape": "rounded",
    },
    "queue": {
        "fill": [(200, 245, 245), (195, 240, 242), (205, 248, 248)],
        "border": [(20, 160, 160), (10, 140, 140), (30, 170, 170)],
        "symbol": "▷ QUEUE",
        "shape": "parallelogram",
    },
    "monitoring": {
        "fill": [(245, 245, 200), (242, 242, 195), (248, 248, 205)],
        "border": [(150, 150, 20), (130, 130, 10), (160, 160, 30)],
        "symbol": "⬤ MONITOR",
        "shape": "rect",
    },
    "user": {
        "fill": [(240, 240, 240), (235, 235, 235), (245, 245, 245)],
        "border": [(80, 80, 80), (60, 60, 60), (90, 90, 90)],
        "symbol": "☺ USER",
        "shape": "rounded",
    },
    "external": {
        "fill": [(200, 200, 200), (195, 195, 195), (205, 205, 205)],
        "border": [(100, 100, 100), (80, 80, 80), (110, 110, 110)],
        "symbol": "⊞ EXT",
        "shape": "dashed_rect",
    },
}

# Paletas de fundo para os diagramas
BACKGROUNDS = [
    (255, 255, 255),   # Branco
    (248, 249, 252),   # Off-white azulado
    (252, 252, 248),   # Off-white amarelado
    (245, 248, 250),   # Cinza-azul claro
    (250, 250, 250),   # Cinza muito claro
]

# ─── Dataclass para componente desenhado ───────────────────────────────────────

@dataclass
class DrawnComponent:
    class_name: str
    x1: int
    y1: int
    x2: int
    y2: int
    label: str = ""

    @property
    def class_id(self):
        return CLASS_ID[self.class_name]

    def to_yolo(self, img_w: int, img_h: int) -> str:
        cx = (self.x1 + self.x2) / 2 / img_w
        cy = (self.y1 + self.y2) / 2 / img_h
        w = (self.x2 - self.x1) / img_w
        h = (self.y2 - self.y1) / img_h
        return f"{self.class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"


# ─── Helpers de desenho ────────────────────────────────────────────────────────

def get_font(size: int = 12) -> ImageFont.ImageFont:
    """Retorna uma fonte disponível no sistema."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_component(
    draw: ImageDraw.Draw,
    comp: DrawnComponent,
    rng: random.Random,
    font: ImageFont.ImageFont,
    font_small: ImageFont.ImageFont,
):
    """Desenha um componente de arquitetura no canvas."""
    style = COMPONENT_STYLE[comp.class_name]
    fill = rng.choice(style["fill"])
    border = rng.choice(style["border"])
    shape = style["shape"]
    x1, y1, x2, y2 = comp.x1, comp.y1, comp.x2, comp.y2

    border_width = rng.randint(2, 3)

    if shape == "rect":
        draw.rectangle([x1, y1, x2, y2], fill=fill, outline=border, width=border_width)

    elif shape == "rounded":
        radius = min(12, (x2 - x1) // 5, (y2 - y1) // 5)
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=border, width=border_width)

    elif shape == "cylinder":
        # Retângulo principal + elipse no topo/base simulando cilindro
        eh = max(8, (y2 - y1) // 6)
        draw.rectangle([x1, y1 + eh // 2, x2, y2 - eh // 2], fill=fill, outline=None)
        draw.ellipse([x1, y1, x2, y1 + eh], fill=fill, outline=border, width=border_width)
        draw.ellipse([x1, y2 - eh, x2, y2], fill=fill, outline=border, width=border_width)
        draw.rectangle([x1, y1 + eh // 2, x2, y2 - eh // 2], fill=fill, outline=None)
        draw.line([(x1, y1 + eh // 2), (x1, y2 - eh // 2)], fill=border, width=border_width)
        draw.line([(x2, y1 + eh // 2), (x2, y2 - eh // 2)], fill=border, width=border_width)
        draw.ellipse([x1, y1, x2, y1 + eh], fill=fill, outline=border, width=border_width)

    elif shape == "diamond":
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        pts = [(cx, y1), (x2, cy), (cx, y2), (x1, cy)]
        draw.polygon(pts, fill=fill, outline=border)

    elif shape == "hexagon":
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        rx = (x2 - x1) // 2
        ry = (y2 - y1) // 2
        offset = rx // 3
        pts = [
            (cx - rx, cy),
            (cx - rx + offset, cy - ry),
            (cx + rx - offset, cy - ry),
            (cx + rx, cy),
            (cx + rx - offset, cy + ry),
            (cx - rx + offset, cy + ry),
        ]
        draw.polygon(pts, fill=fill, outline=border)

    elif shape == "parallelogram":
        skew = (y2 - y1) // 4
        pts = [(x1 + skew, y1), (x2, y1), (x2 - skew, y2), (x1, y2)]
        draw.polygon(pts, fill=fill, outline=border)

    elif shape == "dashed_rect":
        # Retângulo pontilhado simulado com múltiplas linhas
        draw.rectangle([x1, y1, x2, y2], fill=fill, outline=None)
        dash = 6
        gap = 4
        for side in ["top", "bottom", "left", "right"]:
            if side == "top":
                pos = y1
                for px in range(x1, x2, dash + gap):
                    draw.line([(px, pos), (min(px + dash, x2), pos)], fill=border, width=border_width)
            elif side == "bottom":
                pos = y2
                for px in range(x1, x2, dash + gap):
                    draw.line([(px, pos), (min(px + dash, x2), pos)], fill=border, width=border_width)
            elif side == "left":
                pos = x1
                for py in range(y1, y2, dash + gap):
                    draw.line([(pos, py), (pos, min(py + dash, y2))], fill=border, width=border_width)
            elif side == "right":
                pos = x2
                for py in range(y1, y2, dash + gap):
                    draw.line([(pos, py), (pos, min(py + dash, y2))], fill=border, width=border_width)

    # Label do componente (tipo)
    symbol = style["symbol"]
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    try:
        bbox = draw.textbbox((0, 0), symbol, font=font_small)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except Exception:
        tw, th = len(symbol) * 6, 10

    draw.text((cx - tw // 2, cy - th // 2), symbol, fill=border, font=font_small)

    # Rótulo customizado (se houver)
    if comp.label:
        try:
            bbox2 = draw.textbbox((0, 0), comp.label, font=font_small)
            tw2 = bbox2[2] - bbox2[0]
        except Exception:
            tw2 = len(comp.label) * 5
        label_y = y2 + 4
        draw.text((cx - tw2 // 2, label_y), comp.label, fill=(50, 50, 50), font=font_small)


def draw_arrow(
    draw: ImageDraw.Draw,
    src: DrawnComponent,
    dst: DrawnComponent,
    color: tuple = (100, 100, 100),
    width: int = 2,
):
    """Desenha uma seta entre dois componentes."""
    sx = (src.x1 + src.x2) // 2
    sy = (src.y1 + src.y2) // 2
    dx = (dst.x1 + dst.x2) // 2
    dy = (dst.y1 + dst.y2) // 2

    # Ponto de saída/entrada na borda dos boxes
    def clamp_to_box(cx, cy, tx, ty, box):
        bx1, by1, bx2, by2 = box.x1, box.y1, box.x2, box.y2
        if tx == cx:
            return cx, (by1 if ty < cy else by2)
        m = (ty - cy) / (tx - cx)
        # testar lados
        candidates = []
        # esquerda
        xi, yi = bx1, cy + m * (bx1 - cx)
        if by1 <= yi <= by2:
            candidates.append((xi, yi))
        # direita
        xi, yi = bx2, cy + m * (bx2 - cx)
        if by1 <= yi <= by2:
            candidates.append((xi, yi))
        # topo
        yi2 = by1
        xi2 = cx + (yi2 - cy) / m if m != 0 else cx
        if bx1 <= xi2 <= bx2:
            candidates.append((xi2, yi2))
        # base
        yi2 = by2
        xi2 = cx + (yi2 - cy) / m if m != 0 else cx
        if bx1 <= xi2 <= bx2:
            candidates.append((xi2, yi2))
        if not candidates:
            return cx, cy
        return min(candidates, key=lambda p: (p[0] - tx) ** 2 + (p[1] - ty) ** 2)

    ox, oy = clamp_to_box(sx, sy, dx, dy, src)
    ix, iy = clamp_to_box(dx, dy, sx, sy, dst)

    draw.line([(ox, oy), (ix, iy)], fill=color, width=width)

    # Ponta da seta
    import math
    angle = math.atan2(iy - oy, ix - ox)
    arrow_len = 10
    arrow_angle = 0.4
    ax1 = ix - arrow_len * math.cos(angle - arrow_angle)
    ay1 = iy - arrow_len * math.sin(angle - arrow_angle)
    ax2 = ix - arrow_len * math.cos(angle + arrow_angle)
    ay2 = iy - arrow_len * math.sin(angle + arrow_angle)
    draw.polygon([(ix, iy), (int(ax1), int(ay1)), (int(ax2), int(ay2))], fill=color)


def draw_cluster_box(
    draw: ImageDraw.Draw,
    x1: int, y1: int, x2: int, y2: int,
    label: str,
    color: tuple = (180, 180, 210),
    font: Optional[ImageFont.ImageFont] = None,
):
    """Desenha um grupo/cluster com borda pontilhada."""
    padding = 4
    draw.rectangle([x1, y1, x2, y2], fill=None, outline=color, width=1)
    # Linha dupla simula cluster
    draw.rectangle([x1 + 2, y1 + 2, x2 - 2, y2 - 2], fill=None, outline=color, width=1)
    if label and font:
        draw.text((x1 + 6, y1 + 4), label, fill=color, font=font)


# ─── Layouts de diagrama ───────────────────────────────────────────────────────

def layout_linear(rng: random.Random, canvas_w: int, canvas_h: int) -> list:
    """Layout linear: usuário → network → server → database."""
    sequence = rng.choice([
        ["user", "network", "server", "database"],
        ["external", "security", "server", "database"],
        ["user", "network", "serverless", "storage"],
        ["external", "network", "server", "queue", "monitoring"],
        ["user", "security", "server", "database", "storage"],
    ])

    n = len(sequence)
    margin = 60
    comp_w = rng.randint(90, 130)
    comp_h = rng.randint(55, 80)
    total_w = n * comp_w + (n - 1) * 60
    start_x = (canvas_w - total_w) // 2
    cy = canvas_h // 2

    comps = []
    for i, cls in enumerate(sequence):
        x1 = start_x + i * (comp_w + 60)
        y1 = cy - comp_h // 2 + rng.randint(-20, 20)
        comps.append(DrawnComponent(cls, x1, y1, x1 + comp_w, y1 + comp_h))
    return comps


def layout_hub_spoke(rng: random.Random, canvas_w: int, canvas_h: int) -> list:
    """Layout hub-and-spoke: um componente central conectado a vários periféricos."""
    import math

    hub_cls = rng.choice(["server", "network", "security"])
    spokes_pool = [c for c in CLASS_ID if c != hub_cls]
    n_spokes = rng.randint(3, 6)
    spokes = rng.sample(spokes_pool, n_spokes)

    cx, cy = canvas_w // 2, canvas_h // 2
    hub_w = rng.randint(100, 130)
    hub_h = rng.randint(65, 85)
    hub = DrawnComponent(hub_cls, cx - hub_w // 2, cy - hub_h // 2, cx + hub_w // 2, cy + hub_h // 2)

    radius = min(canvas_w, canvas_h) // 2 - 100
    comps = [hub]
    for i, cls in enumerate(spokes):
        angle = 2 * math.pi * i / n_spokes
        sx = int(cx + radius * math.cos(angle))
        sy = int(cy + radius * math.sin(angle))
        sw = rng.randint(80, 110)
        sh = rng.randint(50, 70)
        sx = max(30, min(canvas_w - sw - 30, sx - sw // 2))
        sy = max(30, min(canvas_h - sh - 30, sy - sh // 2))
        comps.append(DrawnComponent(cls, sx, sy, sx + sw, sy + sh))
    return comps


def layout_layered(rng: random.Random, canvas_w: int, canvas_h: int) -> list:
    """Layout em camadas: frontend / backend / data."""
    layer_defs = rng.choice([
        [["user", "external"], ["network", "security"], ["server", "serverless"], ["database", "storage"]],
        [["user"], ["network"], ["server", "queue"], ["database", "monitoring"]],
        [["external", "user"], ["security"], ["server"], ["database", "storage", "queue"]],
        [["user"], ["network", "security"], ["server", "serverless", "monitoring"], ["database"]],
    ])

    n_layers = len(layer_defs)
    margin_x = 50
    margin_y = 60
    layer_h = (canvas_h - 2 * margin_y) // n_layers
    comps = []

    for li, layer in enumerate(layer_defs):
        n_items = len(layer)
        item_w = min(130, (canvas_w - 2 * margin_x - (n_items - 1) * 40) // n_items)
        item_h = rng.randint(50, min(70, layer_h - 30))
        total_row_w = n_items * item_w + (n_items - 1) * 40
        start_x = (canvas_w - total_row_w) // 2
        row_y = margin_y + li * layer_h + (layer_h - item_h) // 2

        for ii, cls in enumerate(layer):
            x1 = start_x + ii * (item_w + 40)
            y1 = row_y + rng.randint(-10, 10)
            comps.append(DrawnComponent(cls, x1, y1, x1 + item_w, y1 + item_h))

    return comps


def layout_microservices(rng: random.Random, canvas_w: int, canvas_h: int) -> list:
    """Layout de microserviços: muitos componentes espalhados em grid."""
    all_classes = list(CLASS_ID.keys())
    n = rng.randint(6, 10)
    selected = rng.choices(all_classes, k=n)

    cols = rng.randint(3, 4)
    rows = (n + cols - 1) // cols

    comp_w = rng.randint(80, 110)
    comp_h = rng.randint(50, 70)
    gap_x = rng.randint(50, 80)
    gap_y = rng.randint(50, 80)

    total_w = cols * comp_w + (cols - 1) * gap_x
    total_h = rows * comp_h + (rows - 1) * gap_y
    start_x = (canvas_w - total_w) // 2
    start_y = (canvas_h - total_h) // 2

    comps = []
    for i, cls in enumerate(selected):
        col = i % cols
        row = i // cols
        x1 = start_x + col * (comp_w + gap_x) + rng.randint(-15, 15)
        y1 = start_y + row * (comp_h + gap_y) + rng.randint(-15, 15)
        x1 = max(20, min(canvas_w - comp_w - 20, x1))
        y1 = max(20, min(canvas_h - comp_h - 20, y1))
        comps.append(DrawnComponent(cls, x1, y1, x1 + comp_w, y1 + comp_h))

    return comps


LAYOUTS = [layout_linear, layout_hub_spoke, layout_layered, layout_microservices]


# ─── Geração de conexões ───────────────────────────────────────────────────────

def generate_connections(comps: list, rng: random.Random) -> list:
    """Gera conexões (arestas) entre os componentes."""
    if len(comps) < 2:
        return []

    edges = []
    n = len(comps)

    # Sempre conectar sequencialmente (garante conectividade)
    for i in range(n - 1):
        edges.append((comps[i], comps[i + 1]))

    # Adicionar algumas conexões extras aleatórias
    n_extra = rng.randint(0, min(3, n - 1))
    for _ in range(n_extra):
        a, b = rng.sample(comps, 2)
        if (a, b) not in edges and (b, a) not in edges:
            edges.append((a, b))

    return edges


# ─── Geração do diagrama completo ──────────────────────────────────────────────

def generate_diagram(rng: random.Random, idx: int) -> tuple:
    """Gera um diagrama completo e retorna (imagem PIL, lista de DrawnComponent)."""

    # Tamanho variado do canvas
    canvas_w = rng.choice([640, 800, 960, 1024, 1280])
    canvas_h = rng.choice([480, 600, 720, 800])

    # Fundo
    bg_color = rng.choice(BACKGROUNDS)
    img = Image.new("RGB", (canvas_w, canvas_h), bg_color)
    draw = ImageDraw.Draw(img)

    # Grid de fundo opcional
    if rng.random() < 0.3:
        grid_color = tuple(max(0, c - 10) for c in bg_color)
        for gx in range(0, canvas_w, 40):
            draw.line([(gx, 0), (gx, canvas_h)], fill=grid_color, width=1)
        for gy in range(0, canvas_h, 40):
            draw.line([(0, gy), (canvas_w, gy)], fill=grid_color, width=1)

    # Fontes
    font = get_font(13)
    font_small = get_font(10)
    font_title = get_font(14)

    # Layout
    layout_fn = rng.choice(LAYOUTS)
    comps = layout_fn(rng, canvas_w, canvas_h)

    # Garantir que todos os componentes estão dentro do canvas
    for comp in comps:
        pad = 5
        comp.x1 = max(pad, comp.x1)
        comp.y1 = max(pad, comp.y1)
        comp.x2 = min(canvas_w - pad, comp.x2)
        comp.y2 = min(canvas_h - pad, comp.y2)

    # Conexões (desenhar antes dos componentes para ficarem embaixo)
    edges = generate_connections(comps, rng)
    arrow_color = tuple(max(0, c - 60) for c in bg_color)
    for src, dst in edges:
        draw_arrow(draw, src, dst, color=arrow_color, width=rng.randint(1, 2))

    # Clusters opcionais (grupos ao redor de 2-3 componentes)
    if rng.random() < 0.4 and len(comps) >= 4:
        n_cluster = rng.randint(2, 3)
        cluster_comps = rng.sample(comps, n_cluster)
        pad = 12
        cx1 = min(c.x1 for c in cluster_comps) - pad
        cy1 = min(c.y1 for c in cluster_comps) - pad
        cx2 = max(c.x2 for c in cluster_comps) + pad
        cy2 = max(c.y2 for c in cluster_comps) + pad
        cluster_names = rng.choice(["VPC", "Cluster", "Zone", "Region", "Subnet", "Service Mesh"])
        draw_cluster_box(draw, cx1, cy1, cx2, cy2, cluster_names,
                         color=(150, 150, 200), font=font_small)

    # Desenhar componentes
    for comp in comps:
        draw_component(draw, comp, rng, font, font_small)

    # Título do diagrama
    if rng.random() < 0.6:
        title = rng.choice([
            "AWS Architecture", "System Design", "Cloud Infrastructure",
            "Microservices", "Data Pipeline", "Web Architecture",
            "Security Architecture", "Backend Services", "Platform Overview",
            "Service Topology", "Network Diagram", "API Gateway Pattern",
        ])
        draw.text((10, 10), title, fill=(80, 80, 80), font=font_title)

    return img, comps


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gera diagramas sintéticos com anotações YOLO")
    parser.add_argument("--count", type=int, default=500, help="Número de diagramas a gerar")
    parser.add_argument("--seed", type=int, default=42, help="Seed para reprodutibilidade")
    parser.add_argument("--preview", action="store_true", help="Salvar apenas 5 imagens de preview")
    args = parser.parse_args()

    count = 5 if args.preview else args.count

    OUTPUT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("GERADOR DE DIAGRAMAS SINTÉTICOS")
    print("=" * 60)
    print(f"Gerando {count} diagramas...")
    print(f"  Imagens: {OUTPUT_IMAGES_DIR}")
    print(f"  Labels:  {OUTPUT_ANNOTATIONS_DIR}")
    print()

    class_counter = {cls: 0 for cls in CLASS_ID}
    rng = random.Random(args.seed)

    for i in range(count):
        img, comps = generate_diagram(rng, i)
        img_w, img_h = img.size

        name = f"synthetic_{i:05d}"
        img_path = OUTPUT_IMAGES_DIR / f"{name}.png"
        ann_path = OUTPUT_ANNOTATIONS_DIR / f"{name}.txt"

        img.save(img_path, "PNG")

        lines = []
        for comp in comps:
            line = comp.to_yolo(img_w, img_h)
            lines.append(line)
            class_counter[comp.class_name] += 1

        with open(ann_path, "w") as f:
            f.write("\n".join(lines) + "\n")

        if (i + 1) % 50 == 0 or i < 5:
            print(f"  [{i+1:4d}/{count}] {name}.png ({img_w}x{img_h}) — {len(comps)} componentes")

    print()
    print("=" * 60)
    print("DISTRIBUIÇÃO DE CLASSES GERADAS")
    print("=" * 60)
    total = sum(class_counter.values())
    for cls, count_cls in sorted(class_counter.items(), key=lambda x: -x[1]):
        pct = count_cls / total * 100 if total > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  {cls:<12} {count_cls:5d}  {pct:5.1f}%  {bar}")
    print(f"  {'TOTAL':<12} {total:5d}")

    print()
    print("=" * 60)
    print("PRÓXIMOS PASSOS")
    print("=" * 60)
    print("1. Adicionar imagens ao split de treino:")
    print(f"   ls {OUTPUT_IMAGES_DIR}/*.png | sed 's|{BASE_DIR}/||' >> {BASE_DIR}/splits/train.txt")
    print()
    print("2. Rebalancear e treinar:")
    print("   python3 scripts/augment_balance.py")
    print("   python3 scripts/train_yolo.py --epochs 150")
    print()
    print("✓ Concluído!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
