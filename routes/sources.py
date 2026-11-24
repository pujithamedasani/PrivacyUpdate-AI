import hashlib
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from database import query_db, execute_db
from services.firecrawl_service import FirecrawlService
from services.diff_service import DiffService
from services.ai_analysis_service import AIAnalysisService

bp = Blueprint('sources', __name__)

@bp.route('/sources')
def sources_page():
    sources = query_db("""
        SELECT s.*,
               COUNT(DISTINCT sn.id) as snapshot_count,
               COUNT(DISTINCT c.id) as change_count
        FROM sources s
        LEFT JOIN snapshots sn ON s.id = sn.source_id
        LEFT JOIN changes c ON s.id = c.source_id
        GROUP BY s.id
        ORDER BY s.id ASC
    """)
    firecrawl_ready = FirecrawlService.is_configured()
    ai_ready = AIAnalysisService.is_configured()
    return render_template('sources.html', sources=sources, firecrawl_ready=firecrawl_ready, ai_ready=ai_ready)

@bp.route('/api/sources', methods=['GET'])
def get_sources_api():
    sources = query_db("""
        SELECT s.*,
               COUNT(DISTINCT sn.id) as snapshot_count,
               COUNT(DISTINCT c.id) as change_count
        FROM sources s
        LEFT JOIN snapshots sn ON s.id = sn.source_id
        LEFT JOIN changes c ON s.id = c.source_id
        GROUP BY s.id
        ORDER BY s.id ASC
    """)
    return jsonify({"success": True, "sources": sources})

@bp.route('/api/sources', methods=['POST'])
def add_source_api():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    url = data.get('url', '').strip()
    description = data.get('description', '').strip()
    is_active = 1 if data.get('is_active', True) else 0

    if not name or not url:
        return jsonify({"success": False, "error": "Source name and URL are required."}), 400

    existing = query_db("SELECT id FROM sources WHERE url = ?", (url,), one=True)
    if existing:
        return jsonify({"success": False, "error": "A monitored source with this URL already exists."}), 409

    source_id = execute_db("""
        INSERT INTO sources (name, url, description, is_active, last_status)
        VALUES (?, ?, ?, ?, 'Pending')
    """, (name, url, description, is_active))

    # Log source creation
    execute_db("""
        INSERT INTO scan_logs (source_id, status, message, extraction_tool)
        VALUES (?, 'Pending', ?, 'System')
    """, (source_id, f"Registered new monitored privacy policy source: {name}"))

    return jsonify({"success": True, "source_id": source_id, "message": "Source added successfully."})

@bp.route('/api/sources/<int:source_id>', methods=['GET'])
def get_single_source_api(source_id):
    source = query_db("SELECT * FROM sources WHERE id = ?", (source_id,), one=True)
    if not source:
        return jsonify({"success": False, "error": "Source not found."}), 404
    snapshots = query_db("SELECT * FROM snapshots WHERE source_id = ? ORDER BY snapshot_date DESC", (source_id,))
    logs = query_db("SELECT * FROM scan_logs WHERE source_id = ? ORDER BY created_at DESC LIMIT 20", (source_id,))
    return jsonify({"success": True, "source": source, "snapshots": snapshots, "logs": logs})

