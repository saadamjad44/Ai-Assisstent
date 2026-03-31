import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod

class BaseWatcher(ABC):  
    def __init__(self, vault_path: str, check_interval: int = 60):  
        self.vault_path = Path(vault_path)  
        self.needs_action = self.vault_path / 'Inbox' # Using current vault structure
        self.logs_dir = self.vault_path / 'Logs'
        self.check_interval = check_interval  
        
        # Setup logging
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.logs_dir / f"watcher_{self.__class__.__name__.lower()}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)  
          
    @abstractmethod  
    def check_for_updates(self) -> list:  
        '''Return list of new items to process'''  
        pass  
      
    @abstractmethod  
    def create_action_file(self, item) -> Path:  
        '''Create .md file in Inbox folder'''  
        pass  
      
    def log_to_vault(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        vault_log = self.logs_dir / f"watcher_log_{time.strftime('%Y-%m')}.md"
        with open(vault_log, "a", encoding="utf-8") as f:
            f.write(f"- **{timestamp}** ({self.__class__.__name__}): {message}\n")

    def run(self):  
        self.logger.info(f'Starting {self.__class__.__name__}')  
        while True:  
            try:  
                items = self.check_for_updates()  
                for item in items:  
                    filepath = self.create_action_file(item)
                    if filepath:
                        self.logger.info(f'Created action file: {filepath.name}')
                        self.log_to_vault(f"Detected new item, created {filepath.name}")
            except Exception as e:  
                self.logger.error(f'Error: {e}')  
            time.sleep(self.check_interval)
