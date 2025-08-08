import requests

# 🔑 API key definitiva proporcionada por el usuario
RESEND_API_KEY = "re_hjkZkuTC_KgkNAHaXKaY58i2Nryv3AMGg"

def send_recovery_email(email: str, code: str):
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "from": "Tony Design <noreply@tonydesignconstruction.com>",
        "to": [email],
        "subject": "Your password reset code",
        "html": f"""
            <div style='font-family:Arial,sans-serif;padding:1rem;background:#f9f9f9;border-radius:10px'>
                <h2 style='color:#ff3300;'>Tony Design Construction</h2>
                <p>Here is your 6-digit recovery code:</p>
                <h1 style='letter-spacing:3px;'>{code}</h1>
                <p>This code will expire soon. Use it to reset your password.</p>
            </div>
        """
    }

    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 200