@bp.route('/api/sources/<int:source_id>', methods=['PUT'])
def edit_source_api(source_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    url = data.get('url', '').strip()
    description = data.get('description', '').strip()
    is_active = 1 if data.get('is_active', True) else 0

    if not name or not url:
        return jsonify({"success": False, "error": "Source name and URL are required."}), 400

    existing = query_db("SELECT id FROM sources WHERE url = ? AND id != ?", (url, source_id), one=True)
    if existing:
        return jsonify({"success": False, "error": "Another monitored source with this URL already exists."}), 409

    execute_db("""
        UPDATE sources SET
            name = ?,
            url = ?,
            description = ?,
            is_active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (name, url, description, is_active, source_id))

    return jsonify({"success": True, "message": "Source updated successfully."})

@bp.route('/api/sources/<int:source_id>/toggle', methods=['POST'])
def toggle_source_api(source_id):
    source = query_db("SELECT is_active, name FROM sources WHERE id = ?", (source_id,), one=True)
    if not source:
        return jsonify({"success": False, "error": "Source not found."}), 404

    new_state = 0 if source['is_active'] == 1 else 1
    execute_db("UPDATE sources SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_state, source_id))

    status_word = "enabled" if new_state == 1 else "disabled"
    execute_db("""
        INSERT INTO scan_logs (source_id, status, message, extraction_tool)
        VALUES (?, 'Info', ?, 'System')
    """, (source_id, f"Monitoring {status_word} for {source['name']}."))

    return jsonify({"success": True, "is_active": new_state, "message": f"Monitoring {status_word}."})

@bp.route('/api/sources/<int:source_id>', methods=['DELETE'])
def delete_source_api(source_id):
    source = query_db("SELECT name FROM sources WHERE id = ?", (source_id,), one=True)
    if not source:
        return jsonify({"success": False, "error": "Source not found."}), 404

    execute_db("DELETE FROM sources WHERE id = ?", (source_id,))
    return jsonify({"success": True, "message": f"Source '{source['name']}' deleted successfully."})

@bp.route('/api/sources/<int:source_id>/scan', methods=['POST'])
def trigger_scan_api(source_id):
    """
    Execute an on-demand scan of the privacy policy URL.
    - Scrapes content via Firecrawl (or clean fallback if key not configured)
    - Compares content hash with previous snapshot
    - If modified, creates new snapshot, detects diffs, runs AI analysis, and records changes
    - Inserts auditable scan log
    """
    source = query_db("SELECT * FROM sources WHERE id = ?", (source_id,), one=True)
    if not source:
        return jsonify({"success": False, "error": "Source not found."}), 404

    url = source['url']
    scrape_res = FirecrawlService.scrape_url(url, allow_fallback=True)

    if not scrape_res.get('success'):
        err_msg = scrape_res.get('error', 'Unknown extraction error')
        execute_db("""
            UPDATE sources SET last_scanned_at = CURRENT_TIMESTAMP, last_status = 'Failed' WHERE id = ?
        """, (source_id,))
        execute_db("""
            INSERT INTO scan_logs (source_id, status, message, extraction_tool, duration_seconds)
            VALUES (?, 'Failed', ?, ?, ?)
        """, (source_id, err_msg, scrape_res.get('tool', 'Firecrawl'), scrape_res.get('duration', 0.0)))
        return jsonify({
            "success": False,
            "error": err_msg,
            "tool": scrape_res.get('tool')
        }), 400

    content = scrape_res.get('content', '').strip()
    if not content:
        err_msg = "Extracted document body was empty."
        execute_db("""
            UPDATE sources SET last_scanned_at = CURRENT_TIMESTAMP, last_status = 'Failed' WHERE id = ?
        """, (source_id,))
        execute_db("""
            INSERT INTO scan_logs (source_id, status, message, extraction_tool, duration_seconds)
            VALUES (?, 'Failed', ?, ?, ?)
        """, (source_id, err_msg, scrape_res.get('tool', 'Firecrawl'), scrape_res.get('duration', 0.0)))
        return jsonify({"success": False, "error": err_msg}), 400

    content_hash = hashlib.sha256(content.encode()).hexdigest()
    tool_used = scrape_res.get('tool', 'Firecrawl')
    duration = scrape_res.get('duration', 0.0)

    # Fetch latest snapshot for this source
    latest_snapshot = query_db("""
        SELECT * FROM snapshots WHERE source_id = ? ORDER BY snapshot_date DESC LIMIT 1
    """, (source_id,), one=True)

    # Case A: Identical content
    if latest_snapshot and latest_snapshot['content_hash'] == content_hash:
        execute_db("""
            UPDATE sources SET last_scanned_at = CURRENT_TIMESTAMP, last_status = 'Success' WHERE id = ?
        """, (source_id,))
        log_msg = f"Scan complete. No policy modifications detected; content matches {latest_snapshot['version_tag']} (SHA-256: {content_hash[:12]}...)."
        execute_db("""
            INSERT INTO scan_logs (source_id, status, message, extraction_tool, duration_seconds)
            VALUES (?, 'Success', ?, ?, ?)
        """, (source_id, log_msg, tool_used, duration))
        return jsonify({
            "success": True,
            "modified": False,
            "message": log_msg,
            "tool": tool_used,
            "snapshot_id": latest_snapshot['id'],
            "version_tag": latest_snapshot['version_tag']
        })

    # Case B: First snapshot or New modifications detected!
    all_snapshots = query_db("SELECT COUNT(*) as c FROM snapshots WHERE source_id = ?", (source_id,), one=True)['c']
    new_version_tag = f"v{all_snapshots + 1}.0 (Active)"

    new_snap_id = execute_db("""
        INSERT INTO snapshots (source_id, version_tag, content, content_hash, extraction_method)
        VALUES (?, ?, ?, ?, ?)
    """, (source_id, new_version_tag, content, content_hash, tool_used))

    detected_changes = []
    if latest_snapshot:
        # Detect syntactic diffs
        diff_items = DiffService.detect_changes(latest_snapshot['content'], content)

        for diff in diff_items:
            # AI-assisted semantic classification and explanation
            ai_res = AIAnalysisService.analyze_change(
                section_name=diff['affected_section'],
                previous_content=diff['previous_content'],
                updated_content=diff['updated_content'],
                change_type=diff['change_type']
            )

            change_id = execute_db("""
                INSERT INTO changes (
                    source_id, old_snapshot_id, new_snapshot_id, change_type,
                    affected_section, previous_content, updated_content, category,
                    ai_summary, privacy_implications, severity, review_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
            """, (
                source_id, latest_snapshot['id'], new_snap_id, diff['change_type'],
                diff['affected_section'], diff['previous_content'], diff['updated_content'],
                ai_res['category'], ai_res['ai_summary'], ai_res['privacy_implications'],
                ai_res['severity']
            ))
            detected_changes.append({
                "id": change_id,
                "change_type": diff['change_type'],
                "affected_section": diff['affected_section'],
                "category": ai_res['category'],
                "ai_summary": ai_res['ai_summary'],
                "severity": ai_res['severity']
            })

    execute_db("""
        UPDATE sources SET last_scanned_at = CURRENT_TIMESTAMP, last_status = 'Success' WHERE id = ?
    """, (source_id,))

    change_note = f"Found and classified {len(detected_changes)} changes." if detected_changes else "Initial baseline snapshot created."
    log_msg = f"Extracted document ({len(content.split())} words) via {tool_used}. {change_note}"
    execute_db("""
        INSERT INTO scan_logs (source_id, status, message, extraction_tool, duration_seconds)
        VALUES (?, 'Success', ?, ?, ?)
    """, (source_id, log_msg, tool_used, duration))

    return jsonify({
        "success": True,
        "modified": bool(detected_changes),
        "message": log_msg,
        "tool": tool_used,
        "snapshot_id": new_snap_id,
        "version_tag": new_version_tag,
        "detected_changes_count": len(detected_changes),
        "detected_changes": detected_changes
    })

@bp.route('/api/sources/<int:source_id>/logs', methods=['GET'])
def get_source_logs_api(source_id):
    logs = query_db("""
        SELECT * FROM scan_logs WHERE source_id = ? ORDER BY created_at DESC LIMIT 50
    """, (source_id,))
    return jsonify({"success": True, "logs": logs})
