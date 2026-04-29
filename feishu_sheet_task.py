import json
import requests

APP_ID = "cli_a92691a8a9785bdb"
APP_SECRET = "L7B9m1AEIAElHLEJQvyKUcijvUGFbs1N"
SHEET_TOKEN = "OqTss9P9YhhUQbtB0DPc4KIcnjd"
SPREADSHEET_TOKEN = "d9b3f6"  # sheetId

BASE_URL = "https://open.feishu.cn"

def get_tenant_access_token():
    url = f"{BASE_URL}/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()["tenant_access_token"]

def get_values(token, range_):
    url = f"{BASE_URL}/open-apis/sheet/v2/spreadsheets/{SHEET_TOKEN}/values/{range_}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def put_values(token, range_, values):
    url = f"{BASE_URL}/open-apis/sheet/v2/spreadsheets/{SHEET_TOKEN}/values/{range_}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"values": values}
    resp = requests.put(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()

# Step 1: Get current data in A-H columns to confirm it's there
print("=== Step 1: Reading A-H columns (rows 1-20) ===")
tok = get_tenant_access_token()
result = get_values(tok, "d9b3f6!A1:H20")
print(json.dumps(result, indent=2, ensure_ascii=False))
