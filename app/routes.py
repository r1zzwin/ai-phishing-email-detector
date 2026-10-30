import logging
import sqlite3

from flask import (
    Blueprint, abort, current_app, flash, redirect,
    render_template, request, url_for,
)

from . import analyzer, db, ollama_client
from .validation import validate_input

bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


def _db_path():
    return current_app.config["DATABASE"]


@bp.route("/")
def index():
    return render_template(
        "index.html", status=ollama_client.check_status(), form={}, errors=[]
    )


@bp.route("/analyze", methods=["POST"])
def analyze():
    data, errors = validate_input(request.form)
    if errors:
        return (
            render_template(
                "index.html",
                status=ollama_client.check_status(),
                form=data,
                errors=errors,
            ),
            400,
        )

    result = analyzer.analyze_email(data["sender"], data["subject"], data["body"])

    scan_id, save_error = None, False
    try:
        scan_id = db.save_scan(_db_path(), data, result)
    except sqlite3.Error:
        logger.warning("Could not save scan to history")
        save_error = True

    return render_template(
        "result.html", email=data, result=result,
        scan_id=scan_id, save_error=save_error,
    )


@bp.route("/history")
def history():
    q = request.args.get("q", "").strip()[:100]
    category = request.args.get("category", "").strip()
    scans, db_error = [], False
    try:
        scans = db.list_scans(_db_path(), q, category)
    except sqlite3.Error:
        logger.warning("Could not load scan history")
        db_error = True
    return render_template(
        "history.html", scans=scans, q=q, category=category,
        categories=db.CATEGORIES, db_error=db_error,
    )


@bp.route("/history/<int:scan_id>")
def history_detail(scan_id):
    try:
        scan = db.get_scan(_db_path(), scan_id)
    except sqlite3.Error:
        logger.warning("Could not load scan")
        flash("The scan could not be loaded.")
        return redirect(url_for("main.history"))
    if scan is None:
        abort(404)
    return render_template("history_detail.html", scan=scan)


@bp.route("/history/<int:scan_id>/delete", methods=["POST"])
def delete_scan(scan_id):
    try:
        removed = db.delete_scan(_db_path(), scan_id)
        flash("Scan deleted." if removed else "That scan no longer exists.")
    except sqlite3.Error:
        logger.warning("Could not delete scan")
        flash("The scan could not be deleted.")
    return redirect(url_for("main.history"))


@bp.route("/history/clear", methods=["POST"])
def clear_history():
    try:
        db.clear_scans(_db_path())
        flash("All history deleted.")
    except sqlite3.Error:
        logger.warning("Could not clear history")
        flash("History could not be cleared.")
    return redirect(url_for("main.history"))