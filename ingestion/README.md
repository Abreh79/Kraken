# Ingestion Layer

Automated, event-driven ingestion for HVAC invoices.

## Project Structure
- `src/`: Python source code
  - `ingestion_handler.py`: The Lambda function handler.
  - `watcher.py`: Local development watcher to simulate S3 events.
- `infra/`: Terraform infrastructure-as-code.
- `/home/team/shared/invoices/incoming/`: Local directory used as a mock S3 bucket for development.

## Local Development

1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Start the local watcher:
   ```bash
   cd src
   python watcher.py
   ```

3. Add a file to the `/home/team/shared/invoices/incoming/` directory to trigger the ingestion handler:
   ```bash
   echo "test content" > ..//home/team/shared/invoices/incoming/invoice.pdf
   ```

## Cloud Deployment

The infrastructure is defined using Terraform in the `infra/` directory.

1. Initialize Terraform:
   ```bash
   cd infra
   terraform init
   ```

2. Deploy:
   ```bash
   terraform apply
   ```

This will create:
- An S3 bucket for invoice uploads.
- A Lambda function to process uploads.
- S3 event notifications to trigger the Lambda.
