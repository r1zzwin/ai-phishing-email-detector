import json
import sqlite3

import pytest

from app import db


def make_result(score=40, category="Medium"):
    return {
        "rules": {
            "findings": [{"rule": "urgent_language",
                          "name": "Urgent or threatening language",
                          "points": 10, "evidence": "urgent"}],
            "rule_score": 10,
        },
        "ai": None,
        "ai_error": "Ollama is off",
        "score": {"score": score, "category": category, "rule_points": 10,
                  "ai_points": 0, "ai_used": False, "explanation": "Rules only."},
    }


def make_email(sender="Ravi <ravi@gmail.com>", subject="Hello", body="Hi there"):
    return {"sender": sender, "subject": subject, "body": body}


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "t.db")
    db.init_db(path)
    return path


def test_save_and_get_roundtrip(db_path):
    scan_id = db.save_scan(db_path, make_email(), make_result())
    scan = db.get_scan(db_path, scan_id)
    assert scan["sender"] == "Ravi <ravi@gmail.com>"
    assert scan["score"] == 40
    assert scan["category"] == "Medium"
    assert scan["report"]["rule_findings"][0]["rule"] == "urgent_language"


def test_email_body_is_never_stored(db_path):
    scan_id = db.save_scan(db_path, make_email(body="SECRETBODYTEXT"), make_result())
    scan = db.get_scan(db_path, scan_id)
    assert "SECRETBODYTEXT" not in json.dumps(scan)


def test_newest_scan_is_listed_first(db_path):
    db.save_scan(db_path, make_email(subject="first"), make_result())
    db.save_scan(db_path, make_email(subject="second"), make_result())
    assert db.list_scans(db_path)[0]["subject"] == "second"


def test_search_matches_sender_or_subject(db_path):
    db.save_scan(db_path, make_email(subject="Invoice overdue"), make_result())
    db.save_scan(db_path, make_email(subject="Lunch plans"), make_result())
    found = db.list_scans(db_path, search="invoice")
    assert len(found) == 1
    assert found[0]["subject"] == "Invoice overdue"


def test_percent_sign_in_search_is_literal(db_path):
    db.save_scan(db_path, make_email(subject="100% off"), make_result())
    db.save_scan(db_path, make_email(subject="hello"), make_result())
    found = db.list_scans(db_path, search="%")
    assert len(found) == 1


def test_category_filter(db_path):
    db.save_scan(db_path, make_email(), make_result(10, "Low"))
    db.save_scan(db_path, make_email(), make_result(80, "Critical"))
    found = db.list_scans(db_path, category="Critical")
    assert len(found) == 1
    assert found[0]["category"] == "Critical"


def test_sql_injection_text_is_harmless(db_path):
    db.save_scan(db_path, make_email(), make_result())
    assert db.list_scans(db_path, search="'; DROP TABLE scans; --") == []
    assert len(db.list_scans(db_path)) == 1


def test_delete_removes_only_that_scan(db_path):
    first = db.save_scan(db_path, make_email(subject="keep"), make_result())
    second = db.save_scan(db_path, make_email(subject="remove"), make_result())
    assert db.delete_scan(db_path, second) == 1
    remaining = db.list_scans(db_path)
    assert [s["id"] for s in remaining] == [first]


def test_clear_removes_everything(db_path):
    db.save_scan(db_path, make_email(), make_result())
    db.clear_scans(db_path)
    assert db.list_scans(db_path) == []


def test_missing_scan_returns_none(db_path):
    assert db.get_scan(db_path, 999) is None


def test_unreachable_database_raises_sqlite_error(tmp_path):
    bad_path = str(tmp_path / "no_such_folder" / "x.db")
    with pytest.raises(sqlite3.Error):
        db.list_scans(bad_path)