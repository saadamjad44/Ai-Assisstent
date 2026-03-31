---
name: LinkedIn Automation
description: Automate LinkedIn monitoring and posting for business growth
---

# LinkedIn Automation Skill

Automate LinkedIn activities for business promotion and lead monitoring.

## Components

### 1. LinkedIn Watcher (`scripts/linkedin_watcher.py`)
Monitors LinkedIn for:
- New messages
- Connection requests
- Notifications with keywords: job, opportunity, pricing, help

Creates action files in `/Inbox/` for Claude to process.

### 2. LinkedIn Poster (`scripts/linkedin_poster.py`)
Posts content to LinkedIn:
- Reads drafts from `/Pending_Approval/linkedin/`
- Publishes when moved to `/Approved/linkedin/`
- Archives posted content to `/Done/linkedin_posts/`

## Setup Requirements

### Driver Requirement
This skill uses **Selenium** with Chrome WebDriver. The script automatically manages the driver download.

### Cookie Authentication
LinkedIn uses cookie-based auth. Export your cookies:

1. Log into LinkedIn in browser
2. Install "Cookie-Editor" extension
3. Export cookies as JSON
4. Save to: `scripts/linkedin_cookies.json`

Required cookies:
- `li_at` (main auth token)
- `JSESSIONID` (session ID)

### Example Cookie File
```json
[
  {"name": "li_at", "value": "AQE...", "domain": ".linkedin.com"},
  {"name": "JSESSIONID", "value": "ajax:123...", "domain": ".linkedin.com"}
]
```

## Creating Posts

### Manual Method
```bash
python scripts/linkedin_poster.py --create "my_post_title"
```

This creates a template in `/Pending_Approval/linkedin/`.

### Post Template
```markdown
---
type: linkedin_post
visibility: PUBLIC  # or CONNECTIONS
scheduled: null
created: 2026-02-07
status: pending_approval
---

## Post Content

Your post content here.
Use emojis and hashtags for engagement! 🚀

#AI #Automation #Business
```

## Approval Flow

1. Create post in `/Pending_Approval/linkedin/`
2. Review and edit the content
3. Move to `/Approved/linkedin/`
4. LinkedIn Poster publishes automatically
5. Check `/Done/linkedin_posts/` for confirmation

## Best Practices

- **Timing**: Post during business hours (9 AM - 5 PM)
- **Hashtags**: Use 3-5 relevant hashtags
- **Engagement**: Ask questions to drive comments
- **Consistency**: Post 2-3 times per week for algorithm favor
