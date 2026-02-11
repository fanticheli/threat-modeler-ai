# Backlog - Estratégia Multicloud

## Objetivo
Tornar o Threat Modeler AI capaz de rodar em múltiplos provedores de cloud (AWS, GCP, Azure) com redundância, alta disponibilidade e sem vendor lock-in.

---

## Fase 1: Containerização e Portabilidade

| ID | Tarefa | Prioridade | Complexidade |
|----|--------|------------|--------------|
| MC-001 | Criar Dockerfile otimizado para produção (multi-stage build) | Alta | Baixa |
| MC-002 | Criar docker-compose para ambiente local completo | Alta | Baixa |
| MC-003 | Parametrizar todas as configurações via variáveis de ambiente | Alta | Baixa |
| MC-004 | Remover dependências hard-coded de serviços específicos | Alta | Média |
| MC-005 | Criar health checks padronizados (/health, /ready) | Alta | Baixa |

---

## Fase 2: Infraestrutura como Código (IaC)

| ID | Tarefa | Prioridade | Complexidade |
|----|--------|------------|--------------|
| MC-006 | Criar módulos Terraform para AWS (ECS/EKS, RDS, ElastiCache) | Alta | Alta |
| MC-007 | Criar módulos Terraform para GCP (Cloud Run, Cloud SQL, Memorystore) | Média | Alta |
| MC-008 | Criar módulos Terraform para Azure (AKS, CosmosDB, Azure Cache) | Média | Alta |
| MC-009 | Criar Helm Charts para Kubernetes | Alta | Média |
| MC-010 | Configurar Terraform Cloud/Atlantis para GitOps | Média | Média |

---

## Fase 3: Abstração de Serviços

| ID | Tarefa | Prioridade | Complexidade |
|----|--------|------------|--------------|
| MC-011 | Criar interface abstrata para Storage (S3/GCS/Azure Blob) | Alta | Média |
| MC-012 | Criar interface abstrata para Queue (SQS/Pub-Sub/Service Bus) | Média | Média |
| MC-013 | Criar interface abstrata para Cache (ElastiCache/Memorystore/Azure Cache) | Média | Média |
| MC-014 | Implementar adapter pattern para troca de providers | Alta | Média |
| MC-015 | Usar MongoDB Atlas (já cloud-agnostic) ou criar abstração DB | Baixa | Alta |

---

## Fase 4: CI/CD Multicloud

| ID | Tarefa | Prioridade | Complexidade |
|----|--------|------------|--------------|
| MC-016 | Configurar GitHub Actions para build de imagens Docker | Alta | Baixa |
| MC-017 | Push automático para ECR (AWS), GCR (GCP), ACR (Azure) | Alta | Média |
| MC-018 | Deploy automático para ambiente de staging em cada cloud | Média | Alta |
| MC-019 | Implementar feature flags para rollout gradual | Média | Média |
| MC-020 | Configurar matriz de testes em múltiplos ambientes | Média | Média |

---

## Fase 5: Observabilidade Centralizada

| ID | Tarefa | Prioridade | Complexidade |
|----|--------|------------|--------------|
| MC-021 | Implementar OpenTelemetry para traces distribuídos | Alta | Média |
| MC-022 | Centralizar logs com formato estruturado (JSON) | Alta | Baixa |
| MC-023 | Configurar Grafana Cloud ou Datadog (cloud-agnostic) | Média | Média |
| MC-024 | Criar dashboards unificados para todas as clouds | Média | Média |
| MC-025 | Configurar alertas centralizados | Média | Baixa |

---

## Fase 6: Rede e DNS

| ID | Tarefa | Prioridade | Complexidade |
|----|--------|------------|--------------|
| MC-026 | Configurar Cloudflare como DNS/CDN global | Alta | Baixa |
| MC-027 | Implementar load balancing entre clouds (Cloudflare LB) | Alta | Média |
| MC-028 | Configurar failover automático entre regiões | Alta | Alta |
| MC-029 | Implementar GeoDNS para roteamento por latência | Média | Média |
| MC-030 | Configurar mTLS entre serviços | Média | Alta |

---

## Fase 7: Dados e Sincronização

| ID | Tarefa | Prioridade | Complexidade |
|----|--------|------------|--------------|
| MC-031 | Configurar MongoDB Atlas multi-region | Alta | Média |
| MC-032 | Implementar estratégia de backup cross-cloud | Alta | Média |
| MC-033 | Configurar replicação de arquivos entre clouds | Média | Alta |
| MC-034 | Implementar cache distribuído (Redis Cluster) | Média | Alta |
| MC-035 | Definir estratégia de consistência eventual | Média | Alta |

---

## Fase 8: Segurança Multicloud

| ID | Tarefa | Prioridade | Complexidade |
|----|--------|------------|--------------|
| MC-036 | Centralizar secrets com HashiCorp Vault | Alta | Média |
| MC-037 | Implementar OIDC federation entre clouds | Média | Alta |
| MC-038 | Configurar policies de IAM consistentes | Alta | Média |
| MC-039 | Implementar audit logging centralizado | Média | Média |
| MC-040 | Configurar scanning de vulnerabilidades nas imagens | Alta | Baixa |

---

## Arquitetura Alvo

```
                        ┌─────────────────┐
                        │   Cloudflare    │
                        │   (DNS + CDN)   │
                        └────────┬────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
            ▼                    ▼                    ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │     AWS       │   │     GCP       │   │    Azure      │
    │  ┌─────────┐  │   │  ┌─────────┐  │   │  ┌─────────┐  │
    │  │ EKS/ECS │  │   │  │Cloud Run│  │   │  │   AKS   │  │
    │  └────┬────┘  │   │  └────┬────┘  │   │  └────┬────┘  │
    │       │       │   │       │       │   │       │       │
    │  ┌────┴────┐  │   │  ┌────┴────┐  │   │  ┌────┴────┐  │
    │  │ ElastiC │  │   │  │MemStore│  │   │  │Az Cache │  │
    │  └─────────┘  │   │  └─────────┘  │   │  └─────────┘  │
    └───────────────┘   └───────────────┘   └───────────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                        ┌────────┴────────┐
                        │  MongoDB Atlas  │
                        │  (Multi-Region) │
                        └─────────────────┘
```

---

## Estimativas por Fase

| Fase | Descrição | Esforço |
|------|-----------|---------|
| 1 | Containerização | 1-2 sprints |
| 2 | IaC | 3-4 sprints |
| 3 | Abstração | 2-3 sprints |
| 4 | CI/CD | 2 sprints |
| 5 | Observabilidade | 2 sprints |
| 6 | Rede | 2-3 sprints |
| 7 | Dados | 3-4 sprints |
| 8 | Segurança | 2-3 sprints |

**Total estimado:** 17-23 sprints (~4-6 meses com 1 dev)

---

## Quick Wins (Começar por aqui)

1. ✅ MongoDB Atlas (já está)
2. ✅ Redis Upstash (já está, cloud-agnostic)
3. [ ] MC-001: Dockerfile otimizado
4. [ ] MC-005: Health checks
5. [ ] MC-021: OpenTelemetry básico
6. [ ] MC-026: Cloudflare DNS

---

## Referências

- [12 Factor App](https://12factor.net/)
- [Cloud Native Computing Foundation](https://www.cncf.io/)
- [Terraform Multi-Cloud](https://developer.hashicorp.com/terraform/tutorials/aws-get-started)
