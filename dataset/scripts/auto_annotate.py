#!/usr/bin/env python3
"""
Script de anotação semi-automática usando Claude Vision.
Gera anotações iniciais que podem ser revisadas manualmente.
"""

import os
import json
import base64
from pathlib import Path
from typing import Dict, List, Any, Tuple
import anthropic
from PIL import Image

# Configuração
BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "images"
ANNOTATIONS_DIR = BASE_DIR / "annotations"
ANNOTATIONS_DIR.mkdir(exist_ok=True)

# Mapeamento de categorias
CATEGORY_MAP = {
    "user": 0,
    "web_browser": 1,
    "mobile_app": 2,
    "api_gateway": 3,
    "load_balancer": 4,
    "web_server": 5,
    "app_server": 6,
    "microservice": 7,
    "container": 8,
    "kubernetes": 9,
    "lambda_function": 10,
    "database_sql": 11,
    "database_nosql": 12,
    "cache": 13,
    "queue": 14,
    "storage_object": 15,
    "storage_block": 16,
    "cdn": 17,
    "firewall": 18,
    "waf": 19,
    "vpc": 20,
    "subnet": 21,
    "iam": 22,
    "kms": 23,
    "secrets_manager": 24,
    "monitoring": 25,
    "logging": 26,
    "external_service": 27,
    "dns": 28,
    "email_service": 29,
}

# Prompt para Claude Vision
ANNOTATION_PROMPT = """Analyze this software architecture diagram and identify all components.

For each component you find, provide:
1. category: One of these exact values: user, web_browser, mobile_app, api_gateway, load_balancer, web_server, app_server, microservice, container, kubernetes, lambda_function, database_sql, database_nosql, cache, queue, storage_object, storage_block, cdn, firewall, waf, vpc, subnet, iam, kms, secrets_manager, monitoring, logging, external_service, dns, email_service
2. label: The text label shown in the diagram (e.g., "Amazon RDS", "API Gateway")
3. bbox_percent: Approximate bounding box as [x_center, y_center, width, height] where all values are percentages (0-100) of the image dimensions

Also identify connections between components:
- from_label: Source component label
- to_label: Target component label
- protocol: If visible (HTTP, HTTPS, TCP, etc.)

Return ONLY a valid JSON object with this structure:
{
  "provider": "aws|azure|gcp|generic",
  "components": [
    {
      "category": "database_sql",
      "label": "Amazon RDS",
      "bbox_percent": [50, 60, 10, 8]
    }
  ],
  "connections": [
    {
      "from_label": "API Gateway",
      "to_label": "Lambda",
      "protocol": "HTTPS"
    }
  ]
}

Be precise with bounding boxes - they should tightly fit each component icon/box."""


def encode_image(image_path: Path) -> Tuple[str, str]:
    """Encode image to base64 and determine media type."""
    suffix = image_path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(suffix, "image/png")

    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    return data, media_type


def get_image_dimensions(image_path: Path) -> Tuple[int, int]:
    """Get image width and height."""
    with Image.open(image_path) as img:
        return img.width, img.height


