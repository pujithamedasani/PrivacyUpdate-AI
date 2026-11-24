import json
from flask import Blueprint, render_template, jsonify
from database import query_db

bp = Blueprint('dashboard', __name__)

@bp.route('/')
def index():
    project = query_db("SELECT * FROM project_details LIMIT 1", one=True)
    return render_template('dashboard.html', project=project)

@bp.route('/api/dashboard/stats')
def get_stats():
    # 1. Total counts
    sources_cnt = query_db("SELECT COUNT(*) as c FROM sources", one=True)['c']
    active_sources_cnt = query_db("SELECT COUNT(*) as c FROM sources WHERE is_active = 1", one=True)['c']
    snapshots_cnt = query_db("SELECT COUNT(*) as c FROM snapshots", one=True)['c']
    changes_cnt = query_db("SELECT COUNT(*) as c FROM changes", one=True)['c']
    
    pending_reviews_cnt = query_db("SELECT COUNT(*) as c FROM changes WHERE review_status = 'Pending'", one=True)['c']
    approved_reviews_cnt = query_db("SELECT COUNT(*) as c FROM changes WHERE review_status = 'Approved'", one=True)['c']
    flagged_reviews_cnt = query_db("SELECT COUNT(*) as c FROM changes WHERE review_status IN ('Flagged', 'Rejected')", one=True)['c']

    # 2. Changes severity breakdown (Critical, High, Medium, Low)
    sev_rows = query_db("SELECT severity, COUNT(*) as cnt FROM changes GROUP BY severity")
    severity_dist = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for r in sev_rows:
        if r['severity'] in severity_dist:
            severity_dist[r['severity']] = r['cnt']

    # 3. Changes by Monitored Website
    source_changes_rows = query_db("""
        SELECT s.name, COUNT(c.id) as change_count
        FROM sources s
        LEFT JOIN changes c ON s.id = c.source_id
        GROUP BY s.id
        ORDER BY change_count DESC
        LIMIT 5
    """)
    source_changes = {r['name']: r['change_count'] for r in source_changes_rows}

    # 4. Changes category distribution
    cat_rows = query_db("SELECT category, COUNT(*) as cnt FROM changes GROUP BY category ORDER BY cnt DESC")
    categories = {r['category']: r['cnt'] for r in cat_rows}

    # 5. Reviews distribution
    reviews_dist = {
        "Approved": approved_reviews_cnt,
        "Pending": pending_reviews_cnt,
        "Flagged / Rejected": flagged_reviews_cnt
    }

    # 6. Recent changes with source details
    recent_changes = query_db("""
        SELECT c.*, s.name as source_name, s.url as source_url
        FROM changes c
        JOIN sources s ON c.source_id = s.id
        ORDER BY c.detected_at DESC
        LIMIT 5
    """)

    # 7. Recent scan logs
    recent_logs = query_db("""
        SELECT l.*, s.name as source_name
        FROM scan_logs l
        LEFT JOIN sources s ON l.source_id = s.id
        ORDER BY l.created_at DESC
        LIMIT 6
    """)

    # 8. Activity over time (snapshots and scans)
    timeline_rows = query_db("""
        SELECT DATE(created_at) as log_date, COUNT(*) as scan_count
        FROM scan_logs
        GROUP BY DATE(created_at)
        ORDER BY log_date ASC
        LIMIT 10
    """)
    timeline = [{"date": r['log_date'], "count": r['scan_count']} for r in timeline_rows]

    return jsonify({
        "success": True,
        "summary": {
            "total_sources": sources_cnt,
            "active_sources": active_sources_cnt,
            "total_snapshots": snapshots_cnt,
            "total_changes": changes_cnt,
            "pending_reviews": pending_reviews_cnt,
            "approved_reviews": approved_reviews_cnt,
            "flagged_reviews": flagged_reviews_cnt,
            "critical_changes": severity_dist["Critical"],
            "high_changes": severity_dist["High"]
        },
        "severity_distribution": severity_dist,
        "source_changes": source_changes,
        "categories_distribution": categories,
        "reviews_distribution": reviews_dist,
        "timeline": timeline,
        "recent_changes": recent_changes,
        "recent_logs": recent_logs
    })
