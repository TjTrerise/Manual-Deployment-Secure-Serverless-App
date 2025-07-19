import json
import boto3
from botocore.exceptions import ClientError
import os
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'ProductsTable')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    print(f"Received event: {event}")

    try:
        if 'pathParameters' not in event or \
           'productId' not in event['pathParameters'] or \
           'category' not in event['pathParameters']:
            print("Missing productId or category in path parameters.")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps('Missing productId or category in path parameters.')
            }

        product_id = event['pathParameters']['productId']
        category = event['pathParameters']['category']

        print(f"Attempting to get item with productId: {product_id}, category: {category}")
        response = table.get_item(
            Key={
                'productId': product_id,
                'category': category
            }
        )
        item = response.get('Item')

        if not item:
            print(f"Product with ID {product_id} and category {category} not found.")
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(f'Product with ID {product_id} and category {category} not found.')
            }

        print(f"Successfully retrieved item: {item}")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(item, cls=DecimalEncoder)
        }
    except ClientError as e:
        error_message = e.response['Error']['Message']
        print(f"DynamoDB Client Error: {error_message}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(f"Database error: {error_message}")
        }
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(f'Internal server error: {str(e)}')
        }