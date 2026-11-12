"""The branded auth emails: required placeholders, mail-client limits, accessibility and the apply script."""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from email_templates import apply_templates

FOLDER = Path(apply_templates.HERE)
FILES = {"recovery": FOLDER / "recovery.html", "invite": FOLDER / "invite.html"}

# The project's colour tokens (src/index.css in the frontend), inlined because email cannot use CSS variables.
PAGE, CARD, PRIMARY, TEXT, MUTED = "#fff7f9", "#ffffff", "#a500a5", "#241722", "#554051"


def luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("name", FILES)
def test_the_sign_in_link_is_in_the_button_and_in_a_copyable_fallback(name):
    html = FILES[name].read_text()
    kind = "recovery" if name == "recovery" else "invite"
    link = "{{ .SiteURL }}/set-password?token_hash={{ .TokenHash }}&amp;type=" + kind
    assert html.count(link) == 3                              # button href, fallback link href, fallback link text
    assert f'href="{link}"' in html and "Copy and paste this link" in html
    # The token is used when the person presses Continue on our page, not when a mail scanner opens the link.
    assert "{{ .ConfirmationURL }}" not in html


@pytest.mark.parametrize("name", FILES)
def test_mail_client_limits(name):
    html = FILES[name].read_text()
    assert len(html.encode()) < 100_000                      # Gmail clips messages over about 102 KB
    assert "<script" not in html.lower() and "@import" not in html and "fonts.googleapis" not in html
    assert "<style" not in html.lower()                      # inline styles only: some clients drop <style>
    assert "background-image" not in html.lower()
    assert html.count("<table") == html.count("</table>")


@pytest.mark.parametrize("name", FILES)
def test_accessibility_basics(name):
    html = FILES[name].read_text()
    assert '<html lang="en">' in html and "<title>" in html
    assert all("alt=" in tag for tag in re.findall(r"<img[^>]*>", html))
    assert html.count("<h1") == 1
    assert 'role="presentation"' in html                     # layout tables are not data tables
    sizes = [int(s) for s in re.findall(r"font-size:(\d+)px", html)]
    assert min(sizes) >= 14                                  # nothing smaller than the footer's 14px


@pytest.mark.parametrize("name", FILES)
def test_colours_meet_contrast_and_use_only_project_tokens(name):
    html = FILES[name].read_text()
    assert contrast("#ffffff", PRIMARY) >= 4.5               # button text on the button
    assert contrast(TEXT, CARD) >= 4.5 and contrast(MUTED, CARD) >= 4.5 and contrast(PRIMARY, CARD) >= 4.5   # body, footer, links
    assert contrast("#dbbed3", CARD) < 3                     # the card edge is decoration only; nothing relies on it
    used = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", html)}
    assert used <= {PAGE, CARD, PRIMARY, TEXT, MUTED, "#dbbed3"}, used - {PAGE, CARD, PRIMARY, TEXT, MUTED, "#dbbed3"}


def test_the_words_match_what_each_email_is_for():
    recovery, invite = FILES["recovery"].read_text(), FILES["invite"].read_text()
    assert "Reset your password" in recovery and ">Reset password</a>" in recovery and "ignore this email" in recovery
    assert "Your volunteer application was approved" in invite and ">Set your password</a>" in invite and "send a new invitation" in invite
    for html in (recovery, invite):
        assert "!" not in re.sub(r"<[^>]+>|\{\{[^}]*\}\}", "", html).replace("!DOCTYPE", "")   # no exclamation marks
        assert "password:" not in html.lower() and "temporary" not in html.lower()            # we never email a password


def test_the_payload_changes_only_the_four_email_fields():
    payload = apply_templates.build_payload()
    assert set(payload) == {"mailer_subjects_recovery", "mailer_templates_recovery_content", "mailer_subjects_invite", "mailer_templates_invite_content"}
    assert payload["mailer_templates_recovery_content"] == FILES["recovery"].read_text()
    assert all(len(v) <= 78 for k, v in payload.items() if k.startswith("mailer_subjects"))


def test_dry_run_sends_nothing(monkeypatch, capsys):
    def no_network(*a, **k):
        raise AssertionError("the dry run must not touch the network")
    monkeypatch.setattr(apply_templates.urllib.request, "urlopen", no_network)
    assert apply_templates.main(["--project-ref", "abc", "--dry-run"]) == 0
    assert "Dry run: nothing sent" in capsys.readouterr().out


def test_without_a_token_it_stops_and_says_how_to_get_one(monkeypatch, capsys):
    monkeypatch.delenv("SUPABASE_ACCESS_TOKEN", raising=False)
    assert apply_templates.main(["--project-ref", "abc"]) == 2
    assert "SUPABASE_ACCESS_TOKEN" in capsys.readouterr().err


def test_a_refusal_from_supabase_is_reported_not_hidden(monkeypatch, capsys):
    import io, urllib.error
    monkeypatch.setenv("SUPABASE_ACCESS_TOKEN", "t")
    def refuse(*a, **k):
        raise urllib.error.HTTPError("u", 403, "Forbidden", {}, io.BytesIO(b'{"message":"no access"}'))
    monkeypatch.setattr(apply_templates.urllib.request, "urlopen", refuse)
    assert apply_templates.main(["--project-ref", "abc"]) == 1
    assert "403" in capsys.readouterr().err


@pytest.mark.parametrize("name", FILES)
def test_the_logo_is_a_small_square_png_that_the_template_points_at(name):
    struct = __import__("struct")
    logo = FOLDER / "email-logo.png"
    data = logo.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    assert (width, height) == (192, 192)                      # shown at 48 px, so sharp on high-density screens
    assert len(data) < 50_000                                 # light enough not to slow the email down
    html = FILES[name].read_text()
    assert 'src="{{ .SiteURL }}/email-logo.png"' in html and 'width="48" height="48"' in html
