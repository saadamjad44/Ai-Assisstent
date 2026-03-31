---
name: Approval Workflow
description: Human-in-the-loop approval pattern for sensitive actions
---

# Approval Workflow Skill

This skill implements the Human-in-the-Loop (HITL) pattern for sensitive actions.

## Overview

For any action that could have significant consequences (payments, emails to clients, social posts), 
Claude should **not** execute directly. Instead:

1. Create an approval request file in `/Pending_Approval/`
2. Wait for human to move the file to `/Approved/`
3. Orchestrator detects approved file and executes the action

## When to Use

Use this pattern for:
- **Payments** > $50
- **Emails** to unknown contacts or with attachments
- **Social media posts** (LinkedIn, Twitter)
- **File deletions** or bulk operations
- **Any action flagged in Company_Handbook.md**

## Creating an Approval Request

Create a markdown file in the appropriate subfolder:

```markdown
---
type: payment  # or: email, linkedin_post, file_operation
amount: 500.00
recipient: Client Name
reason: Invoice #1234 payment
created: 2026-02-07T10:30:00Z
expires: 2026-02-08T10:30:00Z
status: pending
---

## Action Details
- Amount: $500.00
- To: Client Name
- Reference: Invoice #1234

## To Approve
Move this file to `/Approved/` folder.

## To Reject
Delete this file or move to `/Rejected/`.
```

## Folder Structure

```
/Pending_Approval/
  ├── payments/
  ├── emails/
  ├── linkedin/
  └── general/

/Approved/
  ├── linkedin/    # LinkedIn poster watches this
  └── ...          # Orchestrator processes others

/Rejected/         # Archive of rejected actions
```

## Implementation

The Orchestrator monitors `/Approved/` and executes actions:

1. **Payments**: Triggers payment MCP (when implemented)
2. **Emails**: Triggers email MCP to send
3. **LinkedIn**: LinkedIn Poster handles automatically
4. **General**: Logged and marked complete

## Safety Rules

1. **Never auto-approve** actions above thresholds
2. **Always log** both approval requests and executions
3. **Set expiry times** - stale approvals should be reviewed again
4. **One action per file** - don't batch sensitive actions
