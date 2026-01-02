# Wisdom Council

![Digital Souls & Personas](DIGITAL%20SOULS%20&%20PERSONAS.png)

A multi-agent AI system that provides balanced, thoughtful advice by coordinating multiple AI advisors with different perspectives.

## Overview

Wisdom Council implements a "council of advisors" pattern where a **Judge** (supervisor agent) coordinates two specialist agents:

- **Sage** - A contemplative philosopher offering deep wisdom, historical perspective, and ethical reflection
- **Oracle** - A pragmatic advisor providing actionable steps, concrete strategies, and practical guidance

When you ask a question, the Judge:
1. Consults both Sage and Oracle simultaneously for their perspectives
2. Has each advisor rate the other's response (1-10 with reasoning)
3. Synthesizes the perspectives into balanced, actionable guidance

## Architecture

```
                    ┌─────────────┐
                    │    User     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Judge    │
                    │ (Supervisor)│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │                         │
       ┌──────▼──────┐           ┌──────▼──────┐
       │    Sage     │           │   Oracle    │
       │ (Philosopher)│           │ (Pragmatist)│
       └─────────────┘           └─────────────┘
```

## Prerequisites

- Python 3.11+
- AWS Account with Bedrock access enabled
- AWS CLI configured with appropriate credentials
- Terraform >= 1.0.0 (for Terraform deployment)
- Access to Claude models in AWS Bedrock (eu-central-1 region)

## Installation

### Local Development

```bash
# Clone the repository
git clone https://github.com/sivang/wisdom-council.git
cd wisdom-council

# Install bedsheet (the agent framework)
pip install bedsheet
```

## Deployment to AWS Bedrock

The project supports deployment via Terraform to AWS Bedrock Agents.

### Prerequisites

```bash
# Install required tools
brew install awscli
brew install terraform

# Configure AWS credentials
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region (eu-central-1)

# Verify authentication
aws sts get-caller-identity
```

Required AWS permissions:
- Bedrock full access (for agents and model invocation)
- IAM (for creating agent roles)
- Lambda (for action group functions)
- CloudWatch Logs (for agent logging)

Enable Claude models in your region:
1. Go to AWS Console → Amazon Bedrock → Model access
2. Request access to Anthropic Claude models
3. Wait for approval (usually instant for Claude Sonnet)

### Quick Start

```bash
cd deploy/aws-terraform

# Initialize Terraform
make init

# Create/switch to dev workspace
make workspace-dev

# Review the deployment plan
make plan

# Deploy to AWS
make deploy
```

### Configuration

Copy and customize the variables file:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
project_name  = "wisdom_council"
region        = "eu-central-1"
bedrock_model = "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
```

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make init` | Initialize Terraform |
| `make workspace-dev` | Switch to dev workspace |
| `make workspace-staging` | Switch to staging workspace |
| `make workspace-prod` | Switch to production workspace |
| `make plan` | Preview infrastructure changes |
| `make deploy` | Deploy to AWS |
| `make destroy` | Destroy all resources |
| `make outputs` | Show deployment outputs |

### After Deployment

1. Set environment variables from Terraform outputs:

```bash
export BEDROCK_AGENT_ID=$(terraform output -raw supervisor_agent_id)
export BEDROCK_AGENT_ALIAS=$(terraform output -raw supervisor_alias_id)
export AWS_REGION=eu-central-1
```

2. Start the Debug UI:

```bash
python debug-ui/server.py
```

3. Open http://localhost:8080 in your browser

## Project Structure

```
wisdom-council/
├── agents/
│   ├── judge.py      # Supervisor agent - coordinates Sage and Oracle
│   ├── sage.py       # Philosopher agent - wisdom and ethics
│   └── oracle.py     # Pragmatist agent - practical advice
├── deploy/
│   ├── aws-terraform/
│   │   ├── main.tf           # Main Terraform configuration
│   │   ├── variables.tf      # Input variables
│   │   ├── outputs.tf        # Output values
│   │   ├── terraform.tfvars  # Your configuration (gitignored)
│   │   ├── Makefile          # Deployment commands
│   │   ├── lambda/           # Lambda function for agent actions
│   │   ├── schemas/          # OpenAPI schemas for action groups
│   │   └── debug-ui/         # Local testing UI
│   └── gcp/                  # Generated via: bedsheet generate --target gcp
│       ├── agent/            # ADK-compatible agent code
│       ├── terraform/        # Cloud Run infrastructure
│       ├── Dockerfile
│       ├── Makefile
│       └── cloudbuild.yaml
├── bedsheet.yaml     # Agent framework configuration
└── README.md
```

