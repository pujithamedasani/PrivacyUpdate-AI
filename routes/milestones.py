from flask import Blueprint, render_template, request, jsonify
from database import query_db, execute_db

bp = Blueprint('milestones', __name__)

def update_milestone_progress(milestone_id):
    """Recalculate completion percentage of a milestone based on its tasks."""
    tasks = query_db("SELECT status FROM tasks WHERE milestone_id = ?", (milestone_id,))
    if not tasks:
        return
    weights = {'Done': 100, 'In Review': 75, 'In Progress': 50, 'To Do': 0}
    total_score = sum(weights.get(t['status'], 0) for t in tasks)
    avg_pct = round(total_score / len(tasks))
    
    status = 'Completed' if avg_pct == 100 else ('In Progress' if avg_pct > 0 else 'To Do')
    execute_db("""
        UPDATE milestones SET completion_percentage = ?, status = ? WHERE id = ?
    """, (avg_pct, status, milestone_id))

@bp.route('/milestones')
def milestones_page():
    milestones = query_db("SELECT * FROM milestones ORDER BY id ASC")
    
    # Attach tasks to each milestone
    for m in milestones:
        m['tasks'] = query_db("""
            SELECT t.*
            FROM tasks t
            WHERE t.milestone_id = ?
            ORDER BY t.id ASC
        """, (m['id'],))

    # All tasks for JSON / Kanban
    all_tasks = query_db("""
        SELECT t.*, m.title as milestone_title
        FROM tasks t
        JOIN milestones m ON t.milestone_id = m.id
        ORDER BY t.id ASC
    """)

    return render_template(
        'milestones.html',
        milestones=milestones,
        all_tasks=all_tasks
    )

@bp.route('/api/milestones', methods=['GET'])
def get_milestones_api():
    milestones = query_db("SELECT * FROM milestones ORDER BY id ASC")
    for m in milestones:
        m['tasks'] = query_db("SELECT * FROM tasks WHERE milestone_id = ? ORDER BY id ASC", (m['id'],))
    return jsonify({"success": True, "milestones": milestones})

@bp.route('/api/milestones/<int:milestone_id>', methods=['PUT'])
def edit_milestone_api(milestone_id):
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    start_date = data.get('start_date')
    due_date = data.get('due_date')
    status = data.get('status', 'In Progress')

    if not title or not start_date or not due_date:
        return jsonify({"success": False, "error": "Title, start date, and due date are required."}), 400

    execute_db("""
        UPDATE milestones SET
            title = ?, description = ?, start_date = ?, due_date = ?, status = ?
        WHERE id = ?
    """, (title, description, start_date, due_date, status, milestone_id))

    return jsonify({"success": True, "message": "Milestone updated successfully."})

@bp.route('/api/tasks', methods=['GET'])
def get_tasks_api():
    tasks = query_db("""
        SELECT t.*, m.title as milestone_title
        FROM tasks t
        JOIN milestones m ON t.milestone_id = m.id
        ORDER BY t.id ASC
    """)
    return jsonify({"success": True, "tasks": tasks})

@bp.route('/api/tasks', methods=['POST'])
def add_task_api():
    data = request.get_json() or {}
    milestone_id = data.get('milestone_id')
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    priority = data.get('priority', 'Medium')
    start_date = data.get('start_date')
    due_date = data.get('due_date')
    status = data.get('status', 'To Do')

    if not milestone_id or not name:
        return jsonify({"success": False, "error": "Milestone ID and task name are required."}), 400

    task_id = execute_db("""
        INSERT INTO tasks (milestone_id, name, description, priority, start_date, due_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (milestone_id, name, description, priority, start_date, due_date, status))

    update_milestone_progress(milestone_id)
    return jsonify({"success": True, "task_id": task_id, "message": "Task created successfully."})

@bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
def edit_task_api(task_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    priority = data.get('priority', 'Medium')
    start_date = data.get('start_date')
    due_date = data.get('due_date')
    status = data.get('status', 'To Do')
    milestone_id = data.get('milestone_id')

    task = query_db("SELECT milestone_id FROM tasks WHERE id = ?", (task_id,), one=True)
    if not task:
        return jsonify({"success": False, "error": "Task not found."}), 404

    current_milestone_id = milestone_id or task['milestone_id']

    execute_db("""
        UPDATE tasks SET
            milestone_id = ?, name = ?, description = ?,
            priority = ?, start_date = ?, due_date = ?, status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (current_milestone_id, name, description, priority, start_date, due_date, status, task_id))

    update_milestone_progress(current_milestone_id)
    if task['milestone_id'] != current_milestone_id:
        update_milestone_progress(task['milestone_id'])

    return jsonify({"success": True, "message": "Task updated successfully."})

@bp.route('/api/tasks/<int:task_id>/status', methods=['PATCH', 'POST'])
def update_task_status_api(task_id):
    data = request.get_json() or {}
    new_status = data.get('status')

    if new_status not in ['To Do', 'In Progress', 'In Review', 'Done']:
        return jsonify({"success": False, "error": "Invalid status value."}), 400

    task = query_db("SELECT milestone_id FROM tasks WHERE id = ?", (task_id,), one=True)
    if not task:
        return jsonify({"success": False, "error": "Task not found."}), 404

    execute_db("UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, task_id))
    update_milestone_progress(task['milestone_id'])

    milestone = query_db("SELECT id, completion_percentage, status FROM milestones WHERE id = ?", (task['milestone_id'],), one=True)

    return jsonify({
        "success": True,
        "task_id": task_id,
        "status": new_status,
        "milestone_progress": milestone['completion_percentage'],
        "milestone_status": milestone['status']
    })

@bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task_api(task_id):
    task = query_db("SELECT milestone_id, name FROM tasks WHERE id = ?", (task_id,), one=True)
    if not task:
        return jsonify({"success": False, "error": "Task not found."}), 404

    execute_db("DELETE FROM tasks WHERE id = ?", (task_id,))
    update_milestone_progress(task['milestone_id'])

    return jsonify({"success": True, "message": f"Task '{task['name']}' deleted successfully."})
