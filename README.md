# Personal AI Employee - Bronze Tier

**Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

A proof-of-concept Personal AI Employee that autonomously manages your personal and business affairs using Claude Code as the reasoning engine and Obsidian as the management dashboard.

---

## 🎯 Project Overview

This is a **Bronze Tier** implementation of the Personal AI Employee hackathon—a foundational, fully functional autonomous agent system that bridges AI reasoning with practical task automation. 

### What Does It Do?

- **Monitors** your personal and business channels (Gmail, WhatsApp, file systems)
- **Reasons** about tasks and creates action plans autonomously
- **Manages** an Obsidian vault as a centralized knowledge base and execution hub
- **Stores** and retrieves context to execute complex, multi-step workflows
- **Operates** 24/7 with agent skills implementing all AI functionality

### Key Concept

Instead of being a reactive chatbot, this AI Employee is **proactive**. Lightweight Python "Watcher" scripts monitor data sources, wake up Claude Code when something needs attention, and the AI executes decisions—creating a true autonomous system.

---

## 📦 What's Included (Bronze Tier)

✅ **Obsidian Vault Structure**
- `Dashboard.md` — Central hub for task overview and status tracking
- `Company_Handbook.md` — Business rules, templates, and reference documentation
- `/Inbox` — Incoming messages and data requiring processing
- `/Needs_Action` — Prioritized tasks awaiting execution
- `/Done` — Completed work and audit trail

✅ **Core Components**
- One fully functional watcher script (startup foundation)
- Claude Code integration for autonomous reasoning
- Basic folder structure with clear separation of concerns
- Agent Skills framework for implementing AI functionality

✅ **Automation Setup**
- File monitoring system to trigger agent execution
- Vault read/write integration via Claude Code
- Foundational architecture for expansion to higher tiers

---

## 🛠️ Tech Stack

| Component | Purpose |
|-----------|---------|
| **Claude Code** | AI reasoning engine and task execution |
| **Obsidian** | Local-first markdown vault for knowledge management |
| **Python 3.13+** | Watcher scripts and orchestration |
| **MCP (Model Context Protocol)** | Agent skills and external integrations |
| **File System Watchers** | Trigger automation on directory changes |

---

## 🚀 Getting Started

### Prerequisites
- Claude Code (Pro subscription recommended)
- Obsidian v1.10.6+
- Python 3.13 or higher
- Git for version control
- Basic terminal/command-line familiarity

### Installation

1. **Clone or download this repository**
   ```bash
   git clone <repo-url>
   cd AI_Employee
   ```

2. **Open Obsidian Vault**
   - Launch Obsidian
   - Open vault: `AI-Employee-Vault/`
   - Review `Dashboard.md` and `Company_Handbook.md`

3. **Set up Python environment**
   ```bash
   cd scripts
   python -m venv venv
   venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```

4. **Configure Claude Code**
   - Verify Claude Code is active: `claude --version`
   - Set up API credentials if needed

5. **Start the watcher**
   ```bash
   python scripts/inbox_watcher.py
   ```

---

## 📂 Folder Structure

```
AI-Employee/
├── AI-Employee-Vault/          # Obsidian vault
│   ├── Dashboard.md            # Task overview & status
│   ├── Company_Handbook.md     # Business rules & templates
│   ├── Inbox/                  # Incoming data
│   ├── Needs_Action/           # Tasks to execute
│   ├── Done/                   # Completed work
│   └── Logs/                   # Execution logs
├── scripts/                    # Python watcher scripts
│   ├── inbox_watcher.py        # File system monitoring
│   ├── requirements.txt        # Python dependencies
│   └── [other watchers]        # Extensible architecture
├── mcp/                        # Model Context Protocol servers
└── README.md                   # This file
```

---

## 🔄 How It Works

### The Automation Loop

1. **Watch** → Watcher script detects new input (file, email, message)
2. **Alert** → Watcher writes event to `/Inbox` directory
3. **Reason** → Claude Code reads context and creates action plan
4. **Execute** → Claude Code updates vault files (`/Needs_Action` → `/Done`)
5. **Log** → Execution recorded in Logs for audit trail

