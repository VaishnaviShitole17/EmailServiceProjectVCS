from django.shortcuts import render
import os
import ssl
import smtplib
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.core.mail import send_mail
from .google_api_utils import (
    get_service_account_credentials,
    get_oauth_credentials,
    get_google_sheets_service,
)
from .models import EmailLog  # Assuming EmailLog is defined in your models
from .forms import EmailCustomizationForm  # Import the EmailCustomizationForm


def fetch_google_sheet(request):
    
    # Decide the authentication method based on a query parameter or your logic
    auth_method = request.GET.get('auth', 'service_account')  # Default: service_account

    try:
        if auth_method == 'service_account':
            # Use Service Account
            credentials = get_service_account_credentials(
                settings.GOOGLE_SHEETS_CREDENTIALS
            )
        elif auth_method == 'oauth':
            # Use OAuth 2.0 (triggers user login flow)
            credentials = get_oauth_credentials(
                settings.GOOGLE_OAUTH_CREDENTIALS
            )
        else:
            return JsonResponse({'error': 'Invalid authentication method'}, status=400)

        # Build the Google Sheets API service
        service = get_google_sheets_service(credentials)

        # Example: Read data from the spreadsheet
        spreadsheet_id = settings.GOOGLE_SHEET_ID
        range_name = 'Sheet1!A1:C10'  # Adjust range as needed
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        data = result.get('values', [])

        return JsonResponse({'data': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def send_email(request):
    
    if request.method == 'POST':
        subject = 'Your Email Subject'
        message = 'Test mail.'
        from_email = settings.EMAIL_HOST_USER  # Fetch from settings for consistency
        recipient_list = ['sweetbutsour98@gmail.com']  # List of email recipients

        try:
            # Send the email using Django's send_mail function
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)

            # Log the email status
            EmailLog.objects.create(recipient=recipient_list[0], subject=subject, status="Sent")

            # Redirect to a success page
            return render(request, 'email_sent_successful.html')  # Email sent successfully

        except Exception as e:
            # Log the failure
            EmailLog.objects.create(recipient=recipient_list[0], subject=subject, status="Failed")

            # Redirect to a failure page
            return render(request, 'email_sent_failure.html')  # Email sending failed

    else:
        # Handle the GET request to display the email customization form
        form = EmailCustomizationForm()

    # Render the customize email form
    return render(request, 'customize_email.html', {'form': form})


def send_email_with_smtp(request):
   
    from_email = 'shitoletanishka@gmail.com'
    to_email = 'sweetbutsour98@gmail.com'
    message = 'Subject: Test Email\n\nThis is a test email.'
    
    # Fetch the email password securely from environment variable
    email_password = os.getenv('EMAIL_PASSWORD')  # Make sure EMAIL_PASSWORD is set in your environment variables
    
    # Path to your CA bundle
    ca_bundle_path = r"C:\Users\shito\Downloads\cacert.pem"  # Update with your actual file path

    try:
        # Create an SSL context with the provided CA bundle
        context = ssl.create_default_context(cafile=ca_bundle_path)

        # Send email using SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls(context=context)  # Start TLS with SSL context for secure connection
            server.login(from_email, email_password)
            server.sendmail(from_email, to_email, message)

        # Log the email status
        EmailLog.objects.create(recipient=to_email, subject="SMTP Test Email", status="Sent")
        return render(request, 'email_sent_successful.html')  # Email sent successfully

    except Exception as e:
        # Log the failure
        EmailLog.objects.create(recipient=to_email, subject="SMTP Test Email", status="Failed")
        return render(request, 'email_sent_failure.html', {'error': str(e)})  # Email sending failed


def email_analytics(request):
   
    logs = EmailLog.objects.all()
    return render(request, 'analytics.html', {'logs': logs})


def home(request):
    
    return render(request, 'home.html')

