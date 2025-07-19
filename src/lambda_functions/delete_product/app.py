import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ProductsTable') 

def lambda_handler(event, context):
    try:
        if 'pathParameters' not in event or 'productId' not in event['pathParameters']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps('Missing productId in path.')
            }

        product_id = event['pathParameters']['productId']

        response = table.delete_item(
            Key={
                'productId': product_id
            },
            ReturnValues='ALL_OLD'
        )

        if 'Attributes' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(f'Product with ID {product_id} not found or already deleted.')
            }

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(f'Product {product_id} deleted successfully.')
        }
    except ClientError as e:
        print(f"DynamoDB Client Error: {e.response['Error']['Message']}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(f"Database error: {e.response['Error']['Message']}")
        }
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(f'Internal server error: {str(e)}')
        }