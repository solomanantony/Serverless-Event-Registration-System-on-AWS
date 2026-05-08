import json
import boto3
import uuid
from datetime import datetime
from botocore.exceptions import ClientError

# Connect to AWS services
dynamodb = boto3.resource('dynamodb')
events_table = dynamodb.Table('Events')
registrations_table = dynamodb.Table('Registrations')
sns = boto3.client('sns')


SNS_TOPIC_ARN = 'arn:aws:sns:ap-south-2:991524241826:EventRegistrationNotifications'

def lambda_handler(event, context):
    """
    Registers a user for an event.
    Uses DynamoDB conditional update to prevent overbooking.
    """
    try:
        # Parse the request body
        body = json.loads(event['body'])
        event_id = body['eventId']
        user_name = body['userName']
        user_email = body['userEmail']
        
        # --- CORE LOGIC: Atomic seat reservation ---
        # This update will FAIL if availableSeats is already 0
        # This prevents two people from booking the last seat at the same time
        try:
            events_table.update_item(
                Key={'eventId': event_id},
                UpdateExpression="SET availableSeats = availableSeats - :val",
                ConditionExpression="availableSeats > :zero",
                ExpressionAttributeValues={
                    ':val': 1,
                    ':zero': 0
                }
            )
        except ClientError as e:
            # ConditionalCheckFailedException means no seats left
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Sorry, no seats available for this event!'})
                }
            raise e  # Re-raise if it's a different error
        
        # --- Create registration record ---
        registration_id = str(uuid.uuid4())   # Generate unique ID
        
        registrations_table.put_item(
            Item={
                'registrationId': registration_id,
                'eventId': event_id,
                'userName': user_name,
                'userEmail': user_email,
                'registeredAt': datetime.now().isoformat()
            }
        )
        
        # --- Send notification via SNS ---
   
        message = json.dumps({
            'registrationId': registration_id,
            'eventId': event_id,
            'userName': user_name,
            'userEmail': user_email
        })
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject='New Event Registration'
        )
        
        # --- Return success ---
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': 'Registration successful!',
                'registrationId': registration_id
            })
        }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Registration failed. Please try again.'})
        }