import os
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials
from typing import List
from config import CREDS_FILE, MASTER_SHEET_ID, HEADERS, STATE_DIR
from personal_sheets import PEOPLE

TRACK_FILE = os.path.join(STATE_DIR, "last_distributed_row.txt")


def _ensure_state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)


def _load_last_distributed_row() -> int:
    _ensure_state_dir()

    if not os.path.exists(TRACK_FILE):
        return 1
    with open(TRACK_FILE, "r") as f:
        s = f.read().strip()
        return int(s) if s.isdigit() else 1


def _save_last_distributed_row(n: int) -> None:
    _ensure_state_dir()
    with open(TRACK_FILE, "w") as f:
        f.write(str(n))


def _gs_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    return gspread.authorize(creds)


def _ensure_headers(ws):
    current_headers = ws.row_values(1)
    if not current_headers:
        ws.append_row(HEADERS, value_input_option="USER_ENTERED")
    elif current_headers != HEADERS:
        ws.update("1:1", [HEADERS])  # overwrite with correct headers



def split_new_master_rows_chunks(batch_size: int = 500, sleep_seconds: float = 2.0) -> int:
    """
    Split master sheet rows into chunks for each person.
    Upload in batches with sleep to avoid hitting Google Sheets API quota.
    """
    client = _gs_client()

    master = client.open_by_key(MASTER_SHEET_ID).sheet1

    # Fetch only new rows instead of entire sheet
    last_idx = _load_last_distributed_row()
    all_vals: List[List[str]] = master.get_all_values()

    if not all_vals:
        print("Master is empty.")
        return 0

    header, data = all_vals[0], all_vals[1:]

    # Slice only new rows
    start_data_index = max(0, last_idx - 1)
    new_rows = data[start_data_index:]

    if not new_rows:
        print("✅ No new rows to distribute.")
        return 0

    # Open all personal sheets once
    person_sheets = {}
    for person in PEOPLE:
        ws = client.open_by_key(person["sheet_id"]).sheet1
        _ensure_headers(ws)
        person_sheets[person["name"]] = ws

    # Split new rows more fairly
    n_people = len(PEOPLE)
    total = len(new_rows)
    chunk_size = max(1, total // n_people)   # ✅ ensures at least 1 row per person
    remainder = total % n_people

    assigned_count = 0
    start = 0
    for i, person in enumerate(PEOPLE):
        if start >= total:
            break  # stop if we run out of rows

        end = min(start + chunk_size + (1 if i < remainder else 0), total)
        chunk = new_rows[start:end]

        if chunk:
            ws = person_sheets[person["name"]]
            # Upload in batches with sleep
            for j in range(0, len(chunk), batch_size):
                batch = chunk[j:j + batch_size]
                ws.append_rows(batch, value_input_option="USER_ENTERED")
                print(f"✅ Uploaded {len(batch)} rows to {person['name']}")
                time.sleep(sleep_seconds)

            assigned_count += len(chunk)
            print(f"✅ {person['name']} got {len(chunk)} rows (rows {start+1} → {end})")

        start = end

    # Update tracker properly
    new_last_abs = last_idx + assigned_count
    _save_last_distributed_row(new_last_abs)
    print(f"✅ Updated last_distributed_row -> {new_last_abs}")

    return assigned_count



if __name__ == "__main__":
    split_new_master_rows_chunks()

