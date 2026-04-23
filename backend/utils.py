"""
backend/utils.py — shared helpers for routers
"""


def extract_urls(result) -> list[str]:
    """Robustly extract image URL(s) from various Bria API response shapes."""
    if not result:
        return []
    if isinstance(result, str) and result.startswith("http"):
        return [result]
    if isinstance(result, list):
        urls = []
        for item in result:
            urls.extend(extract_urls(item))
        return urls
    if isinstance(result, dict):
        for key in ("result_url", "url"):
            if key in result and isinstance(result[key], str):
                return [result[key]]
        for key in ("result_urls", "urls"):
            if key in result and isinstance(result[key], list):
                return [u for u in result[key] if isinstance(u, str)]
        if "result" in result:
            return extract_urls(result["result"])
    return []
