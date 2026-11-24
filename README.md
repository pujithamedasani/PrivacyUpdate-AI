# PrivacyUpdate AI

**Intelligent Privacy Policy Monitoring & Change Detection Platform**

PrivacyUpdate AI is an automated compliance and privacy policy tracking platform. It monitors selected privacy policies and terms of service across web services, captures historical snapshots, performs syntactic and semantic diffing, classifies modifications across 8 standard privacy dimensions using OpenAI, and provides a human-in-the-loop review workflow.

---

## 🌿 Design System & Aesthetics

PrivacyUpdate AI follows an **Earthy and Natural** palette with a clean, modern SaaS interface:

- **Background:** Warm off-white (`#F6F4EE`)
- **Primary:** Deep forest green (`#344E41`)
- **Secondary:** Sage green (`#A3B18A`)
- **Accent:** Muted terracotta (`#C17C5A`)
- **Supporting:** Warm beige (`#E7E0D3`)
- **Text:** Dark charcoal (`#292D2A`)
- **Cards & Surfaces:** Subtle cream & white (`#FFFFFF` / `#FAF8F5`) with crisp borders and soft shadows.

---

## 🚀 Key Features

1. **Dashboard & Telemetry:**
   - Real-time KPIs retrieved directly from the SQLite database: Monitored Websites, Collected Snapshots, Detected Changes, Pending Human Reviews.
   - Interactive Chart.js charts:
     - Monitoring Activity Over Time (time series)
     - Change Categories Distribution (8 privacy dimensions)
     - Human Review Status (Approved, Flagged, Pending)
     - Milestone Completion Percentage (WBS tracking)
   - Recent changes and monitoring event audit logs.

2. **Privacy Monitoring:**
   - Full CRUD for monitored URLs with active/paused status toggles.
   - On-demand manual scan triggers connecting to Firecrawl (with clean fallback when API keys are unconfigured).
   - Tamper-evident SHA-256 cryptographic hashing to detect whether meaningful changes occurred.
   - Live audit logging per source.

3. **Historical Snapshots & Memento Discovery:**
   - Immutable snapshot storage with timestamps and version tags (`v1.0`, `v2.0`).
   - Side-by-side snapshot comparison tool with similarity scoring and syntactic diff hunks.
   - **Memento Protocol (RFC 7089) Integration:** Query Wayback Machine and Memento aggregators for historical web captures and import them directly into local snapshots.

4. **Change Detection & AI Analysis:**
   - Syntactic diffing using sequence matchers to isolate added, removed, and modified clauses.
   - OpenAI GPT-4o-mini integration classifying changes into:
     - *Data collection*
     - *Data sharing*
     - *Cookies and tracking*
     - *User rights*
     - *Data retention*
     - *Security*
     - *Third-party services*
     - *Policy updates*
   - Generates plain-English summaries and practical privacy risk implications.
   - Clear visual distinction between AI-assisted predictions and human-verified audit decisions.

5. **Human Review Workflow:**
   - Dedicated compliance queue for pending policy modifications.
   - One-click approval or flagging/rejection with reviewer attribution and audit comments.
   - Full auditable review trail recorded in SQLite.

6. **Reports & System Analytics:**
   - Export detected privacy changes to CSV.
   - Export complete audit trail to JSON.
   - On-demand database backup creation and download (`.db`).

---

## 🛠️ Technology Stack

- **Backend:** Python 3.13, Flask 3.1
- **Database:** SQLite 3 (Normalized relational schema with foreign keys)
- **Web Extraction:** Firecrawl API (with built-in clean HTTP scraping fallback)
- **Historical Archives:** Memento TimeMap Protocol (RFC 7089) & Wayback CDX API
- **AI Intelligence:** OpenAI API (`gpt-4o-mini`)
- **Frontend:** Semantic HTML5, CSS3 Custom Properties, Vanilla ES6 JavaScript
- **Visualizations:** Chart.js 4.4

---

## 🗄️ Database Architecture

The SQLite database (`data/privacyupdate.db`) contains 11 normalized tables:
1. `project_details`: Project title, scope, problem statement, and objectives.
2. `team_members`: Academic contributors, roles, and assigned responsibilities.
3. `milestones`: 4 project milestones with start/due dates and dynamic completion percentages.
4. `tasks`: 12 project tasks linked to milestones with priority, assignees, and statuses.
5. `sources`: Monitored privacy policy URLs and scan metadata.
6. `snapshots`: Cryptographically hashed document revisions with Memento URLs.
7. `changes`: Detected syntactic diffs, AI classification, risk severity, and review status.
8. `reviews`: Human-in-the-loop decisions, reviewer names, and audit comments.
9. `scan_logs`: Execution logs recording crawl duration, tools, and error messages.
10. `resources`: Technology stack items and reference documentation links.
11. `deliverables`: 4 academic weekly deliverables with upload file storage paths.

---

## ⚙️ Installation & Running the Application

### 1. Prerequisites
- Python 3.10+ installed.

### 2. Setup Environment
```bash
# Clone or navigate to the project directory
cd "PrivacyUpdate AI"

# (Optional) Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the example environment file:
```bash
cp .env.example .env
```
Optionally configure your API keys in `.env`:
- `FIRECRAWL_API_KEY`: For production Firecrawl web extraction. (If left blank, the system automatically uses the clean HTTP parser fallback).
- `OPENAI_API_KEY`: For OpenAI generative diff summaries and risk classifications. (If left blank, the system automatically uses the rule-based privacy rubric).

### 4. Initialize Database
Initialize and seed the database with complete academic project data:
```bash
python seed.py
```

### 5. Launch Application
```bash
python app.py
```
Open your browser and navigate to:
**http://localhost:5000**
