import requests
from datetime import datetime
from config import Config

class MementoService:
    """
    Memento TimeMap Discovery Service (RFC 7089).
    Discovers historical captures of privacy policies across web archives such as
    Internet Archive Wayback Machine and the Memento TimeTravel aggregator.
    """

    @classmethod
    def get_timemap(cls, url: str, limit: int = 10):
        """
        Query Memento aggregator or Wayback CDX API for historical archives of the given URL.
        Returns:
        {
            "success": bool,
            "url": str,
            "total_mementos": int,
            "mementos": [
                {
                    "datetime": str,
                    "timestamp": str,
                    "uri": str,
                    "rel": str
                }
            ],
            "error": str or None
        }
        """
        clean_url = url.strip()
        mementos = []

        # Try Wayback Machine CDX API first (fast and highly reliable JSON)
        try:
            cdx_url = f"https://web.archive.org/cdx/search/cdx?url={clean_url}&output=json&limit={limit}&fl=timestamp,original,statuscode,digest&filter=statuscode:200"
            res = requests.get(cdx_url, timeout=10)
            if res.status_code == 200:
                rows = res.json()
                if len(rows) > 1:
                    headers = rows[0]
                    for r in rows[1:]:
                        ts = r[0]
                        orig = r[1]
                        try:
                            dt = datetime.strptime(ts, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            dt = ts
                        mementos.append({
                            "datetime": dt,
                            "timestamp": ts,
                            "uri": f"https://web.archive.org/web/{ts}/{orig}",
                            "rel": "memento",
                            "digest": r[3] if len(r) > 3 else ""
                        })
                    return {
                        "success": True,
                        "url": clean_url,
                        "total_mementos": len(mementos),
                        "mementos": mementos,
                        "error": None
                    }
        except Exception as e:
            # CDX failed, try Memento TimeTravel aggregator
            pass

        # Try Memento Web TimeMap JSON endpoint
        try:
            memento_url = f"{Config.MEMENTO_TIMEMAP_URL}{clean_url}"
            res = requests.get(memento_url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                memento_list = data.get("mementos", {}).get("list", [])
                for m in memento_list[:limit]:
                    mementos.append({
                        "datetime": m.get("datetime"),
                        "timestamp": m.get("datetime"),
                        "uri": m.get("uri"),
                        "rel": m.get("rel", "memento"),
                        "digest": ""
                    })
                return {
                    "success": True,
                    "url": clean_url,
                    "total_mementos": len(mementos),
                    "mementos": mementos,
                    "error": None
                }
        except Exception as e:
            return {
                "success": False,
                "url": clean_url,
                "total_mementos": 0,
                "mementos": [],
                "error": f"Memento historical lookup failed: {str(e)}"
            }

        return {
            "success": True,
            "url": clean_url,
            "total_mementos": 0,
            "mementos": [],
            "error": "No historical web archives found for this URL via Memento protocol."
        }

    @classmethod
    def fetch_memento_content(cls, memento_uri: str):
        """Fetch raw HTML/text of a specific historical memento."""
        try:
            headers = {"User-Agent": "PrivacyUpdateBot/1.0"}
            res = requests.get(memento_uri, headers=headers, timeout=15)
            if res.status_code == 200:
                return {"success": True, "content": res.text, "error": None}
            return {"success": False, "content": "", "error": f"HTTP {res.status_code}"}
        except Exception as e:
            return {"success": False, "content": "", "error": str(e)}
