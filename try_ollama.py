from app import ollama_client
from app.analyzer import analyze_email

print("Status:", ollama_client.check_status())

result = analyze_email(
    sender="PayPal Support <help@secure-login.xyz>",
    subject="Urgent: account suspended",
    body="Dear customer, verify your password immediately at http://192.168.1.5/login",
)

print("AI:", result["ai"])
print("AI error:", result["ai_error"])
print("Score:", result["score"]["score"], result["score"]["category"])
print(result["score"]["explanation"])