def annotate_image(client: anthropic.Anthropic, image_path: Path) -> Dict[str, Any]:
    """Use Claude Vision to annotate an image."""
    print(f"Annotating: {image_path.name}")

    # Encode image
    image_data, media_type = encode_image(image_path)
    width, height = get_image_dimensions(image_path)

    # Call Claude Vision
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": ANNOTATION_PROMPT,
                    },
                ],
            }
        ],
    )

    # Parse response
    response_text = message.content[0].text

    # Extract JSON from response (may be wrapped in markdown)
    if "```json" in response_text:
        json_str = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        json_str = response_text.split("```")[1].split("```")[0]
    else:
        json_str = response_text

    try:
        result = json.loads(json_str.strip())
    except json.JSONDecodeError as e:
        print(f"  Warning: Failed to parse JSON: {e}")
        result = {"components": [], "connections": [], "provider": "generic"}

    # Convert to annotation format
    annotations = []
    for i, comp in enumerate(result.get("components", [])):
        category = comp.get("category", "external_service")
        category_id = CATEGORY_MAP.get(category, 27)

        # Convert percentage bbox to normalized (0-1)
        bbox_pct = comp.get("bbox_percent", [50, 50, 10, 10])
        bbox_norm = [
            bbox_pct[0] / 100,  # x_center
            bbox_pct[1] / 100,  # y_center
            bbox_pct[2] / 100,  # width
            bbox_pct[3] / 100,  # height
        ]

        # Also compute pixel coordinates
        bbox_pixels = [
            int((bbox_pct[0] - bbox_pct[2] / 2) / 100 * width),   # x_min
            int((bbox_pct[1] - bbox_pct[3] / 2) / 100 * height),  # y_min
            int((bbox_pct[0] + bbox_pct[2] / 2) / 100 * width),   # x_max
            int((bbox_pct[1] + bbox_pct[3] / 2) / 100 * height),  # y_max
        ]

        annotations.append({
            "id": i + 1,
            "category_id": category_id,
            "category_name": category,
            "bbox": bbox_norm,
            "bbox_pixels": bbox_pixels,
            "confidence": 0.8,  # Auto-annotation confidence
            "attributes": {
                "label": comp.get("label", ""),
                "auto_annotated": True,
            },
        })

    # Convert connections
    connections = []
    label_to_id = {a["attributes"]["label"]: a["id"] for a in annotations}

    for conn in result.get("connections", []):
        from_id = label_to_id.get(conn.get("from_label"))
        to_id = label_to_id.get(conn.get("to_label"))

        if from_id and to_id:
            connections.append({
                "from_id": from_id,
                "to_id": to_id,
                "protocol": conn.get("protocol", ""),
                "bidirectional": False,
            })

    # Build final annotation
    provider_dir = image_path.parent.name
    annotation = {
        "image_id": image_path.stem,
        "file_name": f"{provider_dir}/{image_path.name}",
        "width": width,
        "height": height,
        "provider": result.get("provider", provider_dir),
        "annotations": annotations,
        "connections": connections,
        "metadata": {
            "auto_annotated": True,
            "model": "claude-sonnet-4-20250514",
            "needs_review": True,
        },
    }

    return annotation


def save_annotation(annotation: Dict[str, Any], output_path: Path):
    """Save annotation to JSON file."""
    with open(output_path, "w") as f:
        json.dump(annotation, f, indent=2)
    print(f"  Saved: {output_path.name}")


def convert_to_yolo(annotation: Dict[str, Any], output_path: Path):
    """Convert annotation to YOLO format (.txt)."""
    lines = []
    for ann in annotation["annotations"]:
        # YOLO format: class_id x_center y_center width height (all normalized 0-1)
        bbox = ann["bbox"]
        line = f"{ann['category_id']} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}"
        lines.append(line)

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"  YOLO: {output_path.name}")


def main():
    print("=" * 50)
    print("Auto-Annotation with Claude Vision")
    print("=" * 50)

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return

    client = anthropic.Anthropic(api_key=api_key)

    # Find all images
    image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    images = []
    for ext in image_extensions:
        images.extend(IMAGES_DIR.rglob(f"*{ext}"))
        images.extend(IMAGES_DIR.rglob(f"*{ext.upper()}"))

    print(f"\nFound {len(images)} images to annotate\n")

    # Annotate each image
    for image_path in images:
        # Skip if already annotated
        annotation_path = ANNOTATIONS_DIR / f"{image_path.stem}.json"
        if annotation_path.exists():
            print(f"Skip (exists): {image_path.name}")
            continue

        try:
            annotation = annotate_image(client, image_path)
            save_annotation(annotation, annotation_path)

            # Also save YOLO format
            yolo_path = ANNOTATIONS_DIR / f"{image_path.stem}.txt"
            convert_to_yolo(annotation, yolo_path)

            print(f"  Components: {len(annotation['annotations'])}")
            print(f"  Connections: {len(annotation['connections'])}")
            print()

        except Exception as e:
            print(f"  Error: {e}\n")

    print("\nDone! Review annotations in:", ANNOTATIONS_DIR)


if __name__ == "__main__":
    main()
