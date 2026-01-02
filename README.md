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
│   └── aws-terraform/
│       ├── main.tf           # Main Terraform configuration
│       ├── variables.tf      # Input variables
│       ├── outputs.tf        # Output values
│       ├── terraform.tfvars  # Your configuration (gitignored)
│       ├── Makefile          # Deployment commands
│       ├── lambda/           # Lambda function for agent actions
│       ├── schemas/          # OpenAPI schemas for action groups
│       └── debug-ui/         # Local testing UI
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

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.
