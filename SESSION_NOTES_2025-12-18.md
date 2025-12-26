# Wisdom Council - Session Notes (2025-12-18 Evening)

## Session Objective

Fix AWS Terraform deployment to properly translate Bedsheet's `@action` decorator for multi-agent scenarios, matching the user's original intent: "translate the @action decorator of bedsheet to the implementation in AWS, just as it does for GCP."

## Problem Statement

The AWS target was blindly translating ALL @actions (including the auto-registered `delegate` action) to Lambda functions and OpenAPI endpoints. This is incorrect for multi-agent supervisors because:

1. **Bedrock has native collaboration**: AWS Bedrock uses `aws_bedrockagent_agent_collaborator` resources for supervisor-to-collaborator delegation
2. **The `delegate` action is redundant**: When a Supervisor has collaborators, Bedrock handles delegation automatically - no Lambda tool needed
3. **User explicitly requested translation**: "Just as GCP does" - GCP translates @actions to platform idioms (ADK tool stubs), AWS should translate by filtering delegate for supervisors

## Root Cause

1. **Supervisor auto-registers delegate** (`Supervisor.__init__()` calls `_register_delegate_action()`)
2. **Introspection extracts ALL tools** (including the auto-registered delegate action)
3. **Templates blindly generate Lambda** for ALL tools without platform-specific filtering
4. **Result**: Redundant delegate Lambda + OpenAPI endpoint that conflicts with Bedrock's native collaboration

## Solution Implemented

### 1. Filter Delegate Action BEFORE Creating Template Context

**Files Modified:**
- `bedsheet/deploy/targets/aws.py:40-51`
- `bedsheet/deploy/targets/aws_terraform.py:40-48`

**Code Change:**
```python
# For Supervisors with collaborators, filter out the 'delegate' tool from agent metadata
# since Bedrock handles delegation natively via aws_bedrockagent_agent_collaborator
filtered_agent = agent_metadata
if agent_metadata.is_supervisor and agent_metadata.collaborators:
    filtered_tools = [
        tool for tool in agent_metadata.tools
        if tool.name != "delegate"
    ]
    filtered_agent = replace(agent_metadata, tools=filtered_tools)

context = {
    "config": config,
    "aws": aws_config,
    "agent": filtered_agent,  # Use filtered_agent, not agent_metadata
    "project_name": config.name.replace("-", "_").replace(" ", "_"),
}
```

**Impact:**
- ALL templates (main.tf, openapi.yaml, lambda handler) receive filtered agent metadata
- NO Lambda files generated when only delegate tool exists
- NO OpenAPI `/delegate` endpoint

### 2. Add bedsheet- Prefix to Infrastructure Resources

**File Modified:**
- `bedsheet/deploy/templates/aws-terraform/main.tf.j2:40, 71`

**Changes:**
- IAM roles: `bedsheet-${local.name_prefix}-agent-role`
- IAM policies: `bedsheet-${local.name_prefix}-agent-permissions`
- Lambda functions: `bedsheet-${local.name_prefix}-actions` (when generated)
- Bedrock agents: Keep `${local.name_prefix}` (user-facing, no prefix)
- Agent aliases: Keep `live` (user-facing, no prefix)

**Benefits:**
- Alphabetical grouping in AWS console
- Easy CLI filtering: `aws iam list-roles --query "Roles[?starts_with(RoleName, 'bedsheet-')]"`
- Clear provenance and easier resource management

### 3. Fix Resource Tagging

**File Modified:**
- `bedsheet/deploy/templates/aws-terraform/main.tf.j2:195-201, 226-232, 296-302`

**Change:** `agent_resource_tags` → `tags` (correct Terraform attribute)

**Tags Applied to ALL Resources:**
```terraform
tags = {
  ManagedBy       = "Bedsheet"
  BedsheetVersion = "0.4.0"
  Project         = var.project_name
  Environment     = local.workspace
  AgentType       = "Supervisor|Collaborator|SingleAgent"  # For Bedrock agents
}
```

**Taggable Resources:**
- IAM roles (agent_role, lambda_role)
- Lambda functions
- Bedrock agents (all: supervisor, collaborators, single agents)

**Non-taggable:** IAM policies, agent aliases (Terraform limitation)

## Verification Results

### Generated Files (wisdom-council/deploy/aws-terraform/)

✅ **11 files total** (NO lambda directory):
- main.tf
- variables.tf
- outputs.tf
- terraform.tfvars.example
- pyproject.toml
- Makefile
- .env.example
- schemas/openapi.yaml
- .github/workflows/ci.yaml
- .github/workflows/deploy.yaml
- debug-ui/server.py

### openapi.yaml Verification

```yaml
paths:
  /health:
    get:
      summary: "Health check"
      operationId: "health"
      responses:
        "200":
          description: "OK"
```

✅ Only `/health` endpoint
✅ NO `/delegate` endpoint

### main.tf Verification

✅ NO Lambda resource definitions
✅ IAM resources have `bedsheet-` prefix:
  - `bedsheet-${local.name_prefix}-agent-role`
  - `bedsheet-${local.name_prefix}-agent-permissions`
