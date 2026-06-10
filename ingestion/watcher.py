import time
import os
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ingestion_handler import lambda_handler

class IngestionWatcher(FileSystemEventHandler):
    def __init__(self, bucket_name, storage_path):
        self.bucket_name = bucket_name
        self.storage_path = storage_path

    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_name = os.path.relpath(file_path, self.storage_path)
        
        print(f"\n[Watcher] New file detected: {file_name}")
        
        # Simulate S3 event
        mock_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": self.bucket_name},
                        "object": {"key": file_name}
                    }
                }
            ]
        }
        
        # Trigger the handler
        lambda_handler(mock_event, None)

if __name__ == "__main__":
    BUCKET_NAME = "local-invoices"
    # Use path from lead's message
    STORAGE_PATH = os.path.abspath(os.getenv("INVOICE_INCOMING_DIR", "/home/team/shared/invoices/incoming"))
    
    if not os.path.exists(STORAGE_PATH):
        os.makedirs(STORAGE_PATH)

    event_handler = IngestionWatcher(BUCKET_NAME, STORAGE_PATH)
    observer = Observer()
    observer.schedule(event_handler, STORAGE_PATH, recursive=False)
    
    print(f"Monitoring directory: {STORAGE_PATH}")
    print("Press Ctrl+C to stop.")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
