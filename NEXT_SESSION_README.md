# Next Session: Deploy & Test Wisdom Council on AWS

## Quick Context

**What Was Done (2025-12-18 Evening):**
- ✅ Fixed AWS Terraform target to properly translate @action decorator
- ✅ Delegate action now filtered for supervisors (Bedrock handles it natively)
- ✅ Added bedsheet- prefix to infrastructure resources
- ✅ Fixed resource tagging (agent_resource_tags → tags)
- ✅ Verified with wisdom-council generation (11 files, NO Lambda)

**What's Blocked:**
- Terraform deployment (aws-vault credentials need session restart)
- Debug UI testing (depends on deployment)

## Session Startup Checklist

### 1. Switch to BedsheetAgents Development Branch

```bash
cd /Users/sivan/VitakkaProjects/BedsheetAgents
git status
# Should show: On branch development/v0.4-deploy-anywhere
```

### 2. Verify Latest Changes

```bash
# Check modified files
git diff HEAD~1 bedsheet/deploy/targets/aws.py
git diff HEAD~1 bedsheet/deploy/targets/aws_terraform.py
git diff HEAD~1 bedsheet/deploy/templates/aws-terraform/main.tf.j2

# Should show:
# - Delegate filtering logic in aws.py and aws_terraform.py
# - bedsheet- prefix on IAM resources
# - tags attribute (not agent_resource_tags)
```

### 3. Switch to Wisdom Council Project

```bash
cd /Users/sivan/VitakkaProjects/wisdom-council
```

## Deployment Steps

### Step 1: Terraform Plan

```bash
cd deploy/aws-terraform

# Run plan with aws-vault
aws-vault exec personal -- terraform plan -var-file=terraform.tfvars

# Expected output:
# Plan: X to add, 0 to change, 0 to destroy
#
# Resources to be created:
# - aws_iam_role.agent_role (bedsheet-wisdom_council-dev-agent-role)
# - aws_iam_role_policy.agent_permissions (bedsheet-...)
# - aws_bedrockagent_agent.sage (collaborator)
# - aws_bedrockagent_agent.oracle (collaborator)
# - aws_bedrockagent_agent.supervisor (Judge)
# - aws_bedrockagent_agent_alias.sage
# - aws_bedrockagent_agent_alias.oracle
# - aws_bedrockagent_agent_alias.supervisor
# - aws_bedrockagent_agent_collaborator.sage
# - aws_bedrockagent_agent_collaborator.oracle
#
# NO aws_lambda_function resources (delegate was filtered)
```

**Verification Points:**
- ✅ IAM resources have `bedsheet-` prefix
- ✅ All resources have tags (ManagedBy=Bedsheet)
- ✅ NO Lambda function in plan
- ✅ 3 Bedrock agents (Judge, Sage, Oracle)
- ✅ 2 collaborator resources

### Step 2: Terraform Apply

```bash
aws-vault exec personal -- terraform apply -var-file=terraform.tfvars

# Type 'yes' when prompted
```

**Expected Duration:** 2-3 minutes (Bedrock agent creation is slow)

### Step 3: Capture Outputs

```bash
# Get agent IDs
terraform output supervisor_agent_id
terraform output supervisor_alias_id

# Save for Debug UI
export BEDROCK_AGENT_ID=$(terraform output -raw supervisor_agent_id)
export BEDROCK_AGENT_ALIAS=$(terraform output -raw supervisor_alias_id)

echo "Agent ID: $BEDROCK_AGENT_ID"
echo "Alias ID: $BEDROCK_AGENT_ALIAS"
```

## Testing Steps

### Step 1: Start Debug UI

```bash
cd /Users/sivan/VitakkaProjects/wisdom-council/deploy/aws-terraform

# Use environment variables from previous step
AWS_REGION=eu-central-1 \
BEDROCK_AGENT_ID=$BEDROCK_AGENT_ID \
BEDROCK_AGENT_ALIAS=$BEDROCK_AGENT_ALIAS \
aws-vault exec personal -- python debug-ui/server.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Open Debug UI

Open browser: http://localhost:8000

### Step 3: Test Multi-Agent Collaboration

**Test Case 1: Simple Question**
```
Input: "What is the meaning of life?"

