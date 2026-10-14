"""
邮件发送：通过 SMTP 把内容发送到指定邮箱。
587 端口用 SMTP + starttls()（先明文再升级加密），465 端口才用 SMTP_SSL。
"""
import os
import smtplib
from email.mime.text import MIMEText


def send_email(to: str, subject: str, content: str) -> str:
    """发送邮件，返回结果描述（成功 / 失败原因）"""
    try:
        sender_email = os.getenv("EMAIL_SENDER")
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_password = os.getenv("EMAIL_PASSWORD")

        if not all([sender_email, smtp_host, smtp_password, to]):
            return "邮件配置不完整，发送失败（请检查 EMAIL_SENDER / EMAIL_PASSWORD / SMTP_HOST）"

        msg = MIMEText(content, "plain", "utf-8")
        msg["To"] = to
        msg["Subject"] = subject
        msg["From"] = sender_email

        smtp = smtplib.SMTP(smtp_host, smtp_port)
        smtp.starttls()
        smtp.login(sender_email, smtp_password)
        smtp.sendmail(sender_email, to, msg.as_string())
        smtp.quit()
        return "邮件发送成功"
    except Exception as e:
        print(f"邮件发送异常: {e}")
        return f"邮件发送失败: {e}"