## Usage Example

Once deployed, you can ask the Wisdom Council questions like:

> "Should I take a job offer that pays more but requires relocating away from family?"

The Judge will:
1. Get Sage's philosophical perspective on work-life balance, family values, and long-term fulfillment
2. Get Oracle's practical analysis of financial implications, career trajectory, and actionable considerations
3. Have each rate the other's response
4. Synthesize a balanced recommendation

## AWS Resources Created

The Terraform deployment creates:

- **IAM Roles** - For Bedrock agents and Lambda execution
- **Bedrock Agents** - Sage, Oracle, and Judge (supervisor)
- **Agent Aliases** - "live" aliases for each agent
- **Lambda Function** - For action group execution
- **Lambda Permissions** - Allow Bedrock to invoke Lambda

## Cleanup

To destroy all AWS resources:

```bash
cd deploy/aws-terraform
make destroy
```

---

## Deployment to GCP Cloud Run

The project can also be deployed to Google Cloud Run via Terraform. This section guides you through using the bedsheet CLI to generate and deploy the GCP target.

### Prerequisites

```bash
# Install required tools
brew install terraform
brew install google-cloud-sdk

# Authenticate
gcloud auth login
gcloud auth application-default login

# Set your project
gcloud config set project your-gcp-project-id
```

Required GCP APIs:
- Cloud Run Admin API
- Secret Manager API
- IAM API
- Cloud Build API (optional, for CI/CD)

### Step 1: Add GCP Target Configuration

Add the `gcp` target to your `bedsheet.yaml`:

```yaml
targets:
  # ... existing aws/aws-terraform targets ...
  gcp:
    project: your-gcp-project-id
    region: europe-west1
    cloud_run_memory: 512Mi
    model: gemini-2.5-flash  # Or claude-sonnet-4-5@20250929 for Vertex AI Claude
```

### Step 2: Generate GCP Deployment Artifacts

```bash
# Validate configuration first
bedsheet validate

# Generate GCP deployment files
bedsheet generate --target gcp
```

This creates `deploy/gcp/` with:
- `agent/` - ADK-compatible agent code
- `terraform/` - Infrastructure as Code (Cloud Run, IAM, Secrets)
- `Dockerfile` - Container image definition
- `cloudbuild.yaml` - Cloud Build configuration
- `Makefile` - Deployment commands
- `.github/workflows/` - CI/CD workflows

### Step 3: Deploy to GCP

```bash
cd deploy/gcp

# Configure your settings
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your GCP project details

# Initialize and deploy
make tf-init
make tf-plan    # Review the changes
make tf-apply   # Deploy!
```

### GCP Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make setup` | Install dependencies (google-adk, bedsheet) |
| `make dev-ui-local` | Run ADK Dev UI locally (http://localhost:8000) |
| `make test` | Test agent locally with ADK |
| `make build` | Build Docker image |
| `make deploy` | Deploy via Cloud Build (quick) |
| `make deploy-terraform` | Deploy via Terraform (full IaC) |
| `make tf-init` | Initialize Terraform |
| `make tf-plan` | Plan infrastructure changes |
| `make tf-apply` | Apply infrastructure changes |
| `make tf-destroy` | Destroy all GCP resources |
| `make logs` | View Cloud Run logs |

### ADK Dev UI

The Google Agent Development Kit includes a development UI for testing:

```bash
# Local development (requires GOOGLE_API_KEY for Gemini)
make dev-ui-local

# Or deploy a dev instance to Cloud Run
make dev-ui
```

The Dev UI provides:
- Chat interface for agent testing
- Execution trace visualization
- State inspector
- Evaluation tools

For more details, see the [Bedsheet Deployment Guide](https://sivang.github.io/bedsheet/deployment-guide.html).

---

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.
