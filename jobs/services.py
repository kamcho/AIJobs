import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from django.conf import settings
from django.core.mail import EmailMessage
from allauth.socialaccount.models import SocialToken, SocialAccount, SocialApp
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class EmailService:
    @staticmethod
    def send_application_email(user, job, cover_letter_file, cv_file_path=None):
        """
        Sends a job application email. 
        Uses Gmail API if the user has a connected Google account, 
        otherwise falls back to standard SMTP.
        """
        # 1. Try to get Google credentials
        try:
            print(f"DEBUG Email: Attempting to find Google SocialAccount for user {user.email}")
            social_acc = SocialAccount.objects.get(user=user, provider='google')
            social_token = SocialToken.objects.filter(account=social_acc).first()
            
            if social_token:
                print(f"DEBUG Email: Found SocialToken for user. Attempting Gmail API...")
                # We also need the SocialApp for client_id/secret
                social_app = SocialApp.objects.get(provider='google')
                return EmailService._send_via_gmail_api(user, job, cover_letter_file, social_token, social_app, cv_file_path)
            else:
                print(f"DEBUG Email: No SocialToken found for user. Falling back to SMTP.")
        except SocialAccount.DoesNotExist:
            print(f"DEBUG Email: No Google SocialAccount found for user. Falling back to SMTP.")
        except SocialApp.DoesNotExist:
            print(f"DEBUG Email: No Google SocialApp configured in database. Falling back to SMTP.")
        except Exception as e:
            print(f"DEBUG Email Error: Unexpected transition error: {str(e)}")
            
        # 2. Fallback to SMTP
        return EmailService._send_via_smtp(user, job, cover_letter_file, cv_file_path)

    @staticmethod
    def _send_via_gmail_api(user, job, cover_letter_file, social_token, social_app, cv_file_path):
        creds = Credentials(
            token=social_token.token,
            refresh_token=social_token.token_secret,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=social_app.client_id,
            client_secret=social_app.secret,
        )
        
        service = build('gmail', 'v1', credentials=creds)
        
        message = MIMEMultipart()
        message['to'] = job.employer_email
        message['from'] = user.email
        message['subject'] = f"Application for {job.title} - {user.profile.full_name or user.email}"

        msg_body = f"Hello,\n\nPlease find my application for the {job.title} position attached.\n\nBest regards,\n{user.profile.full_name or user.email}"
        message.attach(MIMEText(msg_body, 'plain'))

        # Attach Cover Letter
        if cover_letter_file:
            content = cover_letter_file.read()
            ext = cover_letter_file.name.split('.')[-1] if '.' in cover_letter_file.name else 'pdf'
            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if ext == 'docx' else 'application/pdf'
            
            part = MIMEApplication(content)
            part.add_header('Content-Disposition', 'attachment', filename=f'Cover_Letter.{ext}')
            # Override content-type for docx
            if ext == 'docx':
                part.set_type(mime_type)
            message.attach(part)
            cover_letter_file.seek(0)

        # Attach CV
        if cv_file_path:
            with open(cv_file_path, 'rb') as f:
                ext = cv_file_path.split('.')[-1] if '.' in cv_file_path else 'pdf'
                part = MIMEApplication(f.read())
                part.add_header('Content-Disposition', 'attachment', filename=f'CV.{ext}')
                message.attach(part)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': raw_message}
        
        try:
            service.users().messages().send(userId="me", body=create_message).execute()
            print("DEBUG Email: Gmail API Send Successful")
            return True, "Email sent via Gmail API"
        except Exception as e:
            print(f"DEBUG Email Error: Gmail API Error: {str(e)}")
            return False, f"Gmail API Error: {str(e)}"

    @staticmethod
    def _send_via_smtp(user, job, cover_letter_file, cv_file_path):
        print("DEBUG Email: Falling back to SMTP (Console Backend)")
        subject = f"Application for {job.title} - {user.profile.full_name or user.email}"
        body = f"Hello,\n\nPlease find my application for the {job.title} position attached.\n\nBest regards,\n{user.profile.full_name or user.email}"
        
        email = EmailMessage(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [job.employer_email],
            reply_to=[user.email]
        )

        if cover_letter_file:
            ext = cover_letter_file.name.split('.')[-1] if '.' in cover_letter_file.name else 'pdf'
            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if ext == 'docx' else 'application/pdf'
            email.attach(f'Cover_Letter.{ext}', cover_letter_file.read(), mime_type)
            cover_letter_file.seek(0)

        if cv_file_path:
            with open(cv_file_path, 'rb') as f:
                email.attach('CV.pdf', f.read(), 'application/pdf')

        try:
            email.send()
            return True, "Email sent via SMTP"
        except Exception as e:
            return False, f"SMTP Error: {str(e)}"
