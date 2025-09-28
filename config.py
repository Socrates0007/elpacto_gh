import os
from dotenv import load_dotenv, find_dotenv
# config.py

# Load environment variables
load_dotenv()
BASE_DIR = os.path.dirname(__file__)

# WooCommerce
STORE_URL = os.getenv("STORE_URL")
WOO_CONSUMER_KEY = os.getenv("WOO_CONSUMER_KEY")
WOO_CONSUMER_SECRET = os.getenv("WOO_CONSUMER_SECRET")
# Google Sheets service account JSON (path on disk)
CREDS_FILE = os.getenv("CREDS_FILE")

# Master Google Sheet ID (the big long ID in the URL)
#MASTER_SHEET_ID = "1T8M3U5vru8QkSgJ7KzEpJhZdu1lpH4HNn7ii5QPryzs"
MASTER_SHEET_ID = os.getenv("MASTER_SHEET_ID")

# Common header for master & all personal sheets (must match exactly)


# config.py

HEADERS = [
    "DATE",            # Col A
    "ORDER NUMBER",    # Col B
    "FIRST NAME",      # Col C
    "LAST NAME",       # Col D
    "LOCATION",        # Col E
    "PRODUCT",         # Col F
    "QUANTITY",        # Col G
    "PRICE",           # Col H
    "PHONE NUMBER",    # Col I
    # J to O (columns between phone and P) are left as-is in sheet
    # Force ADDRESS into column P
    "", "", "", "", "",  # placeholders (J–N)
    "ADDRESS"          # Col P
]



# State directory (for TXT trackers)
STATE_DIR = os.path.join(os.path.dirname(__file__), "state")

# WhatsApp sending safety delay (seconds) between messages
WHATSAPP_DELAY_SECONDS = 5


TWILIO_SID= os.getenv("TWILIO_SID")
TWILIO_AUTH=os.getenv("TWILIO_AUTH")
TWILIO_FROM=os.getenv("TWILIO_FROM")