Expected Trace:
1. Judge (supervisor) receives question
2. Judge invokes Sage via Bedrock native delegation
3. Judge invokes Oracle via Bedrock native delegation
4. Judge synthesizes responses
5. Final answer returned

CRITICAL: Should see collaborator_start/collaborator_complete events
NO Lambda invocations for delegate
```

**Test Case 2: Follow-up Question**
```
Input: "Can you elaborate on that answer?"

Expected: Conversation history maintained across turns
```

### Step 4: Verify Resource Tags

```bash
# List all Bedsheet-managed resources
aws-vault exec personal -- aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=ManagedBy,Values=Bedsheet \
  --region eu-central-1 \
  --output table

# Should show:
# - IAM roles
# - Bedrock agents (Judge, Sage, Oracle)
# All tagged with ManagedBy=Bedsheet
```

### Step 5: Verify IAM Resource Naming

```bash
# List IAM roles with bedsheet- prefix
aws-vault exec personal -- aws iam list-roles \
  --query "Roles[?starts_with(RoleName, 'bedsheet-')].RoleName" \
  --output table

# Expected:
# - bedsheet-wisdom_council-dev-agent-role
```

## Success Criteria

- ✅ Terraform apply succeeds without errors
- ✅ 3 Bedrock agents created (Judge, Sage, Oracle)
- ✅ Debug UI starts successfully
- ✅ Multi-agent conversation works end-to-end
- ✅ Traces show Bedrock native collaboration (NOT Lambda delegate)
- ✅ Resources properly tagged with ManagedBy=Bedsheet
- ✅ IAM resources have bedsheet- prefix

## If Successful, Add to Examples

```bash
# From BedsheetAgents repo
cd /Users/sivan/VitakkaProjects/BedsheetAgents
mkdir -p examples
cp -r /Users/sivan/VitakkaProjects/wisdom-council examples/

# Create example README
cat > examples/wisdom-council/README.md << 'EOF'
# Wisdom Council - Multi-Agent AWS Deployment Example

This example demonstrates deploying a multi-agent Bedsheet system to AWS Bedrock using Terraform.

## Architecture

- **Judge** (Supervisor): Orchestrates collaboration between Sage and Oracle
- **Sage** (Collaborator): Provides philosophical insights
- **Oracle** (Collaborator): Offers prophetic wisdom

## Deployment

See `deploy/aws-terraform/` for full deployment configuration.

## Key Features

- Native Bedrock multi-agent collaboration (no Lambda delegate)
- Terraform workspace support (dev/staging/production)
- Resource tagging for governance
- Debug UI for testing
EOF

# Commit
cd /Users/sivan/VitakkaProjects/BedsheetAgents
git add examples/wisdom-council
git commit -m "docs: add wisdom-council multi-agent AWS example"
```

## Troubleshooting

### Issue: aws-vault credentials fail

**Error:** `aws-vault: error: exec: Failed to get credentials`

**Solution:**
```bash
# Clear aws-vault cache
aws-vault clear

# Try again
aws-vault exec personal -- terraform plan
```

### Issue: Bedrock agent creation fails

**Error:** `Error creating Bedrock Agent: AccessDeniedException`

**Check:**
```bash
# Verify Bedrock permissions
aws-vault exec personal -- aws bedrock list-foundation-models --region eu-central-1

# Should list available models
```

### Issue: Debug UI can't connect to agent

**Error:** `Error invoking agent: AgentNotFoundException`

**Check:**
```bash
# Verify agent exists
aws-vault exec personal -- aws bedrock-agent get-agent \
  --agent-id $BEDROCK_AGENT_ID \
  --region eu-central-1
```

## Files to Reference

- **Session Notes:** `/Users/sivan/VitakkaProjects/wisdom-council/SESSION_NOTES_2025-12-18.md`
- **Project Status:** `/Users/sivan/VitakkaProjects/BedsheetAgents/PROJECT_STATUS.md`
- **Plan Document:** `/Users/sivan/.claude/plans/drifting-baking-swing.md`

## Context for Next Session

When you start the next session, you can say:

> "Continue from the last session. I'm ready to deploy wisdom-council to AWS and test the multi-agent collaboration. The delegate action filtering is complete and verified. Let's start with terraform plan."

The AI will have full context from:
1. PROJECT_STATUS.md - Overall project history
2. SESSION_NOTES_2025-12-18.md - Detailed session work
3. This README - Step-by-step deployment guide
