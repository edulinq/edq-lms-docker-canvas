#!/usr/bin/env python3

import json
import os
import sys

import requests

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(THIS_DIR, '..', 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
COURSES_FILE = os.path.join(DATA_DIR, 'courses.json')
ASSIGNMENTS_FILE = os.path.join(DATA_DIR, 'assignments.json')

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

# See: https://developerdocs.instructure.com/services/canvas/resources/enrollments#enrollment
COURSE_ROLE_ENROLLMENT_MAP = {
    'other': 'ObserverEnrollment',
    'student': 'StudentEnrollment',
    'grader': 'TaEnrollment',
    'admin': 'TaEnrollment',
    'owner': 'TeacherEnrollment',
}

# See: https://developerdocs.instructure.com/services/canvas/resources/assignments#assignment
ASSIGNMENT_SUBMISSION_TYPE_MAP = {
    'autograder': 'none',
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

# Add users to canvas and add a 'canvas' dict to users that has 'account_id' and 'user_id'.
def add_users(users):
    # Add in the server owner's info manually.
    users['server-owner']['canvas'] = {
        'account_id': SERVER_OWNER_ACCOUNT_ID,
        'user_id': SERVER_OWNER_USER_ID,
    }

    for user in users.values():
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

        # Store the canvas info.
        user['canvas'] = {
            'account_id': account_id,
            'user_id': user_id,
        }

# Add courses (not erollments) to canvas and add a 'canvas' dict to courses that has 'course_id'.
def add_courses(courses, users):
    account_id = users['course-owner']['canvas']['account_id']

    for course in courses.values():
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

        course['canvas'] = {'course_id': course_id}

def add_enrollments(courses, users):
    for user in users.values():
        for (course_id, enrollment_info) in user.get('course-info', {}).items():
            role = enrollment_info['role']

            data = {
                'enrollment[user_id]': user['canvas']['user_id'],
                'enrollment[type]': COURSE_ROLE_ENROLLMENT_MAP[role],
                'enrollment[enrollment_state]': 'active',
                'enrollment[limit_privileges_to_course_section]': False,
                'enrollment[notify]': False,
            }

            canvas_course_id = courses[course_id]['canvas']['course_id']
            make_canvas_post(f"courses/{canvas_course_id}/enrollments", data = data)

def add_assignments(assignments, courses):
    for (course_id, course_assignments) in assignments.items():
        for assignment in course_assignments:
            data = {
                'assignment[name]': assignment['name'],
                'assignment[submission_types][]': ASSIGNMENT_SUBMISSION_TYPE_MAP[assignment['type']],
                'assignment[turnitin_enabled]': False,
                'assignment[vericite_enabled]': False,
                'assignment[peer_reviews]': False,
                'assignment[automatic_peer_reviews]': False,
                'assignment[notify_of_update]': False,
                'assignment[points_possible]': assignment['max-points'],
                'assignment[allowed_attempts]': -1,
                'assignment[grading_type]': 'points',
                'assignment[only_visible_to_overrides]': False,
                'assignment[published]': True,
                'assignment[quiz_lti]': False,
                'assignment[moderated_grading]': False,
                'assignment[omit_from_final_grade]': False,
                # For some reason, hide_in_gradebook gives a 400.
                # 'assignment[hide_in_gradebook]': False,
            }

            canvas_course_id = courses[course_id]['canvas']['course_id']
            make_canvas_post(f"courses/{canvas_course_id}/assignments", data = data)

# Load the data from disk into a dict, key by name (users) or id (courses).
def load_test_data():
    with open(USERS_FILE, 'r') as file:
        raw_users = json.load(file)

    with open(COURSES_FILE, 'r') as file:
        raw_courses = json.load(file)

    with open(ASSIGNMENTS_FILE, 'r') as file:
        assignments = json.load(file)

    # Transform the data from an array into a dict (keyed by name/id).

    users = {user['name']: user for user in raw_users}
    courses = {course['id']: course for course in raw_courses}

    return users, courses, assignments

def main():
    users, courses, assignments = load_test_data()

    add_users(users)
    add_courses(courses, users)
    add_enrollments(courses, users)
    add_assignments(assignments, courses)

    return 0

if __name__ == '__main__':
    sys.exit(main())
