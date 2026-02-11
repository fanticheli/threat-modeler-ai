#!/usr/bin/env python3
"""
Script para coletar imagens de arquitetura de software de fontes públicas.
Fontes: GitHub repos, Azure Architecture Center, e imagens locais.

Pré-requisitos:
    pip install requests Pillow cairosvg

Uso:
    python collect_images.py
    python collect_images.py --skip-svg   # Pular conversão SVG (se cairosvg não instalado)
"""

import os
import sys
import json
import hashlib
import argparse
import requests
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse
import time
import shutil

# Diretório base
BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "images"

# Headers para requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (Educational Purpose - FIAP Hackathon)"
}

# ==============================================================================
# FONTES DE IMAGENS - Diagramas de arquitetura públicos
# ==============================================================================

# GitHub: arpitbhardwaj/architecture-diagrams (MIT License)
# GitHub: donnemartin/system-design-primer (CC-BY-4.0)
# GitHub: rcherara/microservice-architecture
GITHUB_DIAGRAMS = {
    "generic": [
        # arpitbhardwaj/architecture-diagrams - System design diagrams
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/services/image/NewsFeed.png",
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/services/image/Notification.png",
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/services/image/RateLimiter.png",
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/services/image/ChatSystem.png",
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/services/image/AutoCompleteSystem.png",
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/services/image/VideoStreaming.png",
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/services/image/CloudStorage.png",
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/services/image/Proximity.png",
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/services/image/MetricsMonitoringAndAlerting.png",
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/services/image/AdClickAggregation.png",
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/cloudnative/image/k8s.png",
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/cloudnative/image/ServiceMesh.png",
        "https://raw.githubusercontent.com/arpitbhardwaj/architecture-diagrams/main/cloudnative/image/MessageQueue.png",
        # donnemartin/system-design-primer - Diversos diagramas de system design
        "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/images/jj3A5N8.png",
        "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/images/zdCAkB3.png",
        "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/images/b4YtAEN.png",
        "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/images/jrUBAF7.png",
        "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/images/OfVllex.png",
        "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/images/4edXG0T.png",
        "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/images/bWxPtQA.png",
        "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/images/V5q57vU.png",
        "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/images/cdCv5g7.png",
        "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/images/4j99mhe.png",
        "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/images/MzExP06.png",
        # rcherara/microservice-architecture
        "https://raw.githubusercontent.com/rcherara/microservice-architecture/master/docs/images/Targert-platform-architecture.png",
    ],
    # HariSekhon/Diagrams-as-Code - AWS architecture diagrams (Apache 2.0)
    "aws": [
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/aws.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/aws_clustered_web_services.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/aws_event_processing.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/aws_load_balanced_web_farm.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/aws_serverless_image_processing.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/aws_web_service_db_cluster.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/aws_web_traffic_classic.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/advanced_web_services_open_source.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/multi_dc_gslb_f5_java_stack.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/kubernetes_kong_api_gateway_eks.png",
        # awsexp/architecture - Real-world AWS architectures
        "https://raw.githubusercontent.com/awsexp/architecture/master/diagrams/ec2/Teem.png",
        "https://raw.githubusercontent.com/awsexp/architecture/master/diagrams/serverless/A%20Sample%20Serverless%20Contact%20App.png",
        "https://raw.githubusercontent.com/awsexp/architecture/master/diagrams/serverless/AWS%20Backups.png",
        "https://raw.githubusercontent.com/awsexp/architecture/master/diagrams/serverless/Analytics%20Serverless%20Data%20Back%20End.png",
        "https://raw.githubusercontent.com/awsexp/architecture/master/diagrams/serverless/EC2%20State%20Change%20Slack.png",
        "https://raw.githubusercontent.com/awsexp/architecture/master/diagrams/serverless/Teem%20Ops%20Serverless%20Back%20End.png",
    ],
    # HariSekhon/Diagrams-as-Code - GCP architecture diagrams
    "gcp": [
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/gcp_cloudflare_web_architecture_gke.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/gcp_pubsub_analytics.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/LucidChart_GCP_diagram.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/kubernetes_traefik_ingress_gke.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/kubernetes_deployment_hpa_ingress.png",
        "https://raw.githubusercontent.com/HariSekhon/Diagrams-as-Code/master/images/kubernetes_stateful_architecture.png",
    ],
}

# Azure Architecture Center - PNG diretos
AZURE_PNG_DIAGRAMS = [
    "https://learn.microsoft.com/en-us/azure/architecture/databases/architecture/_images/azure-data-factory-baseline.png",
    "https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/_images/hub-spoke.png",
    "https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/_images/spoke-spoke-routing.png",
    "https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/_images/spoke-spoke-avnm.png",
    "https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/_images/hub-and-spoke.png",
]

