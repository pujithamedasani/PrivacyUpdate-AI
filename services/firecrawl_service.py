import time
import requests
from bs4 import BeautifulSoup
from config import Config

class FirecrawlService:
    """
    Client for Firecrawl API web extraction.
    If FIRECRAWL_API_KEY is configured, requests are dispatched to Firecrawl v1 endpoint.
    If unavailable or if fallback is permitted, falls back to direct HTTP extraction with clean DOM parsing,
    logging clearly that Firecrawl API key is missing.
    """
    
    @classmethod
    def get_api_key(cls):
        return Config.get_firecrawl_api_key()

    @classmethod
    def is_configured(cls):
        key = cls.get_api_key()
        return bool(key and len(key) > 5)

    @classmethod
    def scrape_url(cls, url: str, allow_fallback: bool = True):
        """
        Scrapes policy content from a URL.
        Returns a dict:
        {
            "success": bool,
            "content": str,
            "markdown": str,
            "title": str,
            "metadata": dict,
            "tool": str,
            "duration": float,
            "error": str or None
        }
        """
        start_time = time.time()
        api_key = cls.get_api_key()
        
        # 1. Attempt Firecrawl API if configured
        if cls.is_configured():
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "url": url,
                    "formats": ["markdown", "html"],
                    "onlyMainContent": True
                }
                response = requests.post(
                    f"{Config.FIRECRAWL_API_URL}/scrape",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                duration = round(time.time() - start_time, 2)
                
                if response.status_code == 200:
                    data = response.json()
                    res_data = data.get("data", {})
                    markdown_content = res_data.get("markdown") or res_data.get("content") or ""
                    title = res_data.get("metadata", {}).get("title") or url
                    return {
                        "success": True,
                        "content": markdown_content,
                        "markdown": markdown_content,
                        "title": title,
                        "metadata": res_data.get("metadata", {}),
                        "tool": "Firecrawl",
                        "duration": duration,
                        "error": None
                    }
                else:
                    err_msg = f"Firecrawl API error {response.status_code}: {response.text}"
                    if not allow_fallback:
                        return {
                            "success": False,
                            "content": "",
                            "markdown": "",
                            "title": "",
                            "metadata": {},
                            "tool": "Firecrawl",
                            "duration": duration,
                            "error": err_msg
                        }
            except Exception as e:
                duration = round(time.time() - start_time, 2)
                if not allow_fallback:
                    return {
                        "success": False,
                        "content": "",
                        "markdown": "",
                        "title": "",
                        "metadata": {},
                        "tool": "Firecrawl",
                        "duration": duration,
                        "error": f"Firecrawl connection failed: {str(e)}"
                    }
        
        # 2. If Firecrawl is NOT configured or failed and fallback is allowed:
        if not allow_fallback:
            return {
                "success": False,
                "content": "",
                "markdown": "",
                "title": "",
                "metadata": {},
                "tool": "Firecrawl",
                "duration": round(time.time() - start_time, 2),
                "error": "Firecrawl API key is not configured. Configure FIRECRAWL_API_KEY in .env or Settings."
            }

        # Fallback to direct HTTP extraction with clean readability parsing
        try:
            req_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 PrivacyUpdateBot/1.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            res = requests.get(url, headers=req_headers, timeout=20)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Remove scripts, styles, forms, and navigation
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
                tag.decompose()
                
            title = soup.title.string.strip() if soup.title and soup.title.string else url
            
            # Locate main content container if possible
            main_element = soup.find("main") or soup.find("article") or soup.find(id=lambda x: x and ("content" in x.lower() or "policy" in x.lower() or "privacy" in x.lower())) or soup.body
            
            text_lines = []
            if main_element:
                for el in main_element.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
                    text = el.get_text(separator=" ", strip=True)
                    if text:
                        if el.name == "h1":
                            text_lines.append(f"# {text}\n")
                        elif el.name == "h2":
                            text_lines.append(f"## {text}\n")
                        elif el.name == "h3":
                            text_lines.append(f"### {text}\n")
                        elif el.name == "li":
                            text_lines.append(f"- {text}")
                        else:
                            text_lines.append(f"{text}\n")
            
            cleaned_text = "\n".join(text_lines).strip()
            if not cleaned_text and main_element:
                cleaned_text = main_element.get_text(separator="\n", strip=True)
                
            duration = round(time.time() - start_time, 2)
            
            tool_label = "Direct Scraper (Fallback - No Firecrawl API Key)" if not cls.is_configured() else "Direct Scraper (Firecrawl Fallback)"
            
            return {
                "success": True,
                "content": cleaned_text,
                "markdown": cleaned_text,
                "title": title,
                "metadata": {"title": title, "status_code": res.status_code, "fallback": True},
                "tool": tool_label,
                "duration": duration,
                "error": None
            }
        except Exception as e:
            duration = round(time.time() - start_time, 2)
            return {
                "success": False,
                "content": "",
                "markdown": "",
                "title": "",
                "metadata": {},
                "tool": "Scraper",
                "duration": duration,
                "error": f"Extraction failed: {str(e)}"
            }
