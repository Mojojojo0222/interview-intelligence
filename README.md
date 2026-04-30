# AI Interview Intelligence System

An enterprise-grade multi-agent system that conducts technical interviews for DevOps/Cloud/SRE roles, detects AI-assisted answers, and generates adaptive follow-up questions that LLMs cannot predict.

## Architecture

```
User → CloudFront → ALB → EKS (interview-service + frontend + ollama)
                              ↓
                         AWS RDS (future) | S3 (reports) | ECR (images)
                              ↓
                    Prometheus + Grafana + CloudWatch
```

## Agents

| Agent | Role |
|---|---|
| Planner | Creates structured interview plan |
| Question Generator | Generates targeted technical questions |
| Answer Analyzer | Scores depth, specificity, authenticity |
| AI Detector | Detects LLM-generated answer patterns |
| Domain Expert | Validates DevOps/AWS/SRE accuracy |
| Adaptive Questioner | Generates unpredictable follow-ups |
| Report Generator | Final hire/no-hire report |

## Quick Start (Local)

### Prerequisites
- Docker + Docker Compose
- 8GB RAM minimum

```bash
git clone https://github.com/<your-username>/interview-intelligence.git
cd interview-intelligence
docker-compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

> First run will pull `llama3.2:3b` (~2GB). Wait for ollama-init to complete.

## Deploy to AWS

### 1. Prerequisites
```bash
# Install tools
aws configure          # set your AWS credentials
terraform init         # in /terraform folder
```

### 2. Provision Infrastructure
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This creates: VPC, EKS cluster, ECR repos, S3 bucket.

### 3. GitHub Secrets Required
Go to your repo → Settings → Secrets → Actions and add:

| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | Your AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key |
| `AWS_ACCOUNT_ID` | Your 12-digit AWS account ID |

### 4. Push to Deploy
```bash
git push origin main
# GitHub Actions will: test → build → push to ECR → deploy to EKS
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/interview/start` | Start new interview session |
| POST | `/interview/answer` | Submit answer for analysis |
| POST | `/interview/report` | Generate final report |
| GET | `/interview/session/{id}` | Get session data |
| GET | `/health` | Health check |

## Project Structure

```
├── .github/workflows/    # CI/CD pipelines
├── services/
│   ├── interview-service/ # FastAPI + CrewAI orchestration
│   └── agent-service/     # 7 AI agents + tasks + tools
├── frontend/              # React UI
├── k8s/                   # Kubernetes manifests
├── terraform/             # AWS infrastructure as code
├── monitoring/            # Prometheus + Grafana configs
└── docker-compose.yml     # Local development
```

## Tech Stack

- **AI**: CrewAI + Ollama (llama3.2:3b)
- **Backend**: FastAPI (Python 3.12)
- **Frontend**: React 18
- **Containers**: Docker
- **Orchestration**: Kubernetes (AWS EKS)
- **IaC**: Terraform
- **CI/CD**: GitHub Actions
- **Registry**: AWS ECR
- **Monitoring**: Prometheus + Grafana + CloudWatch