# Azure Architecture Center - SVG diagrams (CC-BY-4.0 / Microsoft docs)
AZURE_SVG_DIAGRAMS = [
    "https://learn.microsoft.com/en-us/azure/architecture/web-apps/app-service/_images/basic-app-service-architecture-flow.svg",
    "https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/containers/aks-microservices/images/microservices-architecture.svg",
    "https://learn.microsoft.com/en-us/azure/architecture/example-scenario/serverless/media/microservices-with-container-apps.svg",
    "https://learn.microsoft.com/en-us/azure/architecture/web-apps/app-service-environment/_images/app-service-environment.svg",
    "https://learn.microsoft.com/en-us/azure/architecture/web-apps/app-service-environment/_images/app-service-environment-multisite.svg",
    "https://learn.microsoft.com/en-us/azure/architecture/web-apps/app-service/_images/baseline-app-service-architecture.svg",
    "https://learn.microsoft.com/en-us/azure/architecture/web-apps/app-service/_images/baseline-app-service-network-architecture.svg",
    "https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/_images/baseline-microsoft-foundry.svg",
    "https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/_images/baseline-microsoft-foundry-network-flow.svg",
    "https://learn.microsoft.com/en-us/azure/architecture/databases/architecture/_images/azure-data-factory-hardened-network.svg",
    "https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/containers/aks-multi-region/images/aks-multi-cluster.svg",
    "https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/containers/aks-multi-region/images/aks-ingress-flow.svg",
]


def calculate_hash(file_path: Path) -> str:
    """Calcula hash MD5 do arquivo para detectar duplicatas."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_file(url: str, output_path: Path) -> bool:
    """Baixa um arquivo da URL."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        return True
    except Exception as e:
        print(f"  ✗ Falha: {e}")
        return False


def svg_to_png(svg_path: Path, png_path: Path, width: int = 1200) -> bool:
    """Converte SVG para PNG usando cairosvg."""
    try:
        import cairosvg
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(png_path),
            output_width=width,
        )
        return True
    except ImportError:
        print("  ⚠ cairosvg não instalado. Tentando com Pillow...")
        try:
            from PIL import Image
            import io
            # Fallback: salvar SVG como está (não ideal mas funciona)
            # Na prática, precisamos de cairosvg para boa conversão
            print("  ✗ Instale cairosvg: pip install cairosvg")
            return False
        except Exception:
            return False
    except Exception as e:
        print(f"  ✗ Erro na conversão SVG->PNG: {e}")
        return False


def collect_github_diagrams():
    """Coleta diagramas de repositórios GitHub."""
    print("\n📥 Coletando diagramas de GitHub...")
    total = 0

    for provider, urls in GITHUB_DIAGRAMS.items():
        output_dir = IMAGES_DIR / provider
        output_dir.mkdir(parents=True, exist_ok=True)

        for url in urls:
            # Extrair nome do arquivo da URL
            filename = Path(urlparse(url).path).name
            output_path = output_dir / filename

            if output_path.exists():
                print(f"  ⏭ Já existe: {filename}")
                total += 1
                continue

            print(f"  ⬇ Baixando: {filename}")
            if download_file(url, output_path):
                # Verificar se é uma imagem válida
                try:
                    from PIL import Image
                    with Image.open(output_path) as img:
                        w, h = img.size
                        print(f"  ✓ {filename} ({w}x{h})")
                        total += 1
                except Exception:
                    print(f"  ✗ Arquivo inválido, removendo: {filename}")
                    output_path.unlink(missing_ok=True)

            time.sleep(0.5)  # Rate limiting

    print(f"  Total GitHub: {total} imagens")
    return total


def collect_azure_pngs():
    """Coleta PNGs diretos do Azure Architecture Center."""
    print("\n📥 Coletando PNGs do Azure Architecture Center...")
    output_dir = IMAGES_DIR / "azure"
    output_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for url in AZURE_PNG_DIAGRAMS:
        filename = Path(urlparse(url).path).name
        output_path = output_dir / filename

        if output_path.exists():
            print(f"  ⏭ Já existe: {filename}")
            total += 1
            continue

        print(f"  ⬇ Baixando: {filename}")
        if download_file(url, output_path):
            try:
                from PIL import Image
                with Image.open(output_path) as img:
                    w, h = img.size
                    print(f"  ✓ {filename} ({w}x{h})")
                    total += 1
            except Exception:
                print(f"  ✗ Arquivo inválido: {filename}")
                output_path.unlink(missing_ok=True)

        time.sleep(0.5)

    print(f"  Total Azure PNGs: {total} imagens")
    return total


