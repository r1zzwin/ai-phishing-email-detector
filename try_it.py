from app.rules import analyze_rules

result = analyze_rules(
    sender="Ravi <ravi@gmail.com>",
    subject="Meeting tomorrow",
    body="Hi, the meeting is at 3pm tomorrow.",
)

for f in result["findings"]:
    print(f["points"], f["name"], "->", f["evidence"])
print("Rule score:", result["rule_score"])