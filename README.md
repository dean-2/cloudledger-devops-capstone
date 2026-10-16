# CloudLedger — FinOps & Cloud Infrastructure Cost-Auditing SaaS Platform

CloudLedger is a full-stack FinOps & Cloud Infrastructure Cost-Auditing platform built for the **Session 21 DevOps Final Capstone Project**. Engineering and SRE teams use CloudLedger to audit multi-cloud (`AWS`, `GCP`, `Azure`) monthly burn, identify idle zombie assets and over-provisioned resources, and track real-time optimization health.

> 🔗 **Project Submission Links:**
> - **GitHub Repository:** [https://github.com/dean-2/cloudledger-devops-capstone](https://github.com/dean-2/cloudledger-devops-capstone)
> - **Google Drive (PPTX Deck + 2-Min Demo Video):** [Click Here to View Presentation & Demo Video](<https://drive.google.com/drive/folders/1TW8LhFoOcBjlBjoZU-I17uM1dmLRPFBU?usp=sharing>)

---

## 1. System Architecture

| Layer | Technology Stack | Key Features |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite 5, Nginx 1.27 (`alpine`) | FinOps KPI cards, multi-cloud filters, audit ledger, non-root multi-stage container (`USER nginx`) |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2, Alembic | 6 REST CRUD + aggregation endpoints, `/health`, `/ready`, `/metrics`, non-root container (`USER appuser`) |
| **Database** | PostgreSQL 15 (`alpine`) + SQLite (Tests) | `cloud_resources` schema managed via Alembic (`0001_create_cloud_resources.py`) + auto-seeding |
| **CI/CD & DevSecOps** | GitHub Actions, GHCR, Aqua Trivy | Automated Pytest + Vite build, Trivy `HIGH`/`CRITICAL` gate (`exit-code: 1`), SHA-tagged GHCR images |
| **Cloud IaC** | Terraform (`>= 1.5`, AWS Provider `~> 5.50`) | Custom VPC (`10.20.0.0/16`), 2 Public + 2 Private Subnets, NAT Gateway, EKS 1.30 Managed Node Group in `ap-south-1` |
| **Orchestration** | Kubernetes (EKS / Kind), Helm 3, Ingress, HPA | 2x Backend & 2x Frontend replicas, PostgreSQL PVC, Ingress `/api` & `/` routing, CPU-based HPA |
| **Observability** | Prometheus & Grafana (`kube-prometheus-stack`) | `prometheus-fastapi-instrumentator` on `/metrics`, `ServiceMonitor` 15s scrape, live Grafana dashboards |

---

## 2. Repository Structure

```text
cloudledger-devops-capstone/
├── frontend/                 # React + Vite FinOps UI, multi-stage Dockerfile, nginx.conf
├── backend/                  # FastAPI API, SQLAlchemy models, Alembic migrations, Pytest suite
├── docker-compose.yml        # Local 3-tier orchestration (frontend, backend, postgres)
├── terraform/                # AWS VPC + EKS infrastructure in ap-south-1
├── helm/cloudledger/         # Production Helm chart (Deployments, Services, Ingress, HPA, PVC)
├── k8s/                      # Namespace bootstrap manifest (cloudledger)
├── monitoring/               # Prometheus & Grafana Helm values and ServiceMonitor
├── troubleshooting/          # Deliberately broken manifests for live K8s debugging demo
├── scripts/                  # Concurrent HTTP load generator for HPA scaling verification
├── deliverables/             # M1.md – M10.md rubric checklists, commands, and screenshot guides
└── .github/workflows/        # CI/CD + Trivy DevSecOps pipeline (ci-cd.yml)
```

---

## 3. Quick Start: Local Development (`docker compose`)

```bash
# Build and launch PostgreSQL, FastAPI Backend, and React/Nginx Frontend
docker compose up --build -d

# Access endpoints:
# FinOps Dashboard UI:   http://localhost:3000
# FastAPI Swagger Docs:  http://localhost:8000/docs
# Liveness & Readiness:  http://localhost:8000/health | http://localhost:8000/ready
# Prometheus Metrics:    http://localhost:8000/metrics
```

---

## 4. Running the Isolated Automated Test Suite (`pytest`)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

All 6 test cases in `backend/tests/test_api.py` use an isolated in-memory SQLite database (`sqlite:///:memory:`) configured in `backend/conftest.py`.

---

## 5. CI/CD Pipeline & Trivy DevSecOps Scanning

On every push to `main`, `.github/workflows/ci-cd.yml` runs two sequential jobs:
1. **`test-and-build-check`**: Runs the 6 isolated `pytest` tests and compiles the React + Vite production bundle (`npm run build`).
2. **`docker-trivy-and-publish`**: Builds `cloudledger-backend` (`python:3.12-slim`) and `cloudledger-frontend` (`nginx:1.27-alpine`), scans both images with **Aqua Trivy** (`severity: CRITICAL,HIGH`, `exit-code: 1`), and pushes immutable Git SHA-tagged images (`:${{ github.sha }}`) to GitHub Container Registry (`ghcr.io/dean-2/cloudledger-backend` & `ghcr.io/dean-2/cloudledger-frontend`).

---

## 6. Provisioning AWS VPC & EKS with Terraform (`ap-south-1`)

> **Cloud Environment Notice:** If running in an organizational AWS account with a Service Control Policy (SCP) explicit deny on VPC/EC2 creation, validate locally via `terraform init`, `terraform fmt -check`, and `terraform validate`, and deploy Kubernetes manifests to a local **Kind** cluster (`kind create cluster --name cloudledger-cluster`).

```bash
cd terraform
terraform init
terraform fmt -check
terraform validate

# For unrestricted AWS environments:
terraform plan -out=tfplan
terraform apply tfplan
aws eks update-kubeconfig --region ap-south-1 --name cloudledger-eks-cluster
```

> **Cost Safety Reminder:** Always tear down AWS EKS and NAT Gateway resources immediately after verification:
> ```bash
> terraform destroy -auto-approve
> ```

---

## 7. Deploying with Kubernetes & Helm

```bash
kubectl apply -f k8s/namespace.yaml

helm upgrade --install cloudledger ./helm/cloudledger \
  --namespace cloudledger \
  --set backend.image.repository=ghcr.io/dean-2/cloudledger-backend \
  --set backend.image.tag=f491be481f6358680a26f59556423ed437bf9953 \
  --set frontend.image.repository=ghcr.io/dean-2/cloudledger-frontend \
  --set frontend.image.tag=f491be481f6358680a26f59556423ed437bf9953

kubectl get pods,svc,ingress,hpa -n cloudledger
```

---

## 8. Observability: Prometheus & Grafana

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f monitoring/kube-prometheus-values.yaml

kubectl apply -f monitoring/servicemonitor.yaml
```

---

## 9. HPA Scaling & Kubernetes Troubleshooting

- **HorizontalPodAutoscaler (`helm/cloudledger/templates/hpa.yaml`):** Scales `cloudledger-backend` between `2` and `5` replicas at `70%` CPU utilization. Load can be generated using `./scripts/load-test.sh http://localhost:8000/api/resources/stats 60`.
- **Scenario 1 — `troubleshooting/broken-image.yaml` (`ImagePullBackOff`):** Deploys a pod with a non-existent image tag (`:non-existent-broken-tag-999`). Diagnose with `kubectl describe pod -n cloudledger -l app=cloudledger-broken-worker` and remediate live via `kubectl set image`.
- **Scenario 2 — `troubleshooting/broken-service.yaml` (`0 Endpoints`):** Deploys a service with a mismatched selector (`app: cloudledger-backend-typo-selector`). Diagnose via `kubectl get endpoints cloudledger-broken-svc -n cloudledger` (`<none>`) and remediate live via `kubectl patch svc`.

---

## 10. Module Deliverables Index (`deliverables/`)

- [M1 — Application: Frontend + Backend + Database](./deliverables/M1.md)
- [M2 — Testing: Pytest + Code Quality](./deliverables/M2.md)
- [M3 — Git and GitHub](./deliverables/M3.md)
- [M4 — Docker: Dockerfile + Compose](./deliverables/M4.md)
- [M5 — CI/CD: GitHub Actions Pipeline](./deliverables/M5.md)
- [M6 — DevSecOps: Trivy Security Scan](./deliverables/M6.md)
- [M7 — Terraform: AWS Infrastructure as Code](./deliverables/M7.md)
- [M8 — Kubernetes + Helm](./deliverables/M8.md)
- [M9 — Observability: Prometheus + Grafana](./deliverables/M9.md)
- [M10 — Final Presentation + Live Demo Guide](./deliverables/M10.md)