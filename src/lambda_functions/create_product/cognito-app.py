import json
import boto3
from botocore.exceptions import ClientError
import os 

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'ProductsTable')
table = dynamodb.Table(table_name)


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2)) 

    user_id = None
    email = None
    if 'requestContext' in event and \
       'authorizer' in event['requestContext'] and \
       'claims' in event['requestContext']['authorizer']:

        claims = event['requestContext']['authorizer']['claims']
        user_id = claims.get('sub')
        email = claims.get('email')

        print(f"Authenticated User ID: {user_id}")
        print(f"Authenticated User Email: {email}")

    print(f"Received event: {event}")

    product_data = None
    if 'body' in event and isinstance(event['body'], str):
        try:
            product_data = json.loads(event['body'])
        except json.JSONDecodeError:
            print("Invalid JSON format in event['body']")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps('Invalid JSON format in request body.')
            }
    else:
        product_data = event

    if not product_data:
        print("No valid product_data extracted from event.")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps('No data provided in the request.')
        }

    required_fields = ['productId', 'category', 'productName', 'productPrice']
    missing_fields = [field for field in required_fields if field not in product_data]

    if missing_fields:
        print(f"Missing required fields: {', '.join(missing_fields)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(f"Missing required fields: {', '.join(missing_fields)}")
        }

    try:
        product_id = product_data['productId']
        category = product_data['category']
        product_name = product_data['productName']
        product_price = product_data['productPrice']

        item = {
            'productId': product_id,
            'category': category,
            'productName': product_name,
            'productPrice': product_price
        }
        for key, value in product_data.items():
            if key not in required_fields:
                item[key] = value

        print(f"Attempting to put item: {item}")
        table.put_item(Item=item)
        print("Item put successfully!")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': 'Product created successfully!', 'productId': product_id, 'category': category})
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
            'body': json.dumps(f"Internal server error: {str(e)}")
        } 