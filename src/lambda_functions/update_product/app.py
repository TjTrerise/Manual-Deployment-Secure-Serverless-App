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

    body_data = {} 

    if 'body' in event:
        if isinstance(event['body'], str):   
            try:
                body_data = json.loads(event['body'])
            except json.JSONDecodeError:
                print("Invalid JSON format in event['body'] string.")
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps('Invalid JSON format in request body.')
                }
        elif isinstance(event['body'], dict):
            body_data = event['body']
        else:
            print(f"Unexpected type for event['body']: {type(event['body'])}")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps('Invalid request body format.')
            }
    else:
        print("No 'body' field found in the event.")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps('Request body is missing.')
        }

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

  
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}

        if 'productName' in body_data:
            update_expression_parts.append('#N = :name')
            expression_attribute_values[':name'] = body_data['productName']
            expression_attribute_names['#N'] = 'productName'

        if 'productPrice' in body_data:
            update_expression_parts.append('#P = :price')
            expression_attribute_values[':price'] = Decimal(str(body_data['productPrice']))
            expression_attribute_names['#P'] = 'productPrice'

        if 'description' in body_data:
            update_expression_parts.append('#D = :desc')
            expression_attribute_values[':desc'] = body_data['description']
            expression_attribute_names['#D'] = 'description'

        if 'stock' in body_data:
            update_expression_parts.append('#S = :stock')
            expression_attribute_values[':stock'] = Decimal(str(body_data['stock']))
            expression_attribute_names['#S'] = 'stock'

        if not update_expression_parts:
            print("No valid update fields provided in the request body (body_data was empty after checks).")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps('No update fields provided.')
            }

        update_expression = 'SET ' + ', '.join(update_expression_parts)
        
        print(f"Attempting to update item with productId: {product_id}, category: {category}")
        print(f"UpdateExpression: {update_expression}")
        print(f"ExpressionAttributeValues: {expression_attribute_values}")
        print(f"ExpressionAttributeNames: {expression_attribute_names}")

        response = table.update_item(
            Key={
                'productId': product_id,
                'category': category # 
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names if expression_attribute_names else None,
            ReturnValues='UPDATED_NEW'
        )

        print(f"Item updated successfully! Updated Attributes: {response.get('Attributes', {})}")

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Product updated successfully!',
                'updatedAttributes': response.get('Attributes', {})
            }, cls=DecimalEncoder)
        }
    except ClientError as e:
        error_message = e.response['Error']['Message']
        print(f"DynamoDB Client Error: {error_message}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(f"Database error: {error_message}")
        }
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(f'Internal server error: {str(e)}')
        }