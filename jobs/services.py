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
        Uses Gmail API ONLY for direct 'email' method if the user has a connected Google account, 
        otherwise falls back to standard SMTP (sending documents to the user).
        """
        # 1. Try Gmail API ONLY if the method is 'email'
        if job.application_method == 'email':
            try:
                print(f"DEBUG Email: Attempting to find Google SocialAccount for user {user.email}")
                social_acc = SocialAccount.objects.get(user=user, provider='google')
                social_token = SocialToken.objects.filter(account=social_acc).first()
                
                if social_token:
                    print(f"DEBUG Email: Found SocialToken for user. Attempting Gmail API...")
                    social_app = SocialApp.objects.get(provider='google')
                    return EmailService._send_via_gmail_api(user, job, cover_letter_file, social_token, social_app, cv_file_path)
                else:
                    print(f"DEBUG Email: No SocialToken found for user. Falling back to SMTP.")
            except (SocialAccount.DoesNotExist, SocialApp.DoesNotExist):
                print(f"DEBUG Email: Google integration not fully configured for user. Falling back to SMTP.")
            except Exception as e:
                print(f"DEBUG Email Error: Unexpected transition error: {str(e)}")
            
        # 2. Fallback to SMTP (Sending materials to user with instructions)
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

        email_body = f"Hello,\n\nA new job matching your preferences has been posted on JobMatch:\n\nBest regards,\n{user.profile.full_name or user.email}"
        message.attach(MIMEText(email_body, 'plain'))

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
        print(f"DEBUG Email: Sending application materials to user inbox for method: {job.application_method}")
        
        # Get company name from either company field or company_profile
        company_name = job.company
        if job.company_profile:
            company_name = job.company_profile.name
            
        # Determine instructions based on application method
        method = job.application_method
        target = job.application_url or job.employer_email or "the specified application page"
        
        if method == 'email':
            action_title = "FORWARD This Email to the Employer"
            next_steps = f"""1. Forward this email (with all attachments) to the employer's email address: {job.employer_email}
2. You can add a personal message if you'd like before forwarding.
3. Make sure both attachments (Cover Letter and CV) are included."""
            target_label = "EMPLOYER EMAIL"
        elif method == 'google_form':
            action_title = "UPLOAD These Documents to the Google Form"
            next_steps = f"""1. Click the Google Form link below:
   {job.application_url}
2. Fill in your details on the form.
3. When prompted, upload the documents attached to this email (Cover Letter and CV)."""
            target_label = "GOOGLE FORM LINK"
        elif method == 'website':
            action_title = "UPLOAD These Documents to the Company Website"
            next_steps = f"""1. Visit the application page:
   {job.application_url or job.url}
2. Complete the online application.
3. Upload the documents attached to this email (Cover Letter and CV) during the submission process."""
            target_label = "APPLICATION URL"
        else:
            action_title = "Complete Your Application"
            next_steps = f"""1. Use the attached documents (Cover Letter and CV) to complete your application.
2. Follow the instructions provided on the application page:
   {job.application_url or job.url}"""
            target_label = "APPLICATION PAGE"

        subject = f"Application Materials for {job.title} - Submission Required"
        body = f"""Hello {user.profile.full_name or "Applicant"},

Your application materials for "{job.title}" at {company_name or 'the company'} have been successfully generated.

*** IMPORTANT: THIS EMAIL WAS SENT TO YOU (THE APPLICANT) ***

To complete your application, please follow the instructions below based on the application method:

### INSTRUCTIONS: {action_title} ###

{next_steps}

{target_label}: {target}

--------------------------------------------------
ATTACHMENTS INCLUDED:
1. Cover Letter (Generated/Uploaded)
2. CV (Selected)
--------------------------------------------------

Good luck!
FindAJob.ai Team"""
        
        email = EmailMessage(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
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
            display_target = job.employer_email if method == 'email' else "the application link"
            return True, f"Application materials sent to your email. Please follow the instructions to complete your submission to {display_target}."
        except Exception as e:
            return False, f"SMTP Error: {str(e)}"
