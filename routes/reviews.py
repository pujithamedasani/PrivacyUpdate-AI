from flask import Blueprint, render_template, request, jsonify
from database import query_db, execute_db

bp = Blueprint('reviews', __name__)

@bp.route('/reviews')
def reviews_page():
    status = request.args.get('status', 'Pending')
    
    # Fetch team members for the reviewer dropdown (Pujitha Medasani by default)
    team_members = query_db("SELECT id, name, role FROM team_members ORDER BY CASE WHEN name = 'Pujitha Medasani' THEN 0 ELSE 1 END, id ASC")

    # Fetch changes according to filter
    if status == 'All':
        changes = query_db("""
            SELECT c.*, s.name as source_name, s.url as source_url,
                   r.reviewer_name, r.decision, r.comments as review_comments, r.reviewed_at
            FROM changes c
            JOIN sources s ON c.source_id = s.id
            LEFT JOIN reviews r ON c.id = r.change_id
            ORDER BY c.detected_at DESC
        """)
    else:
        changes = query_db("""
            SELECT c.*, s.name as source_name, s.url as source_url,
                   r.reviewer_name, r.decision, r.comments as review_comments, r.reviewed_at
            FROM changes c
            JOIN sources s ON c.source_id = s.id
            LEFT JOIN reviews r ON c.id = r.change_id
            WHERE c.review_status = ?
            ORDER BY c.detected_at DESC
        """, (status,))

    # Counts
    pending_count = query_db("SELECT COUNT(*) as c FROM changes WHERE review_status = 'Pending'", one=True)['c']
    approved_count = query_db("SELECT COUNT(*) as c FROM changes WHERE review_status = 'Approved'", one=True)['c']
    flagged_count = query_db("SELECT COUNT(*) as c FROM changes WHERE review_status IN ('Flagged', 'Rejected')", one=True)['c']

    # Full audit history
    review_history = query_db("""
        SELECT r.*, c.affected_section, c.category, c.severity, s.name as source_name
        FROM reviews r
        JOIN changes c ON r.change_id = c.id
        JOIN sources s ON c.source_id = s.id
        ORDER BY r.reviewed_at DESC
        LIMIT 25
    """)

    return render_template(
        'reviews.html',
        changes=changes,
        team_members=team_members,
        selected_status=status,
        pending_count=pending_count,
        approved_count=approved_count,
        flagged_count=flagged_count,
        review_history=review_history
    )

@bp.route('/api/reviews/submit', methods=['POST'])
def submit_review_api():
    data = request.get_json() or {}
    change_id = data.get('change_id')
    reviewer_name = data.get('reviewer_name', '').strip()
    reviewer_id = data.get('reviewer_id')
    decision = data.get('decision', '').strip()  # 'Approved', 'Flagged', 'Rejected'
    comments = data.get('comments', '').strip()

    if not change_id or not reviewer_name or not decision:
        return jsonify({"success": False, "error": "Change ID, reviewer name, and decision are required."}), 400

    if decision not in ['Approved', 'Flagged', 'Rejected']:
        return jsonify({"success": False, "error": "Decision must be 'Approved', 'Flagged', or 'Rejected'."}), 400

    change = query_db("SELECT * FROM changes WHERE id = ?", (change_id,), one=True)
    if not change:
        return jsonify({"success": False, "error": "Change record not found."}), 404

    # Insert or update review record
    existing_review = query_db("SELECT id FROM reviews WHERE change_id = ?", (change_id,), one=True)
    if existing_review:
        execute_db("""
            UPDATE reviews SET
                reviewer_name = ?,
                reviewer_id = ?,
                decision = ?,
                comments = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reviewer_name, reviewer_id, decision, comments, existing_review['id']))
        review_id = existing_review['id']
    else:
        review_id = execute_db("""
            INSERT INTO reviews (change_id, reviewer_name, reviewer_id, decision, comments)
            VALUES (?, ?, ?, ?, ?)
        """, (change_id, reviewer_name, reviewer_id, decision, comments))

    # Update change status
    execute_db("UPDATE changes SET review_status = ? WHERE id = ?", (decision, change_id))

    return jsonify({
        "success": True,
        "review_id": review_id,
        "decision": decision,
        "message": f"Review marked as {decision} by {reviewer_name}."
    })

@bp.route('/api/reviews/history', methods=['GET'])
def get_review_history_api():
    history = query_db("""
        SELECT r.*, c.affected_section, c.category, c.severity, s.name as source_name
        FROM reviews r
        JOIN changes c ON r.change_id = c.id
        JOIN sources s ON c.source_id = s.id
        ORDER BY r.reviewed_at DESC
        LIMIT 50
    """)
    return jsonify({"success": True, "history": history})
