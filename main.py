import os
import json
import gspread
from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
GOOGLE_CREDENTIALS = os.environ.get('GOOGLE_CREDENTIALS')

def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDENTIALS)
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet('Messages')
    return sheet

def get_display_name(source_type, group_id, user_id):
    try:
        if source_type == 'group':
            url = f'https://api.line.me/v2/bot/group/{group_id}/member/{user_id}'
        else:
            url = f'https://api.line.me/v2/bot/profile/{user_id}'
        headers = {'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'}
        res = requests.get(url, headers=headers)
        return res.json().get('displayName', '')
    except:
        return ''

@app.route('/', methods=['GET'])
def index():
    return jsonify({'status': 'ok'})

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return jsonify({'status': 'ok'})

    body = request.get_json()
    events = body.get('events', [])

    if not events:
        return jsonify({'status': 'ok'})

    sheet = get_sheet()

    for event in events:
        if event.get('type') != 'message':
            continue
        if event.get('message', {}).get('type') != 'text':
            continue

        source      = event.get('source', {})
        source_type = source.get('type', '')
        group_id    = source.get('groupId', '')
        user_id     = source.get('userId', '')
        message     = event['message']['text']
        timestamp   = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        name        = get_display_name(source_type, group_id, user_id)

        sheet.append_row([timestamp, source_type, group_id, user_id, name, message])

    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
