'''# manual_splitter.py
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
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


def manual_split_loop():
    client = _gs_client()
    master = client.open_by_key(MASTER_SHEET_ID).sheet1

    all_vals = master.get_all_values()
    if not all_vals:
        print("Master is empty.")
        return

    header, data = all_vals[0], all_vals[1:]
    last_idx = _load_last_distributed_row()
    total_rows = len(data)

    print(f"Master sheet has {total_rows} rows (excluding header).")
    print(f"Last distributed row: {last_idx}")

    # Open personal sheets
    person_sheets = {}
    for person in PEOPLE:
        ws = client.open_by_key(person["sheet_id"]).sheet1
        _ensure_headers(ws)
        person_sheets[person["name"]] = ws

    while True:
        try:
            start = int(input("Enter start row (relative to data, not including header): "))
            end = int(input("Enter end row: "))

            if start < 1 or end > total_rows or start > end:
                print("❌ Invalid range. Try again.")
                continue

            print("Available agents: ", [p["name"] for p in PEOPLE])
            agent_name = input("Assign to which agent? ").strip()

            if agent_name not in person_sheets:
                print("❌ Invalid agent. Try again.")
                continue

            ws = person_sheets[agent_name]
            
            rows_raw = data[start - 1:end]
            # Force ADDRESS into column P (15th col) for personal sheet
            rows_to_assign = []
            for r in rows_raw:
            # pad row so it has at least 15 columns
                r = r + [""] * (15 - len(r))
                address = r[4]  # LOCATION (City, State) is in col E, but actual ADDRESS is what you stored in master
                r[15 - 1] = address  # put ADDRESS in col P (index 14)
                rows_to_assign.append(r)

            ws.append_rows(rows_to_assign, value_input_option="USER_ENTERED")
            # ✅ Mark assigned agent in Master (Column M = 13th col)
            update_range = f"M{start+1}:M{end+1}"  # +1 because header is row 1
            master.update(update_range, [[agent_name]] * (end - start + 1))

            print(f"✅ Assigned rows {start} → {end} to {agent_name} and marked in Master.")

            # Update tracker
            _save_last_distributed_row(end)

            cont = input("Do you want to continue? (y/n): ").lower()
            if cont != "y":
                print("✅ Finished manual distribution.")
                break

        except Exception as e:
            print("⚠️ Error:", e)
            break


if __name__ == "__main__":
    manual_split_loop()
'''
# manual_splitter.py
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
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


def manual_split_loop():
    client = _gs_client()
    master = client.open_by_key(MASTER_SHEET_ID).sheet1

    all_vals = master.get_all_values()
    if not all_vals:
        print("Master is empty.")
        return

    header, data = all_vals[0], all_vals[1:]
    last_idx = _load_last_distributed_row()
    total_rows = len(data)

    print(f"Master sheet has {total_rows} rows (excluding header).")
    print(f"Last distributed row: {last_idx}")

    # Open personal sheets
    person_sheets = {}
    for person in PEOPLE:
        ws = client.open_by_key(person["sheet_id"]).sheet1
        _ensure_headers(ws)
        person_sheets[person["name"]] = ws

    while True:
        try:
            start = int(input("Enter start row (relative to data, not including header): "))
            end = int(input("Enter end row: "))

            if start < 1 or end > total_rows or start > end:
                print("❌ Invalid range. Try again.")
                continue

            print("Available agents: ", [p["name"] for p in PEOPLE])
            agent_name = input("Assign to which agent? ").strip()

            if agent_name not in person_sheets:
                print("❌ Invalid agent. Try again.")
                continue

            ws = person_sheets[agent_name]

            # ✅ Copy rows from master, making sure they always have 15 cols (up to column P)
            rows_raw = data[start - 1:end]
            rows_to_assign = []
            for r in rows_raw:
                r = r + [""] * (15 - len(r))  # pad to at least 15 columns
                rows_to_assign.append(r)

            ws.append_rows(rows_to_assign, value_input_option="USER_ENTERED")

            # ✅ Mark assigned agent in Master (Column M = 13th col)
            update_range = f"M{start+1}:M{end+1}"  # +1 because header is row 1
            master.update(update_range, [[agent_name]] * (end - start + 1))

            print(f"✅ Assigned rows {start} → {end} to {agent_name} and marked in Master.")

            # Update tracker
            _save_last_distributed_row(end)

            cont = input("Do you want to continue? (y/n): ").lower()
            if cont != "y":
                print("✅ Finished manual distribution.")
                break

        except Exception as e:
            print("⚠️ Error:", e)
            break


if __name__ == "__main__":
    manual_split_loop()
