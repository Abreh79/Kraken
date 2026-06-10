import time
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from kraken_audit.pipeline import Pipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PipelineWatcher")

class IntegratedWatcher(FileSystemEventHandler):
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.pipeline = Pipeline()

    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_name = os.path.basename(file_path)
        
        # Ignore hidden files or temporary files
        if file_name.startswith('.'):
            return

        logger.info(f"New file detected: {file_path}")
        
        # Give the file a second to be fully written
        time.sleep(1)
        
        try:
            self.pipeline.process_invoice(file_path)
            logger.info(f"Successfully processed: {file_path}")
            
            # Move to processed folder
            processed_path = os.path.join("/home/team/shared/invoices/processed", file_name)
            os.rename(file_path, processed_path)
            logger.info(f"Moved to processed: {processed_path}")

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            # Move to failed folder
            failed_path = os.path.join("/home/team/shared/invoices/failed", file_name)
            os.rename(file_path, failed_path)
            logger.info(f"Moved to failed: {failed_path}")

if __name__ == "__main__":
    STORAGE_PATH = os.path.abspath(os.getenv("INVOICE_INCOMING_DIR", "/home/team/shared/invoices/incoming"))
    
    if not os.path.exists(STORAGE_PATH):
        os.makedirs(STORAGE_PATH)
    
    # Ensure processed/failed directories exist
    os.makedirs("/home/team/shared/invoices/processed", exist_ok=True)
    os.makedirs("/home/team/shared/invoices/failed", exist_ok=True)

    event_handler = IntegratedWatcher(STORAGE_PATH)
    observer = Observer()
    observer.schedule(event_handler, STORAGE_PATH, recursive=False)
    
    logger.info(f"Monitoring directory: {STORAGE_PATH}")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
