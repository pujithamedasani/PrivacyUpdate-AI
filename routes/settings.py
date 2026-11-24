from flask import Blueprint, jsonify, request
from config import Config, reload_env
from services.firecrawl_service import FirecrawlService
from services.ai_analysis_service import AIAnalysisService
import requests

bp = Blueprint('settings', __name__)

@bp.route('/api/settings/status')
def get_settings_status():
    reload_env()
    firecrawl_ok = FirecrawlService.is_configured()
    openai_ok = AIAnalysisService.is_configured()
    client, model_name, provider_label = AIAnalysisService.get_client()
    
    return jsonify({
        "success": True,
        "firecrawl": {
            "configured": firecrawl_ok,
            "status_label": "Configured (Active API Scraper)" if firecrawl_ok else "Not Configured (Using Direct Scraper)",
            "api_url": Config.FIRECRAWL_API_URL
        },
        "openai": {
            "configured": openai_ok,
            "status_label": f"Configured ({provider_label})" if openai_ok else "Not Configured (Using Rule-based Classifier)",
            "model": model_name or "gpt-4o-mini",
            "provider": provider_label
        },
        "memento": {
            "configured": True,
            "status_label": "Active (RFC 7089 & Wayback CDX)",
            "endpoint": Config.MEMENTO_TIMEMAP_URL
        }
    })

@bp.route('/api/settings/test-connection', methods=['POST'])
def test_connection_api():
    reload_env()
    target = (request.get_json() or {}).get('target')
    
    if target == 'firecrawl':
        if not FirecrawlService.is_configured():
            return jsonify({"success": False, "error": "FIRECRAWL_API_KEY is not configured in .env."})
        try:
            headers = {"Authorization": f"Bearer {FirecrawlService.get_api_key()}"}
            # Test pinging Firecrawl API
            res = requests.get(Config.FIRECRAWL_API_URL, headers=headers, timeout=8)
            # Any HTTP status (even 401 or 404 or 200) means endpoint is reachable
            if res.status_code in [200, 401, 403]:
                if res.status_code == 401:
                    return jsonify({"success": False, "error": "Firecrawl API key is invalid or rejected by Firecrawl servers."})
                return jsonify({"success": True, "message": "Firecrawl API authenticated successfully."})
            return jsonify({"success": True, "message": "Firecrawl endpoint is reachable."})
        except Exception as e:
            return jsonify({"success": False, "error": f"Firecrawl connection failed: {str(e)}"})

    elif target == 'memento':
        try:
            res = requests.get("https://web.archive.org/cdx/search/cdx?url=example.com&limit=1&output=json", timeout=8)
            if res.status_code == 200:
                return jsonify({"success": True, "message": "Memento / Wayback CDX service is responsive."})
            return jsonify({"success": False, "error": f"Memento returned status {res.status_code}"})
        except Exception as e:
            return jsonify({"success": False, "error": f"Memento connection failed: {str(e)}"})

    elif target == 'openai':
        if not AIAnalysisService.is_configured():
            return jsonify({"success": False, "error": "OPENAI_API_KEY is not configured in .env."})
        try:
            client, model_name, provider_label = AIAnalysisService.get_client()
            if not client:
                return jsonify({"success": False, "error": "Unable to initialize AI client."})
            # Quick lightweight check against the appropriate provider
            models = client.models.list()
            return jsonify({
                "success": True, 
                "message": f"{provider_label} authentication successful! Models accessible."
            })
        except Exception as e:
            err_str = str(e)
            if "Incorrect API key" in err_str and "gsk_" in err_str:
                err_str = (
                    "Error code 401: You supplied a Groq API key (starts with 'gsk_'). "
                    "We have configured the backend to connect directly to Groq (https://api.groq.com/openai/v1). "
                    f"Details: {err_str}"
                )
            return jsonify({"success": False, "error": f"AI Engine connection error: {err_str}"})

    return jsonify({"success": False, "error": "Invalid target specified."}), 400
