#!/usr/bin/env python3

import json
import os
import sys

import requests

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(THIS_DIR, '..', 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
COURSES_FILE = os.path.join(DATA_DIR, 'courses.json')

TOKEN = 'CKa4QeVkC9ZL3aUGQ2kUvtVKnUaBrCuXAvMYNcL34mxMLkc9UrmttFR924FFMRXY'
SERVER = 'http://127.0.0.1:3000'
API_BASE = 'api/v1'

SITE_ADMIN_ACCOUNT_ID = 2
SERVER_OWNER_ACCOUNT_ID = 1
SERVER_OWNER_USER_ID = 1

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

    # {name: {'account_id': account_id, 'user_id': user_id}, ...}
    users_info = {
        'server-owner': {
            'account_id': SERVER_OWNER_ACCOUNT_ID,
            'user_id': SERVER_OWNER_USER_ID,
        },
    }

    for user in users:
        name = user['name']
        email = user['email']

        # The server owner is inserted on initial database population.
        if (name == 'server-owner'):
            continue

        # First, create an account for the user, with the site admin as the parent.
        data = {
            'account[name]': name,
            'account[sis_account_id]': email,
        }

        _, response_data = make_canvas_post(f"accounts/{SERVER_OWNER_ACCOUNT_ID}/sub_accounts", data = data)
        account_id = response_data['id']

        # Create a user for the new account.
        data = {
            'user[name]': name,
            'user[short_name]': name,
            'user[sortable_name]': name,
            'user[terms_of_use]': True,
            'user[skip_registration]': True,
            'pseudonym[unique_id]': email,
            'pseudonym[password]': name,
            'pseudonym[sis_user_id]': email,
            'pseudonym[integration_id]': email,
            'pseudonym[send_confirmation]': False,
            'pseudonym[force_self_registration]': False,
            'force_validations': False,
        }

        _, response_data = make_canvas_post(f"accounts/{account_id}/users", data = data)
        user_id = response_data['id']

        # Store the user info.
        users_info[name] = {
            'account_id': account_id,
            'user_id': user_id,
        }

    return users_info

def add_courses(users_info):
    with open(COURSES_FILE, 'r') as file:
        courses = json.load(file)

    account_id = users_info['course-owner']['account_id']

    # {course_id: canvas_course_id, ...}
    course_ids = {}

    for course in courses:
        data = {
            'course[name]': course['name'],
            'course[course_code]': course['id'],
            'course[is_public]': False,
            'course[is_public_to_auth_users]': False,
            'course[public_syllabus]': False,
            'course[public_syllabus_to_auth]': False,
            'course[allow_student_wiki_edits]': False,
            'course[allow_wiki_comments]': False,
            'course[allow_student_forum_attachments]': False,
            'course[open_enrollment]': False,
            'course[self_enrollment]': False,
            'offer': True,
            'enroll_me': False,
            'skip_course_template': True,
        }

        _, response_data = make_canvas_post(f"accounts/{account_id}/courses", data = data)
        course_id = response_data['id']

        course_ids[course['id']] = course_id

    return course_ids

def main():
    users_info = add_users()
    course_ids = add_courses(users_info)

    return 0

if __name__ == '__main__':
    sys.exit(main())
