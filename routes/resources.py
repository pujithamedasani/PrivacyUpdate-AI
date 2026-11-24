from flask import Blueprint, render_template, request, jsonify
from database import query_db, execute_db

bp = Blueprint('resources', __name__)

@bp.route('/resources')
def resources_page():
    resources = query_db("SELECT * FROM resources ORDER BY is_system DESC, id ASC")
    return render_template('resources.html', resources=resources)

@bp.route('/api/resources', methods=['GET'])
def get_resources_api():
    resources = query_db("SELECT * FROM resources ORDER BY is_system DESC, id ASC")
    return jsonify({"success": True, "resources": resources})

@bp.route('/api/resources', methods=['POST'])
def add_resource_api():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    description = data.get('description', '').strip()
    doc_url = data.get('doc_url', '').strip()

    if not name or not category or not description:
        return jsonify({"success": False, "error": "Name, category, and description are required."}), 400

    resource_id = execute_db("""
        INSERT INTO resources (name, category, description, doc_url, is_system)
        VALUES (?, ?, ?, ?, 0)
    """, (name, category, description, doc_url))

    return jsonify({"success": True, "resource_id": resource_id, "message": "Resource added successfully."})

@bp.route('/api/resources/<int:resource_id>', methods=['PUT'])
def edit_resource_api(resource_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    description = data.get('description', '').strip()
    doc_url = data.get('doc_url', '').strip()

    if not name or not category or not description:
        return jsonify({"success": False, "error": "Name, category, and description are required."}), 400

    execute_db("""
        UPDATE resources SET
            name = ?, category = ?, description = ?, doc_url = ?
        WHERE id = ?
    """, (name, category, description, doc_url, resource_id))

    return jsonify({"success": True, "message": "Resource updated successfully."})

@bp.route('/api/resources/<int:resource_id>', methods=['DELETE'])
def delete_resource_api(resource_id):
    resource = query_db("SELECT is_system, name FROM resources WHERE id = ?", (resource_id,), one=True)
    if not resource:
        return jsonify({"success": False, "error": "Resource not found."}), 404

    if resource['is_system'] == 1:
        return jsonify({"success": False, "error": "Core system technology stack items cannot be deleted."}), 403

    execute_db("DELETE FROM resources WHERE id = ?", (resource_id,))
    return jsonify({"success": True, "message": f"Resource '{resource['name']}' deleted."})
