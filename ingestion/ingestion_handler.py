import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'.pdf', '.jpeg', '.jpg', '.png'}

def lambda_handler(event, context):
    """
    AWS Lambda handler for S3 events.
    In a local environment, this is called by the watcher.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Extract bucket and key from S3 event
    try:
        for record in event.get('Records', []):
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            logger.info(f"Processing file: s3://{bucket}/{key}")
            
            # Validate extension
            _, ext = os.path.splitext(key)
            if ext.lower() not in ALLOWED_EXTENSIONS:
                logger.warning(f"Unsupported file type: {ext}. Skipping.")
                continue
            
            # Forward to extraction engine
            # For now, we just log the "forwarding"
            forward_to_extractor(bucket, key)
            
        return {
            'statusCode': 200,
            'body': json.dumps('Ingestion processed successfully')
        }
    except Exception as e:
        logger.error(f"Error processing ingestion: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }

def forward_to_extractor(bucket, key):
    """
    Placeholder for calling the extraction engine.
    This could be an SQS message, a Lambda invocation, or an API call.
    """
    # TODO: Integrate with extractor agent's API/queue
    file_uri = f"s3://{bucket}/{key}"
    logger.info(f"FORWARDING to Extractor: {file_uri}")
    
    # In local dev, we might want to write this to a shared file or log
    # For now, we'll just print it.
    print(f"PIPELINE_TRIGGER: {file_uri}")

if __name__ == "__main__":
    # Mock event for local testing
    mock_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "invoice_123.pdf"}
                }
            }
        ]
    }
    lambda_handler(mock_event, None)
