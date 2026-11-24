import json
import os
from config import Config

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

VALID_CATEGORIES = [
    "Data collection",
    "Data sharing",
    "Cookies and tracking",
    "User rights",
    "Data retention",
    "Security",
    "Third-party services",
    "Policy updates"
]

class AIAnalysisService:
    """
    AI-powered service for semantic analysis of privacy policy diffs.
    Supports both OpenAI (GPT-4o-mini) and Groq (LLaMA-3.3-70b) seamlessly
    via OpenAI-compatible API specifications.
    Classifies changes into 8 standard privacy dimensions, generates human-digestible
    summaries, and computes potential risk implications.
    """

    @classmethod
    def get_api_key(cls):
        return Config.get_openai_api_key()

    @classmethod
    def get_model(cls):
        return Config.get_openai_model()

    @classmethod
    def is_configured(cls):
        key = cls.get_api_key()
        return bool(key and len(key) > 5 and OpenAI is not None)

    @classmethod
    def is_groq(cls):
        key = cls.get_api_key()
        return bool(key and key.startswith("gsk_"))

    @classmethod
    def get_client(cls):
        """
        Dynamically returns (client, model_name, provider_label).
        Auto-detects Groq API keys (gsk_...) vs OpenAI keys (sk-...).
        """
        if not OpenAI:
            return None, None, "OpenAI SDK Not Installed"
        key = cls.get_api_key()
        if not key:
            return None, None, "Unconfigured"

        if key.startswith("gsk_"):
            # Groq API endpoint (100% OpenAI-compatible)
            client = OpenAI(
                api_key=key,
                base_url="https://api.groq.com/openai/v1"
            )
            configured_model = cls.get_model()
            if configured_model:
                model = configured_model
            else:
                model = "qwen/qwen3.8-27b"
            return client, model, f"Groq ({model})"
        else:
            # Standard OpenAI endpoint
            base_url = os.getenv("OPENAI_BASE_URL", None)
            client = OpenAI(api_key=key, base_url=base_url) if base_url else OpenAI(api_key=key)
            model = cls.get_model()
            return client, model, f"OpenAI ({model})"

    @classmethod
    def analyze_change(cls, section_name: str, previous_content: str, updated_content: str, change_type: str = "Modified"):
        """
        Analyze a specific change hunk.
        Returns a dictionary:
        {
            "category": str,
            "ai_summary": str,
            "privacy_implications": str,
            "severity": "Low" | "Medium" | "High" | "Critical",
            "is_ai_generated": bool,
            "model_used": str
        }
        """
        # If AI engine is configured, invoke actual model
        if cls.is_configured():
            client, primary_model, provider_label = cls.get_client()
            prompt = f"""
You are an expert privacy attorney and data protection compliance analyst.
Analyze the following change in a website's privacy policy:

Section: {section_name}
Change Type: {change_type}

--- PREVIOUS CONTENT ---
{previous_content or "(None - New Section)"}

--- UPDATED CONTENT ---
{updated_content or "(None - Section Removed)"}

Provide your analysis in strictly valid JSON format with the following four keys:
1. "category": Must be exactly one of: {json.dumps(VALID_CATEGORIES)}
2. "ai_summary": A clear 1-2 sentence plain-English summary of what specifically changed.
3. "privacy_implications": A 1-2 sentence assessment of how this change impacts user privacy, permissions, or compliance risk.
4. "severity": One of ["Low", "Medium", "High", "Critical"].

Output ONLY the JSON object, with no markdown code blocks or surrounding text.
"""
            # Candidate models to try in case of model deprecation/404
            models_to_try = [primary_model] if primary_model else []
            if cls.is_groq():
                for fallback_m in ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.1-8b-instant"]:
                    if fallback_m not in models_to_try:
                        models_to_try.append(fallback_m)

            last_error = None
            for model_candidate in models_to_try:
                try:
                    response = client.chat.completions.create(
                        model=model_candidate,
                        messages=[
                            {"role": "system", "content": "You are a precise data privacy compliance analyzer returning structured JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2,
                        max_tokens=400
                    )

                    content_raw = response.choices[0].message.content.strip()
                    # Clean any markdown code blocks if model included them
                    if content_raw.startswith("```"):
                        content_raw = content_raw.strip("`").replace("json\n", "", 1).strip()

                    parsed = json.loads(content_raw)
                    category = parsed.get("category", "Policy updates")
                    if category not in VALID_CATEGORIES:
                        category = "Policy updates"

                    severity = parsed.get("severity", "Medium")
                    if severity not in ["Low", "Medium", "High", "Critical"]:
                        severity = "Medium"

                    return {
                        "category": category,
                        "ai_summary": parsed.get("ai_summary", "Analysis completed."),
                        "privacy_implications": parsed.get("privacy_implications", "Review updated policy clauses."),
                        "severity": severity,
                        "is_ai_generated": True,
                        "model_used": f"{provider_label.split('(')[0].strip()} ({model_candidate})"
                    }
                except Exception as e:
                    last_error = e
                    # If model not found, decommissioned, or error code 400/404, try next candidate
                    err_msg = str(e).lower()
                    if any(term in err_msg for term in ["404", "400", "does not exist", "decommissioned", "not found", "model_not_found"]):
                        continue
                    break

            # If all model attempts failed, log and fall back to rule-based classification cleanly
            fallback = cls._rule_based_fallback(section_name, previous_content, updated_content, change_type)
            fallback["is_ai_generated"] = False
            fallback["model_used"] = "Heuristic Analysis"
            return fallback

        # If AI engine is NOT configured, use rule-based heuristics with clear indicator
        fallback = cls._rule_based_fallback(section_name, previous_content, updated_content, change_type)
        fallback["is_ai_generated"] = False
        fallback["model_used"] = "Rule-based Engine (AI key unconfigured)"
        return fallback

    @classmethod
    def _rule_based_fallback(cls, section_name: str, previous_content: str, updated_content: str, change_type: str):
        """Rule-based heuristic classifier used when OpenAI API key is not supplied."""
        combined_text = f"{section_name} {previous_content} {updated_content}".lower()

        if any(w in combined_text for w in ["cookie", "tracker", "beacon", "pixel", "telemetry", "fingerprint", "analytics"]):
            category = "Cookies and tracking"
            severity = "High" if "fingerprint" in combined_text or "pixel" in combined_text else "Medium"
        elif any(w in combined_text for w in ["share", "disclose", "third party", "vendor", "partner", "affiliate", "broker"]):
            category = "Data sharing"
            severity = "High" if "broker" in combined_text or "sell" in combined_text else "Medium"
        elif any(w in combined_text for w in ["collect", "gather", "obtain", "personal information", "location", "biometric"]):
            category = "Data collection"
            severity = "High" if "biometric" in combined_text or "location" in combined_text else "Medium"
        elif any(w in combined_text for w in ["rights", "opt-out", "delete", "erase", "access", "portability", "gdpr", "ccpa"]):
            category = "User rights"
            severity = "Low" if "opt-out" in combined_text else "Medium"
        elif any(w in combined_text for w in ["retain", "retention", "period", "duration", "storage period"]):
            category = "Data retention"
            severity = "Medium"
        elif any(w in combined_text for w in ["security", "encrypt", "breach", "safeguard", "protect"]):
            category = "Security"
            severity = "Medium"
        elif any(w in combined_text for w in ["third-party", "external", "service provider", "ai partner", "licensing"]):
            category = "Third-party services"
            severity = "High"
        else:
            category = "Policy updates"
            severity = "Low"

        action = "added" if change_type == "Added" else ("removed" if change_type == "Removed" else "modified")
        ai_summary = f"Clause regarding {section_name.strip()} was {action}."
        privacy_implications = f"Changes to {category.lower()} clauses may affect user data boundaries, compliance obligations, or consent requirements."

        return {
            "category": category,
            "ai_summary": ai_summary,
            "privacy_implications": privacy_implications,
            "severity": severity
        }
