from flask import Blueprint, render_template, request

from . import analyzer, ollama_client
from .validation import validate_input

bp = Blueprint("main", __name__)


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
    return render_template("result.html", email=data, result=result)