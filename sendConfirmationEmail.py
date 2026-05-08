import json
import boto3

# Connect to SES
ses = boto3.client('ses', region_name='ap-south-2')  


SENDER_EMAIL = 'omen.soloman@gmail.com'

def lambda_handler(event, context):
    """
    Triggered by SNS. Sends a confirmation email to the user.
    """
    # SNS wraps the message — we need to unwrap it
    for record in event['Records']:
        sns_message = record['Sns']['Message']
        data = json.loads(sns_message)
        
        user_name = data['userName']
        user_email = data['userEmail']
        event_id = data['eventId']
        registration_id = data['registrationId']
        
        # Build the email
        subject = f"✅ Registration Confirmed — Event {event_id}"
        
        body_text = f"""
Hello {user_name},

Your registration is confirmed!

Details:
- Event: {event_id}
- Registration ID: {registration_id}
- Email: {user_email}

Thank you for registering. See you at the event!

Best regards,
Event Team
        """
        
        body_html = f"""
<html>
<body>
  <h2>✅ Registration Confirmed!</h2>
  <p>Hello <strong>{user_name}</strong>,</p>
  <p>Your registration is confirmed!</p>
  <table border="1" cellpadding="8">
    <tr><td><strong>Event</strong></td><td>{event_id}</td></tr>
    <tr><td><strong>Registration ID</strong></td><td>{registration_id}</td></tr>
    <tr><td><strong>Email</strong></td><td>{user_email}</td></tr>
  </table>
  <p>Thank you for registering. See you at the event! 🎉</p>
</body>
</html>
        """
        
        try:
            ses.send_email(
                Source=SENDER_EMAIL,
                Destination={'ToAddresses': [user_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Text': {'Data': body_text},
                        'Html': {'Data': body_html}
                    }
                }
            )
            print(f"Email sent to {user_email}")
        
        except Exception as e:
            print(f"Failed to send email to {user_email}: {str(e)}")
    
    return {'statusCode': 200, 'body': 'Emails processed'}