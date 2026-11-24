from flask import Blueprint, render_template, request, jsonify
from database import query_db, execute_db
from services.diff_service import DiffService
from services.ai_analysis_service import AIAnalysisService, VALID_CATEGORIES

bp = Blueprint('changes', __name__)

@bp.route('/changes')
def changes_page():
    source_id = request.args.get('source_id', type=int)
    category = request.args.get('category')
    status = request.args.get('status')
    severity = request.args.get('severity')

    query = """
        SELECT c.*, s.name as source_name, s.url as source_url,
               r.reviewer_name, r.decision as review_decision, r.comments as review_comments, r.reviewed_at
        FROM changes c
        JOIN sources s ON c.source_id = s.id
        LEFT JOIN reviews r ON c.id = r.change_id
        WHERE 1=1
    """
    params = []

    if source_id:
        query += " AND c.source_id = ?"
        params.append(source_id)
    if category:
        query += " AND c.category = ?"
        params.append(category)
    if status:
        query += " AND c.review_status = ?"
        params.append(status)
    if severity:
        query += " AND c.severity = ?"
        params.append(severity)

    query += " ORDER BY c.detected_at DESC"
    changes = query_db(query, tuple(params))

    sources = query_db("SELECT id, name FROM sources ORDER BY name ASC")
    ai_configured = AIAnalysisService.is_configured()

    return render_template(
        'changes.html',
        changes=changes,
        sources=sources,
        categories=VALID_CATEGORIES,
        selected_source_id=source_id,
        selected_category=category,
        selected_status=status,
        selected_severity=severity,
        ai_configured=ai_configured
    )

@bp.route('/api/changes', methods=['GET'])
def get_changes_api():
    changes = query_db("""
        SELECT c.*, s.name as source_name, s.url as source_url,
               r.reviewer_name, r.decision, r.comments as review_comments, r.reviewed_at
        FROM changes c
        JOIN sources s ON c.source_id = s.id
        LEFT JOIN reviews r ON c.id = r.change_id
        ORDER BY c.detected_at DESC
    """)
    return jsonify({"success": True, "changes": changes})

@bp.route('/api/changes/<int:change_id>', methods=['GET'])
def get_single_change_api(change_id):
    change = query_db("""
        SELECT c.*, s.name as source_name, s.url as source_url,
               r.reviewer_name, r.decision, r.comments as review_comments, r.reviewed_at
        FROM changes c
        JOIN sources s ON c.source_id = s.id
        LEFT JOIN reviews r ON c.id = r.change_id
        WHERE c.id = ?
    """, (change_id,), one=True)
    if not change:
        return jsonify({"success": False, "error": "Change record not found."}), 404
    return jsonify({"success": True, "change": change})

@bp.route('/api/changes/analyze-pair', methods=['POST'])
def analyze_snapshot_pair_api():
    """Manually run diff and AI analysis between two existing snapshot records."""
    data = request.get_json() or {}
    old_snap_id = data.get('old_snapshot_id')
    new_snap_id = data.get('new_snapshot_id')

    if not old_snap_id or not new_snap_id:
        return jsonify({"success": False, "error": "Both old_snapshot_id and new_snapshot_id are required."}), 400

    old_snap = query_db("SELECT * FROM snapshots WHERE id = ?", (old_snap_id,), one=True)
    new_snap = query_db("SELECT * FROM snapshots WHERE id = ?", (new_snap_id,), one=True)

    if not old_snap or not new_snap:
        return jsonify({"success": False, "error": "One or both snapshots could not be found."}), 404

    diff_items = DiffService.detect_changes(old_snap['content'], new_snap['content'])
    if not diff_items:
        return jsonify({"success": True, "changes_created": 0, "message": "No textual differences detected between selected snapshots."})

    created_ids = []
    source_id = new_snap['source_id']

    for diff in diff_items:
        ai_res = AIAnalysisService.analyze_change(
            section_name=diff['affected_section'],
            previous_content=diff['previous_content'],
            updated_content=diff['updated_content'],
            change_type=diff['change_type']
        )

        cid = execute_db("""
            INSERT INTO changes (
                source_id, old_snapshot_id, new_snapshot_id, change_type,
                affected_section, previous_content, updated_content, category,
                ai_summary, privacy_implications, severity, review_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (
            source_id, old_snap_id, new_snap_id, diff['change_type'],
            diff['affected_section'], diff['previous_content'], diff['updated_content'],
            ai_res['category'], ai_res['ai_summary'], ai_res['privacy_implications'],
            ai_res['severity']
        ))
        created_ids.append(cid)

    return jsonify({
        "success": True,
        "changes_created": len(created_ids),
        "change_ids": created_ids,
        "message": f"Successfully analyzed diff and generated {len(created_ids)} classified change records."
    })
