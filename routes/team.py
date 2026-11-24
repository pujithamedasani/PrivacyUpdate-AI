from flask import Blueprint, render_template, request, jsonify
from database import query_db, execute_db

bp = Blueprint('team', __name__)

@bp.route('/team')
def team_page():
    members = query_db("""
        SELECT tm.*,
               COUNT(DISTINCT t.id) as assigned_tasks_count,
               COUNT(DISTINCT d.id) as assigned_deliverables_count
        FROM team_members tm
        LEFT JOIN tasks t ON tm.id = t.assigned_to
        LEFT JOIN deliverables d ON tm.id = d.assigned_to
        GROUP BY tm.id
        ORDER BY tm.id ASC
    """)
    for m in members:
        m['tasks'] = query_db("SELECT id, name, priority, status FROM tasks WHERE assigned_to = ?", (m['id'],))
        m['deliverables'] = query_db("SELECT id, week_number, title, status FROM deliverables WHERE assigned_to = ?", (m['id'],))

    return render_template('team.html', members=members)

@bp.route('/api/team', methods=['GET'])
def get_team_api():
    members = query_db("""
        SELECT tm.*,
               COUNT(DISTINCT t.id) as assigned_tasks_count
        FROM team_members tm
        LEFT JOIN tasks t ON tm.id = t.assigned_to
        GROUP BY tm.id
        ORDER BY tm.id ASC
    """)
    return jsonify({"success": True, "members": members})

@bp.route('/api/team', methods=['POST'])
def add_member_api():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    reg_number = data.get('reg_number', '').strip()
    role = data.get('role', '').strip()
    email = data.get('email', '').strip()
    responsibilities = data.get('responsibilities', '').strip()

    if not name or not role:
        return jsonify({"success": False, "error": "Member name and role are required."}), 400

    member_id = execute_db("""
        INSERT INTO team_members (name, reg_number, role, email, responsibilities)
        VALUES (?, ?, ?, ?, ?)
    """, (name, reg_number, role, email, responsibilities))

    return jsonify({"success": True, "member_id": member_id, "message": "Team member added successfully."})

@bp.route('/api/team/<int:member_id>', methods=['PUT'])
def edit_member_api(member_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    reg_number = data.get('reg_number', '').strip()
    role = data.get('role', '').strip()
    email = data.get('email', '').strip()
    responsibilities = data.get('responsibilities', '').strip()

    if not name or not role:
        return jsonify({"success": False, "error": "Member name and role are required."}), 400

    execute_db("""
        UPDATE team_members SET
            name = ?, reg_number = ?, role = ?, email = ?, responsibilities = ?
        WHERE id = ?
    """, (name, reg_number, role, email, responsibilities, member_id))

    return jsonify({"success": True, "message": "Team member updated successfully."})

@bp.route('/api/team/<int:member_id>', methods=['DELETE'])
def delete_member_api(member_id):
    member = query_db("SELECT name FROM team_members WHERE id = ?", (member_id,), one=True)
    if not member:
        return jsonify({"success": False, "error": "Team member not found."}), 404

    execute_db("DELETE FROM team_members WHERE id = ?", (member_id,))
    return jsonify({"success": True, "message": f"Team member '{member['name']}' removed."})
