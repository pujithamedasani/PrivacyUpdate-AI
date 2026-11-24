import hashlib
import json
from datetime import datetime, date, timedelta
from database import get_direct_db, init_db

def seed_database(force=False):
    """Seed the database with official PrivacyUpdate AI project milestones and operational data."""
    init_db()
    conn = get_direct_db()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM project_details")
    if cursor.fetchone()[0] > 0 and not force:
        conn.close()
        return False

    if force:
        # Clear existing tables
        tables = [
            "reviews", "changes", "snapshots", "scan_logs", "sources",
            "tasks", "milestones", "deliverables", "team_members",
            "resources", "project_details"
        ]
        for tbl in tables:
            cursor.execute(f"DELETE FROM {tbl}")
        cursor.execute("DELETE FROM sqlite_sequence")

    # 1. Project Details (Clean SaaS & System Architecture Focus)
    cursor.execute("""
        INSERT INTO project_details (
            id, title, description, problem_statement, proposed_solution,
            objectives, scope, technologies, updated_at
        ) VALUES (
            1,
            'PrivacyUpdate AI',
            'PrivacyUpdate AI is an intelligent privacy policy monitoring and change detection platform. It monitors privacy policies and related documents from different websites, collects their content, maintains historical versions and identifies meaningful changes. The system uses web data extraction, historical web archives and AI-powered analysis to help users understand what has changed in privacy policies without manually comparing lengthy documents.',
            'Websites frequently update their privacy policies, terms and data protection practices. Users often remain unaware of these changes because manually checking multiple websites and comparing lengthy policy documents is time-consuming and difficult. Existing approaches do not provide users with a convenient, centralized way to monitor policy updates, maintain historical records, identify important changes and understand their implications.',
            'Develop PrivacyUpdate AI, an automated platform that monitors selected privacy policy URLs, extracts webpage content using Firecrawl, stores historical content snapshots, uses Memento integration to explore historical web versions where available, compares newly collected content with previously stored versions, uses OpenAI to generate AI-assisted summaries and classify changes, highlights important privacy-related modifications, provides a human review mechanism, and maintains monitoring logs, historical records and project reports.',
            ?,
            'The project scope encompasses automated extraction of publicly accessible web privacy policies, historical snapshot archiving, syntactic and semantic diff computation, AI-driven summarization, and human-in-the-loop review. The system is designed for privacy researchers, consumer advocacy groups, and individual users seeking transparency.',
            ?,
            CURRENT_TIMESTAMP
        )
    """, (
        json.dumps([
            "Automate periodic and on-demand web extraction of privacy policies across registered services.",
            "Maintain tamper-evident historical content versions with cryptographic hashes and Memento archival lineage.",
            "Compute granular structural and textual differences between policy revisions.",
            "Leverage generative AI to classify modifications into key privacy dimensions and explain user impact.",
            "Empower human compliance reviewers to approve, flag, or reject AI assessments in an auditable workflow.",
            "Track project milestones, tasks, and system performance metrics through dynamic dashboards."
        ]),
        json.dumps([
            {"name": "Python", "role": "Main programming language & backend scripting", "category": "Core Language"},
            {"name": "Flask", "role": "Lightweight, robust web backend and RESTful API framework", "category": "Backend Framework"},
            {"name": "SQLite", "role": "Relational database with foreign-key integrity and persistent disk storage", "category": "Database"},
            {"name": "Firecrawl API", "role": "Clean web scraping and markdown conversion engine", "category": "Extraction API"},
            {"name": "Memento Protocol", "role": "TimeMap discovery across Internet Archive and public web repositories", "category": "Archive Protocol"},
            {"name": "OpenAI API", "role": "Generative intelligence for policy diff explanation and impact categorization", "category": "AI Engine"},
            {"name": "HTML5 / CSS3 / JavaScript", "role": "Responsive, earthy-themed frontend with native components", "category": "Frontend"},
            {"name": "Chart.js", "role": "Interactive visualization of monitoring trends and analytics", "category": "Data Visualization"}
        ])
    ))

    # 2. Team Members (3 Official Members - Led by Pujitha Medasani)
    team_data = [
        (1, "Pujitha Medasani", "PU-LEAD-01", "Project Lead, Full-Stack Architect & AI System Designer", "pujitha.medasani@privacyupdate.ai", "Overall project direction, full-stack Flask REST architecture, SQLite schema design, AI analysis engine (OpenAI/Groq), policy diff comparison algorithms, and core system integration."),
        (2, "Lahari Nanduru", "PU-DATA-02", "Data Extraction & Historical Archival Specialist", "lahari.nanduru@privacyupdate.ai", "Firecrawl extraction pipelines, Memento TimeMap historical querying, public privacy policy source monitoring, and snapshot cryptographic hashing."),
        (3, "Ratna Bindu Lingipilli", "PU-UI-03", "Frontend UI/UX & Quality Assurance Specialist", "ratnabindu.lingipilli@privacyupdate.ai", "Earthy design system implementation, responsive layouts, Chart.js telemetry dashboards, human review interface, and processing pipeline validation.")
    ]
    cursor.executemany("""
        INSERT INTO team_members (id, name, reg_number, role, email, responsibilities)
        VALUES (?, ?, ?, ?, ?, ?)
    """, team_data)

    # 3. Milestones (Exact Official Milestones: M1 to M4)
    milestones_data = [
        (
            1,
            "M1. Privacy Monitoring Planning and Source Identification",
            "Define the monitoring scope, information requirements, authoritative sources, privacy-update categories, and technical workflow for PrivacyUpdate AI. Establish how collected information will move from web extraction through processing, historical storage, change analysis, and AI-generated review outputs.",
            "2026-10-25", "2026-11-03", 100, "Completed"
        ),
        (
            2,
            "M2. Privacy Update Collection and Data Processing",
            "Build the data collection and processing pipeline that retrieves public privacy information using Firecrawl and transforms raw content into consistent, structured records for historical storage and analysis.",
            "2026-11-04", "2026-11-12", 100, "Completed"
        ),
        (
            3,
            "M3. Historical Privacy Context and Change Analysis",
            "Implement persistent historical context using Memento and develop comparison logic that distinguishes new privacy developments from previously reviewed information and identifies meaningful changes.",
            "2026-11-13", "2026-11-21", 85, "In Progress"
        ),
        (
            4,
            "M4. AI Privacy Summary and Review Checklist Generation",
            "Integrate the data pipeline, historical context, and LLM capabilities into PrivacyUpdate AI to generate structured privacy change summaries and review checklists. Evaluate output quality, reliability, and usefulness for human privacy review.",
            "2026-11-22", "2026-12-01", 60, "In Progress"
        )
    ]
    cursor.executemany("""
        INSERT INTO milestones (id, title, description, start_date, due_date, completion_percentage, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, milestones_data)

    # 4. Tasks (Exact Official 12 Tasks: 3 per Milestone - Primary Lead: Pujitha Medasani)
    tasks_data = [
        # Milestone 1: Privacy Monitoring Planning and Source Identification (Week 1)
        (
            1, 1, "1.1. Design the Monitoring Workflow",
            "Establish the technical workflow defining how privacy policy information moves from web extraction through processing, historical storage, change analysis, and AI-generated outputs.",
            1, "High", "2026-10-25", "2026-10-28", "Done"
        ),
        (
            2, 1, "1.2. Identify Authoritative Privacy Sources",
            "Identify authoritative privacy sources, target policy URLs, terms of service locations, and compliance documentation across selected services.",
            2, "High", "2026-10-28", "2026-10-31", "Done"
        ),
        (
            3, 1, "1.3. Define Privacy Monitoring Requirements",
            "Define the monitoring scope, information requirements, privacy-update categories, and change detection thresholds for PrivacyUpdate AI.",
            1, "Medium", "2026-10-31", "2026-11-03", "Done"
        ),

        # Milestone 2: Privacy Update Collection and Data Processing (Week 2)
        (
            4, 2, "2.1. Validate the Processing Pipeline",
            "Validate that the processing pipeline transforms raw web content into consistent, clean, and reliable policy records without formatting anomalies.",
            3, "High", "2026-11-04", "2026-11-07", "Done"
        ),
        (
            5, 2, "2.2. Process and Structure Privacy Updates",
            "Build routines to parse extracted DOM and markdown data into structured, indexed records prepared for historical storage and comparison.",
            1, "High", "2026-11-07", "2026-11-10", "Done"
        ),
        (
            6, 2, "2.3. Configure Privacy Data Collection",
            "Configure the automated data collection pipeline to retrieve public privacy documents using Firecrawl web extraction with robust error handling.",
            2, "Medium", "2026-11-10", "2026-11-12", "Done"
        ),

        # Milestone 3: Historical Privacy Context and Change Analysis (Week 3)
        (
            7, 3, "3.1. Prepare Privacy Analysis Context",
            "Assemble historical context, baseline snapshots, and metadata needed to ground policy comparisons and preserve legal auditability.",
            1, "High", "2026-11-13", "2026-11-16", "Done"
        ),
        (
            8, 3, "3.2. Compare Current and Historical Updates",
            "Develop comparison logic and diff algorithms that distinguish new privacy developments from previously reviewed information and identify meaningful changes.",
            1, "High", "2026-11-16", "2026-11-19", "Done"
        ),
        (
            9, 3, "3.3. Implement Historical Privacy Storage",
            "Implement persistent historical context using Memento TimeMap discovery and SHA-256 cryptographic snapshot version storage.",
            2, "Medium", "2026-11-19", "2026-11-21", "In Progress"
        ),

        # Milestone 4: AI Privacy Summary and Review Checklist Generation (Week 4)
        (
            10, 4, "4.1. Evaluate and Document PrivacyUpdate AI",
            "Evaluate output quality, reliability, and usefulness for human privacy reviewers, and document platform deployment and verification results.",
            1, "High", "2026-11-22", "2026-11-25", "In Progress"
        ),
        (
            11, 4, "4.2. Implement AI-Generated Privacy Outputs",
            "Implement LLM-driven generation of structured privacy change summaries, impact explanations, and human review checklists.",
            1, "High", "2026-11-25", "2026-11-28", "To Do"
        ),
        (
            12, 4, "4.3. Design Privacy Analysis Prompts",
            "Design and optimize prompt templates and schemas for 8 privacy dimension classifications, user implications, and severity risk ratings.",
            1, "Medium", "2026-11-28", "2026-12-01", "To Do"
        )
    ]
    cursor.executemany("""
        INSERT INTO tasks (id, milestone_id, name, description, assigned_to, priority, start_date, due_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tasks_data)

    # 5. Monitored Sources (5 sources)
    sources_data = [
        (1, "GitHub Privacy Statement", "https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement", "GitHub's primary privacy statement detailing data processing for repositories, developer activity, and telemetry.", 1, "2026-11-24 09:04:30", "Success"),
        (2, "Reddit Privacy Policy", "https://www.reddit.com/policies/privacy-policy", "Reddit's user privacy rules covering public posts, behavioral tracking, ad personalization, and third-party data broker sharing.", 1, "2026-11-24 06:04:30", "Success"),
        (3, "Discord Privacy Policy", "https://discord.com/privacy", "Discord terms covering voice/video telemetry, message indexing, age verification, and generative AI features.", 1, "2026-11-24 00:04:30", "Success"),
        (4, "OpenAI Privacy Policy", "https://openai.com/privacy/", "OpenAI consumer and enterprise terms governing model training on user inputs, data retention, and API logging.", 1, "2026-11-23 12:04:30", "Success"),
        (5, "Spotify Privacy Policy", "https://www.spotify.com/us/legal/privacy-policy/", "Spotify global privacy policy governing streaming listening habits, voice control data, and marketing cookies.", 0, "2026-11-22 12:04:30", "Pending")
    ]
    cursor.executemany("""
        INSERT INTO sources (id, name, url, description, is_active, last_scanned_at, last_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, sources_data)

    # 6. Snapshots
    gh_v1_content = """# GitHub Privacy Statement (Archived Oct 2024)

## 1. Information GitHub Collects
We collect basic user profile information, such as your username and email address, when you register for an account. We also collect transactional information regarding your purchases.

## 2. How We Use Your Information
We use your information to provide GitHub services, process transactions, communicate with you, and secure our platform. We do not sell your personal information.

## 3. Data Sharing with Third Parties
We share personal data with our affiliates, vendors, and service providers who help us operate GitHub, such as cloud hosting providers.

## 4. User Rights and Choices
You can access, update, or delete your personal information through your account settings or by contacting privacy@github.com."""

    gh_v2_content = """# GitHub Privacy Statement (Current Nov 2026)

## 1. Information GitHub Collects
We collect basic user profile information, such as your username and email address, when you register for an account. We also collect transactional information regarding your purchases, as well as developer environment telemetry, telemetry related to Copilot usage, and public code contribution telemetry.

## 2. How We Use Your Information
We use your information to provide GitHub services, process transactions, communicate with you, secure our platform, and train foundational developer assistance AI models using telemetry and public code repositories, subject to opt-out controls.

## 3. Data Sharing with Third Parties
We share personal data with our affiliates, parent company Microsoft, vendors, and trusted cloud infrastructure providers. We may also provide aggregated analytical telemetry to research partners.

## 4. User Rights and Choices
You can access, update, or delete your personal information through your account settings or by contacting privacy@github.com. You may also configure AI telemetry training opt-outs directly in your organization settings."""

    reddit_v1_content = """# Reddit Privacy Policy (Archived 2024)

## Information We Collect
We collect the content you submit to Reddit, including posts, comments, private messages, and votes. We also collect device and browser information.

## How We Share Information
We share information with our vendors and service providers. Much of the information on Reddit is public and accessible to anyone."""

    reddit_v2_content = """# Reddit Privacy Policy (Current Nov 2026)

## Information We Collect
We collect the content you submit to Reddit, including posts, comments, private messages, and votes. We also collect detailed device fingerprints, precise geolocation if enabled, and off-platform web browsing activity through Reddit Pixels.

## How We Share Information
We share information with our vendors and service providers. Much of the information on Reddit is public. We also license public user content and comment corpora to commercial artificial intelligence partners for LLM training purposes."""

    discord_v1_content = """# Discord Privacy Policy (Current Nov 2026)

## What We Collect
We collect information you provide directly, such as email, phone number, and messages you send in servers and direct messages.

## Voice and Video Data
When you participate in voice or video calls, we transmit that data to deliver the call. We do not record the audio of calls without explicit notification.

## Your Controls
You have the right to request deletion of your Discord account and associated data."""

    openai_v1_content = """# OpenAI Privacy Policy (Current Nov 2026)

## Personal Information We Collect
We collect personal information that you provide when using our Services, including your name, contact details, payment card information, and account credentials.

## Content You Provide
When you use our consumer services, we may use the content you submit to help train and improve our models, unless you submit an opt-out request or use enterprise business plans with zero-retention guarantees.

## Data Retention
We retain personal information only for as long as necessary to provide the Services and fulfill legal obligations."""

    snapshots_data = [
        (1, 1, "v1.0 (Historical)", gh_v1_content, hashlib.sha256(gh_v1_content.encode()).hexdigest(), "Memento Archive", "https://web.archive.org/web/20241001/github.com/privacy", "2026-10-10 12:04:30"),
        (2, 1, "v2.0 (Active)", gh_v2_content, hashlib.sha256(gh_v2_content.encode()).hexdigest(), "Firecrawl", None, "2026-11-24 09:04:30"),
        (3, 2, "v1.0 (Historical)", reddit_v1_content, hashlib.sha256(reddit_v1_content.encode()).hexdigest(), "Memento Archive", "https://web.archive.org/web/20240915/reddit.com/privacy", "2026-09-15 12:04:30"),
        (4, 2, "v2.0 (Active)", reddit_v2_content, hashlib.sha256(reddit_v2_content.encode()).hexdigest(), "Firecrawl", None, "2026-11-24 06:04:30"),
        (5, 3, "v1.0 (Active)", discord_v1_content, hashlib.sha256(discord_v1_content.encode()).hexdigest(), "Firecrawl", None, "2026-11-24 00:04:30"),
        (6, 4, "v1.0 (Active)", openai_v1_content, hashlib.sha256(openai_v1_content.encode()).hexdigest(), "Firecrawl", None, "2026-11-23 12:04:30")
    ]
    cursor.executemany("""
        INSERT INTO snapshots (id, source_id, version_tag, content, content_hash, extraction_method, memento_archive_url, snapshot_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, snapshots_data)

    # 7. Changes (5 detected changes)
    changes_data = [
        (1, 1, 1, 2, "Modified", "Data Collection & AI Model Training",
         "We use your information to provide GitHub services, process transactions, communicate with you, and secure our platform. We do not sell your personal information.",
         "We use your information to provide GitHub services, process transactions, communicate with you, secure our platform, and train foundational developer assistance AI models using telemetry and public code repositories, subject to opt-out controls.",
         "Data collection",
         "GitHub explicitly added AI model training to its permitted data processing purposes, utilizing developer telemetry and public repository code.",
         "Users' public contributions and interaction metrics may be ingested into generative coding models. Users must actively opt out via account feature settings.",
         "High", "Approved", "2026-11-24 09:04:30"),

        (2, 1, 1, 2, "Added", "Corporate Affiliate Data Sharing",
         "We share personal data with our affiliates, vendors, and service providers who help us operate GitHub, such as cloud hosting providers.",
         "We share personal data with our affiliates, parent company Microsoft, vendors, and trusted cloud infrastructure providers. We may also provide aggregated analytical telemetry to research partners.",
         "Data sharing",
         "Clarified direct data pipeline sharing with parent enterprise Microsoft and academic/industry research partners.",
         "User telemetry and telemetry aggregates are broader in scope across Microsoft cloud ecosystems.",
         "Medium", "Approved", "2026-11-24 09:04:30"),

        (3, 2, 3, 4, "Modified", "Third-Party AI Licensing of Public Content",
         "Much of the information on Reddit is public and accessible to anyone.",
         "Much of the information on Reddit is public. We also license public user content and comment corpora to commercial artificial intelligence partners for LLM training purposes.",
         "Third-party services",
         "Reddit formalized licensing agreements permitting commercial AI laboratories to ingest public post and comment feeds.",
         "User commentary, conversations, and public submissions are monetized and repurposed for training external commercial LLMs.",
         "Critical", "Approved", "2026-11-24 06:04:30"),

        (4, 2, 3, 4, "Added", "Off-Platform Pixel & Geolocation Tracking",
         "We also collect device and browser information.",
         "We also collect detailed device fingerprints, precise geolocation if enabled, and off-platform web browsing activity through Reddit Pixels.",
         "Cookies and tracking",
         "Introduced broader cross-web tracking through proprietary ad pixels and hardware fingerprinting.",
         "Users are tracked beyond reddit.com across partner merchant sites for targeted advertising attribution.",
         "High", "Pending", "2026-11-24 06:04:30"),

        (5, 1, 1, 2, "Added", "User Rights - AI Opt-Out Mechanism",
         "You can access, update, or delete your personal information through your account settings or by contacting privacy@github.com.",
         "You can access, update, or delete your personal information through your account settings or by contacting privacy@github.com. You may also configure AI telemetry training opt-outs directly in your organization settings.",
         "User rights",
         "Added explicit user administrative toggle to opt out of Copilot/AI telemetry collection.",
         "Positive privacy enhancement providing user self-determination over code telemetry utilization.",
         "Low", "Approved", "2026-11-24 09:04:30")
    ]
    cursor.executemany("""
        INSERT INTO changes (
            id, source_id, old_snapshot_id, new_snapshot_id, change_type, affected_section,
            previous_content, updated_content, category, ai_summary, privacy_implications,
            severity, review_status, detected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, changes_data)

    # 8. Reviews
    reviews_data = [
        (1, 1, "Pujitha Medasani", 1, "Approved", "Verified against GitHub November policy update changelog. Accurate AI categorization regarding Copilot training telemetry.", "2026-11-24 10:04:30"),
        (2, 2, "Lahari Nanduru", 2, "Approved", "Corporate sharing clause confirmed. Microsoft affiliate data flow is standard but noteworthy.", "2026-11-24 10:30:00"),
        (3, 5, "Ratna Bindu Lingipilli", 3, "Approved", "AI summary accurately highlights the new opt-out control added in organization settings.", "2026-11-24 11:00:00")
    ]
    cursor.executemany("""
        INSERT INTO reviews (id, change_id, reviewer_name, reviewer_id, decision, comments, reviewed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, reviews_data)

    # 9. Scan Logs
    scan_logs_data = [
        (1, 1, "Success", "Extracted 4,210 tokens from GitHub Privacy Statement. Compared with snapshot v1.0. Found 2 modifications.", "Firecrawl", 2.34, "2026-11-24 09:04:30"),
        (2, 2, "Success", "Extracted 3,890 tokens from Reddit Privacy Policy. Compared with snapshot v1.0. Found 2 modifications.", "Firecrawl", 1.89, "2026-11-24 06:04:30"),
        (3, 3, "Success", "Initial baseline snapshot captured for Discord Privacy Policy. No previous version to diff.", "Firecrawl", 2.15, "2026-11-24 00:04:30"),
        (4, 4, "Success", "Initial baseline snapshot captured for OpenAI Privacy Policy. Stored SHA-256 hash.", "Firecrawl", 1.95, "2026-11-23 12:04:30"),
        (5, 5, "Pending", "Monitoring disabled by user. Next scheduled run queued.", "System", 0.0, "2026-11-22 12:04:30")
    ]
    cursor.executemany("""
        INSERT INTO scan_logs (id, source_id, status, message, extraction_tool, duration_seconds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, scan_logs_data)

    # 10. Resources
    resources_data = [
        (1, "Python 3.13", "Core Language", "Primary programming language utilized for server execution, diffing algorithms, and API orchestration.", "https://docs.python.org/3/", 1),
        (2, "Flask 3.1", "Backend Framework", "Micro-framework providing routing, request dispatching, session handling, and RESTful API endpoints.", "https://flask.palletsprojects.com/", 1),
        (3, "SQLite 3", "Database Engine", "Serverless zero-configuration relational database enforcing ACID compliance, foreign keys, and transaction integrity.", "https://www.sqlite.org/", 1),
        (4, "Firecrawl API", "Extraction Engine", "Clean web scraping and markdown conversion engine optimized for modern JavaScript-heavy DOMs.", "https://firecrawl.dev/", 1),
        (5, "Memento Protocol (RFC 7089)", "Historical Archiving", "Standardized web protocol for discovering and accessing temporal versions across Internet Archive Wayback Machine.", "https://tools.ietf.org/html/rfc7089", 1),
        (6, "OpenAI API (GPT-4o-mini)", "AI Analysis Engine", "Generative language model employed for policy diff explanation, classification into 8 privacy categories, and user impact risk scoring.", "https://platform.openai.com/docs/", 1),
        (7, "HTML5 / CSS3 / ES6", "Frontend Architecture", "Semantic markup and custom earthy design system styled with responsive CSS variables.", "https://developer.mozilla.org/", 1),
        (8, "Chart.js 4.4", "Data Visualization", "Canvas-based charting library for dynamic telemetry visualization across time series and distribution graphs.", "https://www.chartjs.org/", 1)
    ]
    cursor.executemany("""
        INSERT INTO resources (id, name, category, description, doc_url, is_system)
        VALUES (?, ?, ?, ?, ?, ?)
    """, resources_data)

    # 11. Deliverables (Exact 4 Weekly Phases - Led by Pujitha Medasani)
    deliverables_data = [
        (
            1, 1, "Week 1: Privacy Monitoring Planning and Source Identification",
            "Define the monitoring scope, information requirements, authoritative sources, privacy-update categories, and technical workflow for PrivacyUpdate AI. Establish how collected information will move from web extraction through processing, historical storage, change analysis, and AI-generated review outputs.",
            "2026-11-03", 1, "Approved", None, None, "2026-11-02 12:04:30"
        ),
        (
            2, 2, "Week 2: Privacy Update Collection and Data Processing",
            "Build the data collection and processing pipeline that retrieves public privacy information using Firecrawl and transforms raw content into consistent, structured records for historical storage and analysis.",
            "2026-11-10", 1, "Approved", None, None, "2026-11-09 12:04:30"
        ),
        (
            3, 3, "Week 3: Historical Privacy Context and Change Analysis",
            "Implement persistent historical context using Memento and develop comparison logic that distinguishes new privacy developments from previously reviewed information and identifies meaningful changes.",
            "2026-11-17", 2, "Submitted", None, None, "2026-11-17 12:04:30"
        ),
        (
            4, 4, "Week 4: AI Privacy Summary and Review Checklist Generation",
            "Integrate the data pipeline, historical context, and LLM capabilities into PrivacyUpdate AI to generate structured privacy change summaries and review checklists. Evaluate output quality, reliability, and usefulness for human privacy review.",
            "2026-12-01", 1, "In Progress", None, None, None
        )
    ]
    cursor.executemany("""
        INSERT INTO deliverables (
            id, week_number, title, description, deadline, assigned_to,
            status, file_path, file_name, submission_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, deliverables_data)

    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    seed_database(force=True)
    print("Database successfully reseeded with official PrivacyUpdate AI project milestones!")