### Example Workflow

```
User adds task → Inbox/ → Claude Code reasons → Plan.md created → 
Action executed → Vault updated → Done/
```

---

## 🎓 Learning Resources

### Required Reading
- `CLAUDE.md` — System instructions and operating standards
- `AGENTS.md` — Persona roles (Designer, Engineer, QA, Communicator)
- `requirements.md` — Full hackathon brief and tier definitions

### Documentation
- Review `Company_Handbook.md` for business logic
- Check `Dashboard.md` for current status and active tasks
- See `Logs/` for execution history and debugging

---

## 🚦 Current Capabilities (Bronze Tier)

✅ **What Works Now**
- File system monitoring and task detection
- Vault reading and writing via Claude Code
- Dashboard tracking and status updates
- Action plan creation and execution logging
- Extensible folder structure for scalability

⏭️ **Roadmap (Silver & Gold Tiers)**
- Multiple data source integration (Gmail, WhatsApp, LinkedIn)
- Social media posting automation
- Email MCP server integration
- Multi-step reasoning loops (Ralph Wiggum pattern)
- External action execution
- Human-in-the-loop approvals

---

## 🔐 Security & Best Practices

### Local-First Philosophy
- All sensitive data stays local (no cloud sync of credentials)
- Secrets stored separately from vault (`.env` files)
- Audit trail in `Logs/` for accountability
- Git-tracked for version control and recovery

### Privacy
- No personal data transmitted to external services by default
- Credentials and tokens never synced to cloud
- WhatsApp sessions isolated to local machine
- Banking data remains on-device

---

## 📝 Configuration

### Watcher Scripts
Edit `scripts/requirements.txt` to add new Python dependencies:
```
claude-sdk>=1.0.0
obsidian-api
python-dotenv
```

### Dashboard Customization
- Update `Dashboard.md` to add custom sections
- Use standard Markdown formatting for compatibility
- Link to related documents via `[[WikiLinks]]`

### Adding New Tasks
1. Create `.md` file in `/Inbox`
2. Claude Code automatically detects and processes
3. Results appear in `/Needs_Action` or `/Done`

---

## 🐛 Troubleshooting

### Watcher Not Triggering
- Check file system permissions on `/Inbox` directory
- Verify Python environment is activated
- Review `Logs/watcher_log_*.md` for errors

### Claude Code Not Reading Files
- Ensure vault path is correct in configuration
- Verify Obsidian is running or vault is accessible as directory
- Check Claude Code API credentials

### Tasks Not Executing
- Review `Dashboard.md` for blocking issues
- Check `Company_Handbook.md` for business rule conflicts
- Enable debug logging in watcher scripts

---

## 📊 Extending to Silver & Gold Tiers

Once Bronze tier is stable, upgrade roadmap:

### Silver Tier (20-30 hours additional)
- Add Gmail and WhatsApp watchers
- Implement LinkedIn posting automation
- Create multi-step reasoning loops
- Add MCP server for email actions
- Enable human-in-the-loop approvals

### Gold Tier (40+ hours additional)
- Cross-domain integration (Personal + Business)
- Odoo accounting system integration
- Facebook, Instagram, Twitter automation
- CEO briefing generation
- Advanced error recovery

---

## 📞 Support & Community

- **Weekly Research Meeting:** Wednesday 10:00 PM UTC on Zoom
- **Meeting ID:** 871 8870 7642 | **Passcode:** 744832
- **YouTube (Live & Recording):** [Panaversity Channel](https://www.youtube.com/@panaversity)
- **Documentation:** See `requirements.md` for full hackathon details

---

## 📄 License

This project is part of the Personal AI Employee Hackathon 2026.

---

## ✨ Credits

Created as a Bronze Tier submission for the **Personal AI Employee Hackathon: Building Autonomous FTEs in 2026**.

Built with Claude Code, Obsidian, and Python—proving that with the right architecture, AI can be both autonomous _and_ trustworthy.

---

**Status:** ✅ Bronze Tier Complete | Next: Silver Tier Expansion

**Last Updated:** March 31, 2026

