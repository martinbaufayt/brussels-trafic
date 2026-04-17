import httpx

BASE_URL = "https://data.mobility.brussels/traffic/api/counts/"


def fetch_devices() -> dict:
    response = httpx.get(BASE_URL, params={"request": "devices", "outputFormat": "json"}, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_live() -> dict:
    response = httpx.get(
        BASE_URL,
        params={"request": "live", "interval": "1", "singleValue": "true"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
