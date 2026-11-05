"""Applies the branded Supabase Auth emails (password reset, volunteer invitation) to a Supabase project.

The templates live in this folder; Supabase keeps the live copy in the project's Auth settings, so they
must be pushed. Usage:

    export SUPABASE_ACCESS_TOKEN=...            # a personal access token (Supabase dashboard > Account > Access Tokens)
    python email_templates/apply_templates.py --project-ref <ref> --dry-run   # show what would change, send nothing
    python email_templates/apply_templates.py --project-ref <ref>             # apply

Only the four email fields below are sent; every other Auth setting is left alone.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
API = "https://api.supabase.com/v1/projects/{ref}/config/auth"

TEMPLATES = {
    "recovery": {"subject": "Reset your Project Kaagapay password", "file": "recovery.html"},
    "invite": {"subject": "You're invited to volunteer with Project Kaagapay", "file": "invite.html"},
}


def build_payload() -> dict:
    payload = {}
    for name, spec in TEMPLATES.items():
        payload[f"mailer_subjects_{name}"] = spec["subject"]
        payload[f"mailer_templates_{name}_content"] = (HERE / spec["file"]).read_text(encoding="utf-8")
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-ref", required=True, help="the project's reference, e.g. abcdefghijklmnop")
    parser.add_argument("--dry-run", action="store_true", help="print what would be sent and stop")
    args = parser.parse_args(argv)

    payload = build_payload()
    if args.dry_run:
        for key, value in payload.items():
            print(f"{key}: {value if key.startswith('mailer_subjects') else f'{len(value)} characters of HTML'}")
        print(f"Dry run: nothing sent. Would update project {args.project_ref}.")
        return 0

    token = os.environ.get("SUPABASE_ACCESS_TOKEN")
    if not token:
        print("Set SUPABASE_ACCESS_TOKEN first (Supabase dashboard > Account > Access Tokens).", file=sys.stderr)
        return 2

    request = urllib.request.Request(
        API.format(ref=args.project_ref),
        data=json.dumps(payload).encode(),
        method="PATCH",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": "kaagapay-email-templates"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            print(f"Updated project {args.project_ref} (HTTP {response.status}).")
    except urllib.error.HTTPError as err:
        print(f"Supabase refused the update (HTTP {err.code}): {err.read().decode()[:300]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
