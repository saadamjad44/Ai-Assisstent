import time
import os
import subprocess
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
VAULT_PATH = Path("d:/practice/AI_Employee/AI-Employee-Vault")
INBOX_DIR = VAULT_PATH / "Inbox"
PROCESSED_DIR = INBOX_DIR / "Processed"
LOGS_DIR = VAULT_PATH / "Logs"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

class InboxHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = Path(event.src_path)
        
        # Support both .txt and .md files
        if filepath.suffix.lower() in ['.txt', '.md']:
            print(f"[Watcher] Detected new task: {filepath.name}")
            self.process_task(filepath)

    def process_task(self, filepath):
        try:
            # 1. Log receipt
            self.log_event(f"Received task: {filepath.name}")

            # 2. Trigger CCR (Claude Code Router)
            CCR_SCRIPT = Path(__file__).parent / "ccr.bat"
            print(f"[Watcher] Triggering CCR ({CCR_SCRIPT.name}) for {filepath.name}...")
            
            prompt = (
                f"Use the content of '{filepath}' to build a high-quality website. "
                f"Save the RESULTING CODE (HTML/CSS/JS) into a new folder in '{VAULT_PATH}/Done'. "
                f"Do not move the text file itself to Done. "
                "Follow the standards in CLAUDE.md and AGENTS.md."
            )
            
            # Use strict call to the bat file
            # We pass the prompt as an argument. 
            # If Claude expects it purely interactive, we also print it for manual copy-paste.
            
            print("="*60)
            print("AUTOMATION ATTEMPTED. IF CLAUDE ASKS FOR INPUT, COPY-PASTE THIS:")
            print(prompt)
            print("="*60)

            # Use string command for Windows compatibility when shell=True
            command = f'"{CCR_SCRIPT}" -p "{prompt}"'
            print(f"[Watcher] Executing: {command}")
            subprocess.run(command, shell=True, check=False)
            
            print(f"[Watcher] CCR finished processing {filepath.name}")

            # 3. Move original file to Processed to avoid re-triggering (and keep Inbox clean)
            target_path = PROCESSED_DIR / filepath.name
            if target_path.exists():
                timestamp = int(time.time())
                target_path = PROCESSED_DIR / f"{filepath.stem}_{timestamp}{filepath.suffix}"
            
            shutil.move(str(filepath), str(target_path))
            print(f"[Watcher] Archived instruction to {target_path}")

        except Exception as e:
            print(f"[Error] Failed to process {filepath.name}: {e}")
            self.log_event(f"Error processing {filepath.name}: {e}")

    def log_event(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_file = LOGS_DIR / f"watcher_log_{time.strftime('%Y-%m')}.md"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"- **{timestamp}**: {message}\n")

    def check_existing_tasks(self):
        print(f"[Watcher] Checking for existing tasks in {INBOX_DIR}...")
        for filepath in INBOX_DIR.glob("*"):
            if filepath.is_file() and filepath.suffix.lower() in ['.txt', '.md'] and filepath.parent.name == "Inbox":
                print(f"[Watcher] Processing existing task: {filepath.name}")
                self.process_task(filepath)

if __name__ == "__main__":
    print(f"Starting Inbox Watcher...")
    print(f"Monitoring: {INBOX_DIR}")
    
    event_handler = InboxHandler()
    
    # Process existing files first
    event_handler.check_existing_tasks()
    
    observer = Observer()
    observer.schedule(event_handler, str(INBOX_DIR), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
