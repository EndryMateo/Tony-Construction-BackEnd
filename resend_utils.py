# resend_utils.py
import resend

# ✅ Nueva API Key funcional
resend.api_key = "re_GWf6ezd7_Jd7c13Ng7zs2sTANbY22kgE5"

def send_recovery_email(to_email, code):
    try:
        response = resend.Emails.send({
            "from": "onboarding@resend.dev",  # ✅ No cambiar a menos que verifiques un nuevo remitente
            "to": [to_email],
            "subject": "Your Recovery Code",
            "html": f"""
                <h2>Password Recovery</h2>
                <p>Here is your 6-digit recovery code:</p>
                <h1>{code}</h1>
                <p>If you did not request this, you can ignore this email.</p>
            """
        })
        return True
    except Exception as e:
        print("❌ Resend error:", e)
        return False
