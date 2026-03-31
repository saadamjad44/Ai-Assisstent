---
name: Email Actions
description: Send and manage emails via Gmail MCP server
---

# Email Actions Skill

Send, draft, and manage emails using the Email MCP Server.

## MCP Server Setup

### Installation
```bash
cd mcp/email-mcp
npm install
```

### Configuration
Ensure these files exist:
- `scripts/credentials.json` (Google OAuth credentials)
- `scripts/token.json` (Auto-generated after first Gmail watcher run)

### Starting the Server
```bash
cd mcp/email-mcp
npm start
```

## Available Tools

### send_email
Send an email immediately.

**Parameters:**
- `to` (required): Recipient email
- `subject` (required): Subject line
- `body` (required): Email body (HTML supported)
- `cc` (optional): CC recipients
- `bcc` (optional): BCC recipients

**Example:**
```json
{
  "to": "client@example.com",
  "subject": "Invoice #1234",
  "body": "<h1>Thank you!</h1><p>Your invoice is attached.</p>"
}
```

### draft_email
Create a draft without sending.

Same parameters as `send_email`. Draft appears in Gmail Drafts folder.

### list_emails
List recent emails.

**Parameters:**
- `query` (optional): Gmail search query (default: "is:unread")
- `maxResults` (optional): Max emails to return (default: 10)

**Example Queries:**
- `is:unread` - Unread emails
- `from:client@example.com` - From specific sender
- `subject:invoice` - Contains "invoice" in subject
- `newer_than:1d` - Last 24 hours

## Claude Code Integration

Add to your `claude_code_config.json`:

```json
{
  "mcp_servers": [
    {
      "name": "email",
      "command": "node",
      "args": ["d:/practice/AI_Employee/mcp/email-mcp/index.js"]
    }
  ]
}
```

## Usage in Prompts

Claude can now use email tools:
- "Send an email to john@example.com about the meeting"
- "Draft a follow-up email for the proposal"
- "List my unread emails from today"

## Approval Workflow

For emails to unknown contacts or important messages:
1. Create draft instead of sending
2. Or create approval file in `/Pending_Approval/emails/`
3. Human reviews and approves
4. Orchestrator sends via MCP