✅ Bedrock agents use correct `tags` attribute (not `agent_resource_tags`)
✅ 4 occurrences of `ManagedBy = "Bedsheet"` tags

### Lambda Directory Check

```bash
$ ls -la deploy/aws-terraform/ | grep lambda
# (no output - lambda directory does not exist)
```

✅ Confirmed NO lambda/ directory or files

## Testing Blocked

**Issue:** AWS credentials not loading in current session
**Error:** `aws-vault: error: exec: Failed to get credentials for personal`

**Reason:** Session needs restart for aws-vault to refresh credentials properly

## Next Steps (For Next Session)

### 1. Deploy with Terraform

```bash
cd /Users/sivan/VitakkaProjects/wisdom-council/deploy/aws-terraform
aws-vault exec personal -- terraform plan -var-file=terraform.tfvars
aws-vault exec personal -- terraform apply -var-file=terraform.tfvars
```

**Expected Result:**
- 3 Bedrock agents created: Judge (supervisor), Sage, Oracle (collaborators)
- 2 agent aliases created (all agents get "live" alias)
- 2 collaborator resources linking supervisor to collaborators
- IAM role with Bedrock permissions
- NO Lambda function (delegate was filtered out)

### 2. Test with Debug UI

```bash
# Get agent ID and alias from Terraform outputs
export BEDROCK_AGENT_ID=$(terraform output -raw supervisor_agent_id)
export BEDROCK_AGENT_ALIAS=$(terraform output -raw supervisor_alias_id)

# Start Debug UI
aws-vault exec personal -- python debug-ui/server.py
```

**Open:** http://localhost:8000

**Test Case:** "What is the meaning of life?"

**Expected Traces:**
- ✅ Supervisor (Judge) receives question
- ✅ Supervisor invokes collaborators (Sage, Oracle) via Bedrock native delegation
- ✅ Trace shows `collaborator_start` and `collaborator_complete` events
- ✅ NO Lambda invocations for delegate
- ✅ Collaborator responses synthesized into final answer

### 3. Verify Resource Tagging

```bash
# List all Bedsheet-managed resources
aws-vault exec personal -- aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=ManagedBy,Values=Bedsheet \
  --region eu-central-1

# List IAM roles with bedsheet- prefix
aws-vault exec personal -- aws iam list-roles \
  --query "Roles[?starts_with(RoleName, 'bedsheet-')]"
```

### 4. Add to examples/ (If Successful)

```bash
# From BedsheetAgents repo
cp -r /Users/sivan/VitakkaProjects/wisdom-council examples/wisdom-council
cd examples/wisdom-council
# Update README with deployment instructions
```

## Files Changed Summary

| File | Lines | Change |
|------|-------|--------|
| `bedsheet/deploy/targets/aws.py` | 40-51 | Filter delegate before creating context |
| `bedsheet/deploy/targets/aws_terraform.py` | 40-48 | Filter delegate before creating context |
| `bedsheet/deploy/templates/aws-terraform/main.tf.j2` | 40, 71 | Add bedsheet- prefix to IAM resources |
| `bedsheet/deploy/templates/aws-terraform/main.tf.j2` | 195-201, 226-232, 296-302 | Fix tags attribute (agent_resource_tags → tags) |

## Technical Decisions

### Why Filter at Python Level vs Template Level?

**Chosen:** Filter in Python code before creating template context

**Alternatives Considered:**
1. Template-level filtering with Jinja2 conditionals
2. Introspection-level filtering

**Rationale:**
- **Platform-specific logic belongs in target class** - introspection should remain platform-agnostic
- **Single point of change** - both Lambda and OpenAPI filtering in one place
- **Clear semantics** - "translate Bedsheet delegate to Bedrock collaborators"
- **Easy to extend** - if other actions need special handling, add more filters

### Why bedsheet- Prefix Only for Infrastructure?

**User-facing resources:** Bedrock agents, agent aliases
**Infrastructure resources:** IAM roles, policies, Lambda functions

**Rationale:**
- Users interact with agent names in Debug UI and API calls
- Infrastructure resources are managed by DevOps/admins
- Clean separation improves UX while maintaining manageability

### Why Both Prefix AND Tags?

**Prefix:** Alphabetical grouping, CLI filtering
**Tags:** Governance policies, cost allocation, cross-account queries

**Rationale:** Two-layer approach provides maximum flexibility:
- CLI filtering: `--query "Roles[?starts_with(RoleName, 'bedsheet-')]"`
- Tag-based policies: Enforce access controls on all Bedsheet resources
- Cost allocation: Track Bedsheet infrastructure costs

## Lessons Learned

1. **Platform idiom translation is critical** - Don't blindly copy Bedsheet patterns to cloud platforms
2. **Auto-registered actions need special handling** - delegate is a framework action, not a user action
3. **Early filtering prevents downstream issues** - Filter at context creation, not template level
4. **Tags are powerful but have limitations** - Some AWS resources don't support tags in Terraform
5. **Restart session when credentials fail** - aws-vault needs clean environment for proper credential loading
