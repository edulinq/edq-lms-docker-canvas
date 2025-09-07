#!/usr/bin/env python3

import json
import os
import sys

import requests

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(THIS_DIR, '..', 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

TOKEN = 'CKa4QeVkC9ZL3aUGQ2kUvtVKnUaBrCuXAvMYNcL34mxMLkc9UrmttFR924FFMRXY'
SERVER = 'http://127.0.0.1:3000'
API_BASE = 'api/v1'

SERVER_OWNER_ACCOUNT_ID = 1

DEFAULT_HEADERS = {
    "Authorization": "Bearer %s" % (TOKEN),
    "Accept": "application/json+canvas-string-ids",
}

def make_canvas_post(endpoint, data = None, headers = None, json_body = True):
    if (data is None):
        data = {}

    if (headers is None):
        headers = {}

    # Add in standard headers.
    for (key, value) in DEFAULT_HEADERS.items():
        if (key not in headers):
            headers[key] = value

    url = f"{SERVER}/{API_BASE}/{endpoint}"

    response = requests.post(url, headers = headers, data = data)
    response.raise_for_status()

    body = None
    if (json_body):
        body = response.json()
    else:
        body = response.text

    return response, body

def add_users():
    with open(USERS_FILE, 'r') as file:
        users = json.load(file)

    for user in users:
        # Skip server owner (they were inserted on initial database population).
        if (user['name'] == 'server-owner'):
            continue

        data = {
            'user[name]': user['name'],
            'user[short_name]': user['name'],
            'user[sortable_name]': user['name'],
            'user[terms_of_use]': True,
            'user[skip_registration]': True,
            'pseudonym[unique_id]': user['email'],
            'pseudonym[password]': user['name'],
            'pseudonym[sis_user_id]': user['email'],
            'pseudonym[integration_id]': user['email'],
            'pseudonym[send_confirmation]': False,
            'pseudonym[force_self_registration]': False,
            'force_validations': False,
        }

        # TEST - We are enrolling everyone under server owner. Is this fine?
        make_canvas_post(f"accounts/{SERVER_OWNER_ACCOUNT_ID}/users", data = data)

def main():
    add_users()

    return 0

if __name__ == '__main__':
    sys.exit(main())
