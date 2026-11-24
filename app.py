import json
from datetime import datetime
from flask import Flask, render_template, g
from config import Config
from database import close_db, init_db, query_db
from seed import seed_database

# Import blueprints
from routes.dashboard import bp as dashboard_bp
from routes.projects import bp as projects_bp
from routes.sources import bp as sources_bp
from routes.snapshots import bp as snapshots_bp
from routes.changes import bp as changes_bp
from routes.reviews import bp as reviews_bp
from routes.team import bp as team_bp
from routes.deliverables import bp as deliverables_bp
from routes.resources import bp as resources_bp
from routes.reports import bp as reports_bp
from routes.settings import bp as settings_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.ensure_directories()

    # Ensure database is initialized and seeded
    init_db()
    seed_database(force=False)

    # Register teardown
    app.teardown_appcontext(close_db)

    # Template filters
    @app.template_filter('datetime_format')
    def datetime_format(value, format="%b %d, %Y %H:%M"):
        if not value:
            return "N/A"
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            else:
                dt = value
            return dt.strftime(format)
        except Exception:
            return str(value)

    @app.template_filter('date_format')
    def date_format(value, format="%b %d, %Y"):
        if not value:
            return "N/A"
        try:
            if isinstance(value, str):
                dt = datetime.strptime(value[:10], "%Y-%m-%d")
            else:
                dt = value
            return dt.strftime(format)
        except Exception:
            return str(value)

    @app.template_filter('from_json')
    def from_json_filter(val):
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return []

    # Global context processor for sidebar counts and status
    @app.context_processor
    def inject_global_data():
        try:
            pending_reviews = query_db("SELECT COUNT(*) as c FROM changes WHERE review_status = 'Pending'", one=True)['c']
            active_sources = query_db("SELECT COUNT(*) as c FROM sources WHERE is_active = 1", one=True)['c']
            return {
                "global_pending_reviews": pending_reviews,
                "global_active_sources": active_sources,
                "current_year": datetime.now().year
            }
        except Exception:
            return {
                "global_pending_reviews": 0,
                "global_active_sources": 0,
                "current_year": datetime.now().year
            }

    # Register all application blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(sources_bp)
    app.register_blueprint(snapshots_bp)
    app.register_blueprint(changes_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(deliverables_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html', error=str(e)), 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