def collect_azure_svgs(skip_svg: bool = False):
    """Coleta e converte diagramas SVG do Azure Architecture Center."""
    if skip_svg:
        print("\n⏭ Pulando diagramas SVG do Azure (--skip-svg)")
        return 0

    print("\n📥 Coletando diagramas SVG do Azure Architecture Center...")
    svg_dir = IMAGES_DIR / "_svg_temp"
    svg_dir.mkdir(parents=True, exist_ok=True)
    output_dir = IMAGES_DIR / "azure"
    output_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for url in AZURE_SVG_DIAGRAMS:
        svg_name = Path(urlparse(url).path).name
        png_name = svg_name.replace(".svg", ".png")
        svg_path = svg_dir / svg_name
        png_path = output_dir / png_name

        if png_path.exists():
            print(f"  ⏭ Já existe: {png_name}")
            total += 1
            continue

        print(f"  ⬇ Baixando: {svg_name}")
        if download_file(url, svg_path):
            print(f"  🔄 Convertendo para PNG: {png_name}")
            if svg_to_png(svg_path, png_path):
                # Validar
                try:
                    from PIL import Image
                    with Image.open(png_path) as img:
                        w, h = img.size
                        print(f"  ✓ {png_name} ({w}x{h})")
                        total += 1
                except Exception:
                    print(f"  ✗ Conversão falhou: {png_name}")
                    png_path.unlink(missing_ok=True)
            else:
                print(f"  ✗ Não foi possível converter: {svg_name}")

        time.sleep(0.5)

    # Limpar temp SVGs
    shutil.rmtree(svg_dir, ignore_errors=True)

    print(f"  Total Azure: {total} imagens")
    return total


def find_local_images(search_dir: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """Encontra imagens locais em um diretório."""
    if extensions is None:
        extensions = [".png", ".jpg", ".jpeg"]

    images = []
    for ext in extensions:
        images.extend(search_dir.rglob(f"*{ext}"))
        images.extend(search_dir.rglob(f"*{ext.upper()}"))

    # Filtrar arquivos temporários e de predição
    images = [
        img for img in images
        if "_svg_temp" not in str(img) and "predictions" not in str(img)
    ]

    return sorted(set(images))


def generate_metadata():
    """Gera arquivo de metadados do dataset."""
    metadata = {
        "version": "2.0.0",
        "created": time.strftime("%Y-%m-%d"),
        "description": "Dataset de diagramas de arquitetura de software para detecção de componentes",
        "sources": [
            "GitHub: arpitbhardwaj/architecture-diagrams (MIT License)",
            "Azure Architecture Center (Microsoft Learn)",
            "Hackathon FIAP - imagens de teste",
        ],
        "images": [],
        "statistics": {
            "total": 0,
            "by_provider": {}
        }
    }

    for provider_dir in sorted(IMAGES_DIR.iterdir()):
        if provider_dir.is_dir() and not provider_dir.name.startswith("_"):
            provider = provider_dir.name
            images = find_local_images(provider_dir)

            metadata["statistics"]["by_provider"][provider] = len(images)
            metadata["statistics"]["total"] += len(images)

            for img in images:
                try:
                    from PIL import Image
                    with Image.open(img) as pil_img:
                        w, h = pil_img.size
                except Exception:
                    w, h = 0, 0

                metadata["images"].append({
                    "file_name": f"{provider}/{img.name}",
                    "provider": provider,
                    "width": w,
                    "height": h,
                    "hash": calculate_hash(img),
                })

    # Salvar
    with open(BASE_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Estatísticas do Dataset:")
    print(f"  Total de imagens: {metadata['statistics']['total']}")
    for provider, count in metadata["statistics"]["by_provider"].items():
        print(f"  - {provider}: {count}")

    return metadata["statistics"]["total"]


def main():
    parser = argparse.ArgumentParser(description="Coleta imagens de arquitetura para dataset YOLO")
    parser.add_argument("--skip-svg", action="store_true", help="Pular download/conversão de SVGs do Azure")
    args = parser.parse_args()

    print("=" * 60)
    print("🏗️  Architecture Diagram Dataset Collector v2.0")
    print("=" * 60)

    # Criar diretórios
    for provider in ["aws", "azure", "gcp", "generic"]:
        (IMAGES_DIR / provider).mkdir(parents=True, exist_ok=True)

    # 1. GitHub diagrams (PNGs diretos)
    github_count = collect_github_diagrams()

    # 2. Azure PNG diagrams (diretos)
    azure_png_count = collect_azure_pngs()

    # 3. Azure SVG diagrams (conversão para PNG)
    azure_count = collect_azure_svgs(skip_svg=args.skip_svg)

    # 4. Gerar metadados
    print("\n📝 Gerando metadados...")
    total = generate_metadata()

    print("\n" + "=" * 60)
    print(f"✅ Coleta finalizada! Total: {total} imagens")
    print("=" * 60)
    print(f"\nPróximos passos:")
    print(f"  1. python auto_annotate.py    # Anotar com Claude Vision")
    print(f"  2. python train_yolo.py       # Treinar modelo YOLO")


if __name__ == "__main__":
    main()
