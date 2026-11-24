import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, jsonify, send_from_directory, current_app
from database import query_db, execute_db
from config import Config

bp = Blueprint('deliverables', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@bp.route('/deliverables')
def deliverables_page():
    deliverables = query_db("""
        SELECT d.*, tm.name as member_name, tm.role as member_role
        FROM deliverables d
        LEFT JOIN team_members tm ON d.assigned_to = tm.id
        ORDER BY d.week_number ASC
    """)
    team_members = query_db("SELECT id, name, role FROM team_members ORDER BY CASE WHEN name = 'Pujitha Medasani' THEN 0 ELSE 1 END, id ASC")
    return render_template('deliverables.html', deliverables=deliverables, team_members=team_members)

@bp.route('/api/deliverables', methods=['GET'])
def get_deliverables_api():
    deliverables = query_db("""
        SELECT d.*, tm.name as member_name, tm.role as member_role
        FROM deliverables d
        LEFT JOIN team_members tm ON d.assigned_to = tm.id
        ORDER BY d.week_number ASC
    """)
    return jsonify({"success": True, "deliverables": deliverables})

@bp.route('/api/deliverables/<int:deliverable_id>', methods=['PUT'])
def edit_deliverable_api(deliverable_id):
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    deadline = data.get('deadline')
    assigned_to = data.get('assigned_to')
    status = data.get('status', 'Pending')

    if not title or not deadline:
        return jsonify({"success": False, "error": "Title and deadline are required."}), 400

    execute_db("""
        UPDATE deliverables SET
            title = ?, description = ?, deadline = ?, assigned_to = ?, status = ?
        WHERE id = ?
    """, (title, description, deadline, assigned_to, status, deliverable_id))

    return jsonify({"success": True, "message": "Deliverable updated successfully."})

@bp.route('/api/deliverables/<int:deliverable_id>/upload', methods=['POST'])
def upload_deliverable_file(deliverable_id):
    deliverable = query_db("SELECT * FROM deliverables WHERE id = ?", (deliverable_id,), one=True)
    if not deliverable:
        return jsonify({"success": False, "error": "Deliverable record not found."}), 404

    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file payload found in request."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file."}), 400

    if not allowed_file(file.filename):
        exts = ", ".join(sorted(Config.ALLOWED_EXTENSIONS))
        return jsonify({"success": False, "error": f"Invalid file extension. Allowed extensions are: {exts}"}), 400

    Config.ensure_directories()
    raw_name = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stored_filename = f"week_{deliverable['week_number']}_{timestamp}_{raw_name}"
    save_path = Config.UPLOAD_FOLDER / stored_filename
    
    file.save(str(save_path))

    # Update database record
    execute_db("""
        UPDATE deliverables SET
            file_path = ?,
            file_name = ?,
            submission_date = CURRENT_TIMESTAMP,
            status = 'Submitted'
        WHERE id = ?
    """, (stored_filename, raw_name, deliverable_id))

    return jsonify({
        "success": True,
        "message": f"File '{raw_name}' uploaded successfully. Status updated to 'Submitted'.",
        "file_name": raw_name,
        "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@bp.route('/api/deliverables/<int:deliverable_id>/download', methods=['GET'])
def download_deliverable_file(deliverable_id):
    deliverable = query_db("SELECT * FROM deliverables WHERE id = ?", (deliverable_id,), one=True)
    if not deliverable or not deliverable['file_path']:
        return jsonify({"success": False, "error": "No submission file available for this deliverable."}), 404

    file_path = Config.UPLOAD_FOLDER / deliverable['file_path']
    if not file_path.exists():
        return jsonify({"success": False, "error": "File was not found on server disk."}), 404

    return send_from_directory(
        directory=str(Config.UPLOAD_FOLDER),
        path=deliverable['file_path'],
        as_attachment=True,
        download_name=deliverable['file_name'] or deliverable['file_path']
    )
