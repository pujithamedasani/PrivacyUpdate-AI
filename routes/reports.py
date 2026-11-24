import io
import csv
import json
from flask import Blueprint, render_template, request, jsonify, Response, send_file
from database import query_db, backup_db

bp = Blueprint('reports', __name__)

@bp.route('/reports')
def reports_page():
    sources = query_db("SELECT id, name FROM sources ORDER BY name ASC")
    return render_template('reports.html', sources=sources)

@bp.route('/api/reports/summary')
def get_reports_summary_api():
    source_id = request.args.get('source_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Base conditions
    source_clause = " WHERE c.source_id = ?" if source_id else ""
    params = [source_id] if source_id else []

    # KPI counts
    total_sources = query_db("SELECT COUNT(*) as c FROM sources", one=True)['c']
    total_snapshots = query_db("SELECT COUNT(*) as c FROM snapshots", one=True)['c']
    total_changes = query_db("SELECT COUNT(*) as c FROM changes", one=True)['c']
    pending_reviews = query_db("SELECT COUNT(*) as c FROM changes WHERE review_status = 'Pending'", one=True)['c']
    approved_reviews = query_db("SELECT COUNT(*) as c FROM changes WHERE review_status = 'Approved'", one=True)['c']
    flagged_reviews = query_db("SELECT COUNT(*) as c FROM changes WHERE review_status IN ('Flagged', 'Rejected')", one=True)['c']

    # Category distribution
    cat_query = f"SELECT c.category, COUNT(*) as cnt FROM changes c {source_clause} GROUP BY c.category ORDER BY cnt DESC"
    categories = {r['category']: r['cnt'] for r in query_db(cat_query, tuple(params))}

    # Severity distribution
    sev_query = f"SELECT c.severity, COUNT(*) as cnt FROM changes c {source_clause} GROUP BY c.severity ORDER BY cnt DESC"
    severities = {r['severity']: r['cnt'] for r in query_db(sev_query, tuple(params))}

    # Sources monitoring summary
    sources_summary = query_db("""
        SELECT s.id, s.name, s.url, s.is_active, s.last_status, s.last_scanned_at,
               COUNT(c.id) as total_changes
        FROM sources s
        LEFT JOIN changes c ON s.id = c.source_id
        GROUP BY s.id
        ORDER BY total_changes DESC
    """)

    # Scan logs activity
    scan_query = """
        SELECT DATE(created_at) as log_date, status, COUNT(*) as cnt
        FROM scan_logs
        GROUP BY DATE(created_at), status
        ORDER BY log_date ASC
        LIMIT 20
    """
    scan_activity = query_db(scan_query)

    return jsonify({
        "success": True,
        "kpis": {
            "total_sources": total_sources,
            "total_snapshots": total_snapshots,
            "total_changes": total_changes,
            "pending_reviews": pending_reviews,
            "approved_reviews": approved_reviews,
            "flagged_reviews": flagged_reviews
        },
        "categories": categories,
        "severities": severities,
        "sources_summary": sources_summary,
        "scan_activity": scan_activity
    })

@bp.route('/api/reports/export/changes')
def export_changes_csv():
    """Export all detected privacy changes to CSV file format."""
    source_id = request.args.get('source_id', type=int)
    query = """
        SELECT c.id, s.name as website_name, s.url, c.change_type, c.affected_section,
               c.category, c.severity, c.review_status, c.ai_summary, c.privacy_implications,
               c.detected_at, r.reviewer_name, r.decision, r.comments as review_comments
        FROM changes c
        JOIN sources s ON c.source_id = s.id
        LEFT JOIN reviews r ON c.id = r.change_id
    """
    params = ()
    if source_id:
        query += " WHERE c.source_id = ?"
        params = (source_id,)
    query += " ORDER BY c.detected_at DESC"

    rows = query_db(query, params)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Change ID", "Website Name", "Policy URL", "Change Type", "Affected Section",
        "Category", "Severity", "Review Status", "AI Summary", "Privacy Implications",
        "Detected Date", "Reviewer Name", "Review Decision", "Review Comments"
    ])

    for r in rows:
        writer.writerow([
            r['id'], r['website_name'], r['url'], r['change_type'], r['affected_section'],
            r['category'], r['severity'], r['review_status'], r['ai_summary'], r['privacy_implications'],
            r['detected_at'], r['reviewer_name'] or "N/A", r['decision'] or "Pending", r['review_comments'] or ""
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=privacyupdate_detected_changes.csv"}
    )

@bp.route('/api/reports/export/json')
def export_full_report_json():
    """Export complete system audit trail and data in JSON."""
    project = query_db("SELECT * FROM project_details LIMIT 1", one=True)
    sources = query_db("SELECT * FROM sources")
    changes = query_db("SELECT * FROM changes")
    reviews = query_db("SELECT * FROM reviews")

    report_payload = {
        "project": project,
        "monitored_sources": sources,
        "detected_changes": changes,
        "human_reviews": reviews
    }

    return Response(
        json.dumps(report_payload, indent=2, default=str),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=privacyupdate_full_report.json"}
    )

@bp.route('/api/backup')
def download_database_backup():
    """Create timestamped SQLite backup and send to user."""
    backup_file = backup_db()
    return send_file(
        str(backup_file),
        as_attachment=True,
        download_name=backup_file.name,
        mimetype="application/x-sqlite3"
    )
