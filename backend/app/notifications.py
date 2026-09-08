import os,smtplib,ssl
from email.message import EmailMessage
import httpx

def deliver(event,settings):
    """Called by the worker only for enabled operational events."""
    results=[]
    recipient=settings.get('notification_email')
    if recipient and os.getenv('SMTP_HOST'):
        message=EmailMessage();message['Subject']='[CI/CD] '+event['title'];message['From']=os.getenv('SMTP_FROM','cicd@localhost');message['To']=recipient;message.set_content(event['title']+'\n\n'+event['time'])
        with smtplib.SMTP(os.environ['SMTP_HOST'],int(os.getenv('SMTP_PORT','587')),timeout=15) as server:
            server.starttls(context=ssl.create_default_context())
            if os.getenv('SMTP_USER'): server.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD'])
            server.send_message(message)
        results.append('email')
    chat=settings.get('telegram_chat_id');token=os.getenv('TELEGRAM_BOT_TOKEN')
    if chat and token:
        response=httpx.post(f'https://api.telegram.org/bot{token}/sendMessage',json={'chat_id':chat,'text':'[CI/CD] '+event['title']},timeout=15)
        response.raise_for_status();results.append('telegram')
    return results
