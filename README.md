# Kraken Audit - Automated HVAC Invoice Auditing

Kraken Audit is an automated, serverless-ready pipeline that ingests commercial HVAC invoices, extracts granular line-item data via LLM (Gemini), and cross-references it against a compliance rulebook to flag overcharges and billing discrepancies.

## Project Structure

- `kraken_audit/`
  - `ingestion/`: Logic for monitoring incoming files.
  - `extraction/`: Gemini LLM extraction engine and schema models.
  - `judge/`: Compliance Engine and Knowledge Base (Vector DB).
  - `delivery/`: Database persistence and Markdown report generation.
  - `pipeline.py`: Main orchestrator wiring all modules together.
  - `watcher_integrated.py`: File watcher that triggers the pipeline on new files.
  - `tests/`: Integration and E2E tests.

## Prerequisites

- Python 3.12+
- `GOOGLE_API_KEY`: Required for live extraction (optional for mock tests).
- `team-db`: CLI tool for Turso database synchronization.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   export GOOGLE_API_KEY="your_api_key_here"
   export PYTHONPATH=$PYTHONPATH:/home/team/shared
   ```

## Running the Pipeline

### Automated (File Watcher)
The watcher monitors `/home/team/shared/invoices/incoming/` and processes any new files detected.

```bash
python kraken_audit/watcher_integrated.py
```

### Manual Trigger
You can process a single invoice file using the `Pipeline` class:

```python
from kraken_audit.pipeline import Pipeline
pipeline = Pipeline()
report_path = pipeline.process_invoice("path/to/invoice.pdf")
print(f"Report generated at: {report_path}")
```

## Testing

### Integration Test (No API Key Required)
This test uses mock extraction JSON and mocks the LLM call to verify the full pipeline logic (Compliance → Delivery → DB Persistence).

```bash
python kraken_audit/tests/test_integration.py
```

### End-to-End Test
Verifies the orchestration and file watcher trigger.

```bash
python kraken_audit/tests/test_pipeline.py
```

## Compliance Rules
The system currently implements three core audit rules:
1. **Labor Cap**: Flags labor rates exceeding $95/hour.
2. **Vague Billing**: Flags non-specific descriptions (e.g., "MISC", "Repair") with high amounts.
3. **Role Discrepancy**: Flags high-level roles (e.g., Master Tech) billed for simple tasks (e.g., filter swaps).
