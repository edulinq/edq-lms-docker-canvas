#!/bin/bash

# Load initial data that then allows the rest of the data to be loaded.
# This will include an API token that we will insert directly into the DB.
# The rest of the data will be loaded via more conventional means.

# A valid cleartext token associated with server-owner.
readonly TOKEN='CKa4QeVkC9ZL3aUGQ2kUvtVKnUaBrCuXAvMYNcL34mxMLkc9UrmttFR924FFMRXY'

function main() {
    trap exit SIGINT
    set -e

    # Insert the token for server admin, and make some other changes to allow the token to be valid.
    psql -d canvas_development <<EOF
        INSERT INTO public.developer_keys (
            id, api_key, email, user_name, account_id,
            created_at, updated_at,
            user_id, name, workflow_state, auto_expire_tokens, root_account_id
        ) VALUES (
            1, '6uzWLnHeWCUTtHnRhEHCftLkxnkYAf2z8zAMCUAffLkxCLF4hvQXZyKNX3Eu883z',
            'server-owner@test.edulinq.org', 'server-owner@test.edulinq.org', 2,
            'epoch', 'epoch',
            1, 'User-Generated', 'active', 'f', 2
        );

        INSERT INTO access_tokens (
            developer_key_id,
            user_id,
            purpose,
            created_at,
            updated_at,
            crypted_token,
            crypted_refresh_token,
            token_hint,
            workflow_state,
            root_account_id
        ) VALUES (
            1,
            1,
            'Initial API Token',
            'epoch',
            'epoch',
            '75462267d5d8723c8cfd797de20e4a09afe5bb9d',
            'c3219f0e2231e4894c4c88df84acd031b7d9ccaa',
            'CKa4Q',
            'active',
            2
        );

        INSERT INTO public.developer_key_account_bindings (
            id, account_id, developer_key_id, workflow_state, created_at, updated_at, root_account_id
        ) VALUES (
            1, 2, 1, 'on', 'epoch', 'epoch', 2
        );

        UPDATE public.accounts SET parent_account_id = 2 WHERE id = 1;
EOF
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
