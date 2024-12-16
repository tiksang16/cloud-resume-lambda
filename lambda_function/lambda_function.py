import json
import boto3
import logging
from botocore.exceptions import ClientError
from decimal import Decimal

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

# DynamoDB Table Name
TABLE_NAME = "visitor-counter"

# Helper function to convert Decimal to int
def decimal_to_int(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def lambda_handler(event, context):
    try:
        # Reference the DynamoDB table
        table = dynamodb.Table(TABLE_NAME)

        # Fetch the current visitor count
        response = table.get_item(Key={'id': 'visitor-counter'})
        if 'Item' in response:
            current_count = response['Item']['count']
        else:
            # Item does not exist, initialize it
            current_count = 0
            table.put_item(Item={'id': 'visitor-counter', 'count': current_count})

        # Increment the visitor count
        updated_count = current_count + 1

        # Update the count in DynamoDB
        table.update_item(
            Key={'id': 'visitor-counter'},
            UpdateExpression="set #count = :count",
            ExpressionAttributeNames={'#count': 'count'},
            ExpressionAttributeValues={':count': updated_count}
        )

        # Return the updated visitor count
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            # Convert Decimal to int before returning
            'body': json.dumps({'count': updated_count}, default=decimal_to_int)
        }

    except ClientError as e:
        logger.error(f"Error interacting with DynamoDB: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Internal Server Error'})
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Internal Server Error'})
        }