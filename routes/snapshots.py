import hashlib
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from database import query_db, execute_db
from services.diff_service import DiffService
from services.memento_service import MementoService

bp = Blueprint('snapshots', __name__)

@bp.route('/snapshots')
def snapshots_page():
    source_id = request.args.get('source_id', type=int)
    sources = query_db("SELECT id, name FROM sources ORDER BY name ASC")
    
    if source_id:
        snapshots = query_db("""
            SELECT sn.*, s.name as source_name, s.url as source_url
            FROM snapshots sn
            JOIN sources s ON sn.source_id = s.id
            WHERE sn.source_id = ?
            ORDER BY sn.snapshot_date DESC
        """, (source_id,))
    else:
        snapshots = query_db("""
            SELECT sn.*, s.name as source_name, s.url as source_url
            FROM snapshots sn
            JOIN sources s ON sn.source_id = s.id
            ORDER BY sn.snapshot_date DESC
        """)

    return render_template('snapshots.html', snapshots=snapshots, sources=sources, selected_source_id=source_id)

@bp.route('/api/snapshots', methods=['GET'])
def get_snapshots_api():
    source_id = request.args.get('source_id', type=int)
    if source_id:
        snapshots = query_db("""
            SELECT sn.*, s.name as source_name, s.url as source_url
            FROM snapshots sn
            JOIN sources s ON sn.source_id = s.id
            WHERE sn.source_id = ?
            ORDER BY sn.snapshot_date DESC
        """, (source_id,))
    else:
        snapshots = query_db("""
            SELECT sn.*, s.name as source_name, s.url as source_url
            FROM snapshots sn
            JOIN sources s ON sn.source_id = s.id
            ORDER BY sn.snapshot_date DESC
        """)
    return jsonify({"success": True, "snapshots": snapshots})

@bp.route('/api/snapshots/<int:snapshot_id>', methods=['GET'])
def get_single_snapshot_api(snapshot_id):
    snapshot = query_db("""
        SELECT sn.*, s.name as source_name, s.url as source_url
        FROM snapshots sn
        JOIN sources s ON sn.source_id = s.id
        WHERE sn.id = ?
    """, (snapshot_id,), one=True)
    if not snapshot:
        return jsonify({"success": False, "error": "Snapshot not found."}), 404
    return jsonify({"success": True, "snapshot": snapshot})

@bp.route('/api/snapshots/compare', methods=['GET'])
def compare_snapshots_api():
    old_id = request.args.get('old_id', type=int)
    new_id = request.args.get('new_id', type=int)

    if not old_id or not new_id:
        return jsonify({"success": False, "error": "Both old_id and new_id are required parameters."}), 400

    old_snap = query_db("SELECT * FROM snapshots WHERE id = ?", (old_id,), one=True)
    new_snap = query_db("SELECT * FROM snapshots WHERE id = ?", (new_id,), one=True)

    if not old_snap or not new_snap:
        return jsonify({"success": False, "error": "One or both snapshots could not be found."}), 404

    similarity = DiffService.compute_similarity(old_snap['content'], new_snap['content'])
    diff_changes = DiffService.detect_changes(old_snap['content'], new_snap['content'])
    html_diff = DiffService.generate_html_diff(old_snap['content'], new_snap['content'])

    return jsonify({
        "success": True,
        "old_snapshot": {
            "id": old_snap['id'],
            "version_tag": old_snap['version_tag'],
            "snapshot_date": old_snap['snapshot_date'],
            "hash": old_snap['content_hash']
        },
        "new_snapshot": {
            "id": new_snap['id'],
            "version_tag": new_snap['version_tag'],
            "snapshot_date": new_snap['snapshot_date'],
            "hash": new_snap['content_hash']
        },
        "similarity": similarity,
        "diff_count": len(diff_changes),
        "changes": diff_changes,
        "html_diff": html_diff
    })

@bp.route('/api/memento/discover', methods=['POST', 'GET'])
def discover_mementos_api():
    """Discover historical captures of a given URL via Memento TimeMap / Wayback CDX."""
    url = request.args.get('url') or (request.get_json() or {}).get('url')
    if not url:
        return jsonify({"success": False, "error": "A target policy URL is required."}), 400

    result = MementoService.get_timemap(url, limit=12)
    return jsonify(result)

@bp.route('/api/memento/import', methods=['POST'])
def import_memento_api():
    """Import a historical Memento snapshot from web archive into local database."""
    data = request.get_json() or {}
    source_id = data.get('source_id')
    memento_uri = data.get('memento_uri')
    memento_date = data.get('memento_date')

    if not source_id or not memento_uri:
        return jsonify({"success": False, "error": "source_id and memento_uri are required."}), 400

    source = query_db("SELECT * FROM sources WHERE id = ?", (source_id,), one=True)
    if not source:
        return jsonify({"success": False, "error": "Source not found."}), 404

    fetch_res = MementoService.fetch_memento_content(memento_uri)
    if not fetch_res['success']:
        return jsonify({"success": False, "error": f"Failed to retrieve archive content: {fetch_res['error']}"}), 502

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(fetch_res['content'], "html.parser")
    for t in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        t.decompose()
    content = soup.get_text(separator="\n", strip=True)

    if not content:
        return jsonify({"success": False, "error": "Extracted archive content was empty."}), 400

    content_hash = hashlib.sha256(content.encode()).hexdigest()
    version_tag = f"Archived ({memento_date[:10] if memento_date else 'Memento'})"

    snap_id = execute_db("""
        INSERT INTO snapshots (source_id, version_tag, content, content_hash, extraction_method, memento_archive_url, snapshot_date)
        VALUES (?, ?, ?, ?, 'Memento Archive', ?, ?)
    """, (source_id, version_tag, content, content_hash, memento_uri, memento_date or datetime.now().isoformat()))

    execute_db("""
        INSERT INTO scan_logs (source_id, status, message, extraction_tool)
        VALUES (?, 'Success', ?, 'Memento')
    """, (source_id, f"Imported historical snapshot {version_tag} from Wayback/Memento."))

    return jsonify({
        "success": True,
        "snapshot_id": snap_id,
        "version_tag": version_tag,
        "message": f"Historical snapshot successfully imported for {source['name']}."
    })
