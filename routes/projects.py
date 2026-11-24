import json
from flask import Blueprint, render_template, request, jsonify
from database import query_db, execute_db

bp = Blueprint('projects', __name__)

@bp.route('/project')
def project_page():
    project = query_db("SELECT * FROM project_details LIMIT 1", one=True)
    if project:
        try:
            project['objectives_list'] = json.loads(project['objectives'])
        except Exception:
            project['objectives_list'] = [project['objectives']]
        try:
            project['technologies_list'] = json.loads(project['technologies'])
        except Exception:
            project['technologies_list'] = []
    return render_template('project.html', project=project)

@bp.route('/api/project', methods=['GET'])
def get_project_api():
    project = query_db("SELECT * FROM project_details LIMIT 1", one=True)
    if not project:
        return jsonify({"success": False, "error": "Project not found"}), 404
    try:
        project['objectives'] = json.loads(project['objectives'])
    except Exception:
        pass
    try:
        project['technologies'] = json.loads(project['technologies'])
    except Exception:
        pass
    return jsonify({"success": True, "project": project})

@bp.route('/api/project', methods=['PUT', 'POST'])
def update_project_api():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    problem_statement = data.get('problem_statement', '').strip()
    proposed_solution = data.get('proposed_solution', '').strip()
    objectives = data.get('objectives')
    scope = data.get('scope', '').strip()
    technologies = data.get('technologies')

    if not title or not description:
        return jsonify({"success": False, "error": "Title and description are required"}), 400

    obj_str = json.dumps(objectives) if isinstance(objectives, list) else str(objectives)
    tech_str = json.dumps(technologies) if isinstance(technologies, list) else str(technologies)

    execute_db("""
        UPDATE project_details SET
            title = ?,
            description = ?,
            problem_statement = ?,
            proposed_solution = ?,
            objectives = ?,
            scope = ?,
            technologies = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    """, (title, description, problem_statement, proposed_solution, obj_str, scope, tech_str))

    return jsonify({"success": True, "message": "Project details updated successfully."})
