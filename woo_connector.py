'''# woo_connector.py
import os
import requests
from datetime import datetime
from typing import List, Dict, Any
from config import STORE_URL, WOO_CONSUMER_KEY, WOO_CONSUMER_SECRET, STATE_DIR

LAST_ID_FILE = os.path.join(STATE_DIR, "last_order_id.txt")


def _ensure_state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)


def _load_last_order_id() -> int:
    _ensure_state_dir()
    if not os.path.exists(LAST_ID_FILE):
        return 0
    
    
    try:
        with open(LAST_ID_FILE, "r") as f:
            val = f.read().strip()
            return int(val) if val.isdigit() else 0
    except Exception:
        return 0


def _save_last_order_id(order_id: int) -> None:
    _ensure_state_dir()
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(order_id))


def fetch_new_orders() -> List[Dict[str, Any]]:
    """
    Fetch new WooCommerce orders with ID > last saved ID.
    Tries 'min_id' for efficiency; falls back to fetch+filter if unsupported.
    Returns list of order dicts (as from WC API).
    """
    base = f"{STORE_URL}/wp-json/wc/v3/orders"
    last_id = _load_last_order_id()
    session = requests.Session()
    auth = (WOO_CONSUMER_KEY, WOO_CONSUMER_SECRET)

    new_orders: List[Dict[str, Any]] = []

    # Attempt efficient path with min_id
    params = {
        "per_page": 100,
        "orderby": "id",
        "order": "asc",
        "min_id": last_id + 1,  # only strictly newer
        "page": 1,
    }

    try:
        resp = session.get(base, auth=auth, params=params, timeout=30)
        # If server doesn't support min_id, it might 400. Then fallback.
        if resp.status_code == 400:
            raise RuntimeError("min_id unsupported; falling back to filter")

        resp.raise_for_status()
        total_pages = int(resp.headers.get("X-WP-TotalPages", "1"))
        new_orders.extend(resp.json())

        for page in range(2, total_pages + 1):
            params["page"] = page
            r = session.get(base, auth=auth, params=params, timeout=30)
            r.raise_for_status()
            new_orders.extend(r.json())

    except Exception:
        # Fallback: fetch by pages, then filter id > last_id
        new_orders = []
        params_fallback = {
            "per_page": 100,
            "orderby": "id",
            "order": "asc",
            "page": 1,
        }
        r0 = session.get(base, auth=auth, params=params_fallback, timeout=30)
        r0.raise_for_status()
        total_pages = int(r0.headers.get("X-WP-TotalPages", "1"))
        new_orders.extend([o for o in r0.json() if o.get("id", 0) > last_id])

        for page in range(2, total_pages + 1):
            params_fallback["page"] = page
            r = session.get(base, auth=auth, params=params_fallback, timeout=30)
            r.raise_for_status()
            new_orders.extend([o for o in r.json() if o.get("id", 0) > last_id])

    # Update last ID if we got any
    if new_orders:
        max_id = max(o.get("id", 0) for o in new_orders)
        _save_last_order_id(max_id)

    return new_orders


if __name__ == "__main__":
    orders = fetch_new_orders()
    print(f"Fetched {len(orders)} new orders")
    for o in orders:
        print(o["id"], o["status"], o["billing"]["first_name"], o["total"])
'''
# woo_connector.py
import os
import requests
from datetime import datetime
from typing import List, Dict, Any
from config import STORE_URL, WOO_CONSUMER_KEY, WOO_CONSUMER_SECRET, STATE_DIR

LAST_ID_FILE = os.path.join(STATE_DIR, "last_order_id.txt")


def _ensure_state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)


def _load_last_order_id() -> int:
    _ensure_state_dir()
    if not os.path.exists(LAST_ID_FILE):
        return 0

    try:
        with open(LAST_ID_FILE, "r") as f:
            val = f.read().strip()
            return int(val) if val.isdigit() else 0
    except Exception:
        return 0


def _save_last_order_id(order_id: int) -> None:
    _ensure_state_dir()
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(order_id))


def fetch_new_orders() -> List[Dict[str, Any]]:
    """
    Fetch new WooCommerce orders with ID > last saved ID.
    Tries 'min_id' for efficiency; falls back to fetch+filter if unsupported.
    Returns list of order dicts (as from WC API).
    """
    base = f"{STORE_URL}/wp-json/wc/v3/orders"
    last_id = _load_last_order_id()
    session = requests.Session()
    auth = (WOO_CONSUMER_KEY, WOO_CONSUMER_SECRET)

    new_orders: List[Dict[str, Any]] = []

    # Attempt efficient path with min_id
    params = {
        "per_page": 100,
        "orderby": "id",
        "order": "asc",
        "min_id": last_id + 1,  # only strictly newer
        "page": 1,
    }

    try:
        resp = session.get(base, auth=auth, params=params, timeout=30)
        if resp.status_code == 400:
            raise RuntimeError("min_id unsupported; falling back to filter")

        resp.raise_for_status()
        total_pages = int(resp.headers.get("X-WP-TotalPages", "1"))
        new_orders.extend(resp.json())

        for page in range(2, total_pages + 1):
            params["page"] = page
            r = session.get(base, auth=auth, params=params, timeout=30)
            r.raise_for_status()
            new_orders.extend(r.json())

    except Exception:
        # Fallback: fetch everything, then filter
        new_orders = []
        params_fallback = {
            "per_page": 100,
            "orderby": "id",
            "order": "asc",
            "page": 1,
        }
        r0 = session.get(base, auth=auth, params=params_fallback, timeout=30)
        r0.raise_for_status()
        total_pages = int(r0.headers.get("X-WP-TotalPages", "1"))
        new_orders.extend(r0.json())

        for page in range(2, total_pages + 1):
            params_fallback["page"] = page
            r = session.get(base, auth=auth, params=params_fallback, timeout=30)
            r.raise_for_status()
            new_orders.extend(r.json())

    # ✅ Strict filter: only keep orders > last_id
    filtered_orders = [o for o in new_orders if o.get("id", 0) > last_id]

    # Update last ID only if we got any new
    if filtered_orders:
        max_id = max(o.get("id", 0) for o in filtered_orders)
        _save_last_order_id(max_id)

    print(f"Last saved ID: {last_id}, fetched {len(filtered_orders)} new orders")
    return filtered_orders


if __name__ == "__main__":
    orders = fetch_new_orders()
    print(f"Fetched {len(orders)} new orders")
    for o in orders:
        print(o["id"], o["status"], o["billing"]["first_name"], o["total"])
