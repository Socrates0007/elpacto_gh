
# master_sheet_updater.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import List, Dict, Any
from config import CREDS_FILE, MASTER_SHEET_ID, HEADERS
from woo_connector import fetch_new_orders


def _gs_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    return gspread.authorize(creds)


def _ensure_headers(worksheet):
    first = worksheet.row_values(1)
    if not first:
        worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")


def _fmt_date_gmt(dateStr: str) -> str:
    # Woo gives like "2025-08-20T14:21:33Z" -> "YYYY-MM-DD"
    if dateStr.endswith("Z"):
        dateStr = dateStr.replace("Z", "+00:00")
    dt = datetime.fromisoformat(dateStr)
    return dt.date().isoformat()


def _orders_to_rows(orders: List[Dict[str, Any]]) -> List[List[str]]:
    rows: List[List[str]] = []
    for o in orders:
        order_date = _fmt_date_gmt(o.get("date_created_gmt", o.get("date_created")))
        order_id = str(o.get("id", ""))
        billing = o.get("billing", {}) or {}
        first = billing.get("first_name", "")
        last = billing.get("last_name", "")
        phone = billing.get("phone", "")
        city = billing.get("city", "")
        state = billing.get("state", "")

        # ✅ Build ADDRESS string
        address = ", ".join(
            filter(None, [
                billing.get("address_1", ""),
                billing.get("address_2", ""),
                billing.get("city", ""),
                billing.get("state", ""),
                billing.get("postcode", ""),
                billing.get("country", "")
            ])
        )

        line_items = o.get("line_items", []) or []
        if not line_items:
            # Minimal row
            row = [
                order_date, order_id, first, last,
                f"{city}, {state}", "", "", "", phone
            ]
            # ✅ Pad to 15 cols (up to column O)
            row += [""] * (15 - len(row))
            row[14] = address  # Column P
            rows.append(row)
            continue

        for li in line_items:
            product = li.get("name", "")
            qty = str(li.get("quantity", ""))
            price = li.get("total", "")
            row = [
                order_date, order_id, first, last,
                f"{city}, {state}", product, qty, price, phone
            ]
            # ✅ Pad to 15 cols (up to column O)
            row += [""] * (15 - len(row))
            row[14] = address  # Column P
            rows.append(row)

    return rows


def _load_last_master_order_id(ws) -> int:
    """Find the highest ORDER NUMBER in master sheet to avoid duplicates"""
    try:
        all_vals = ws.get_all_values()[1:]  # skip header
        if not all_vals:
            return 0
        # ORDER NUMBER is at index 1 according to HEADERS
        ids = [int(r[1]) for r in all_vals if r[1].isdigit()]
        return max(ids) if ids else 0
    except Exception:
        return 0


def append_new_orders_to_master() -> int:
    orders = fetch_new_orders()
    if not orders:
        print("✅ No new orders to add to Master.")
        return 0

    client = _gs_client()
    #ws = client.open_by_key(MASTER_SHEET_ID).sheet1
    ws = client.open_by_key(MASTER_SHEET_ID).worksheet("December")
    _ensure_headers(ws)

    last_master_id = _load_last_master_order_id(ws)
    # Only keep orders newer than the last in master sheet
    orders = [o for o in orders if o.get("id", 0) > last_master_id]

    if not orders:
        print("✅ No truly new rows to add after checking master sheet.")
        return 0

    rows = _orders_to_rows(orders)
    ws.append_rows(rows, value_input_option="USER_ENTERED")
    print(f"✅ Added {len(rows)} rows to Master.")
    return len(rows)


if __name__ == "__main__":
    append_new_orders_to_master()
