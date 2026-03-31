"""
LinkedIn Watcher - Monitors LinkedIn notifications and messages using Selenium.
Replaced Playwright due to Python 3.14 incompatibility.

Requirements:
    pip install selenium webdriver-manager
"""

import time
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('LinkedInWatcher')

class LinkedInWatcher:
    def __init__(self, vault_path: str, cookies_path: str = None, check_interval: int = 300, headless: bool = True):
        self.vault_path = Path(vault_path)
        self.cookies_path = Path(cookies_path) if cookies_path else self.vault_path.parent / "scripts" / "linkedin_cookies.json"
        self.check_interval = check_interval
        self.headless = headless
        self.driver = None
        
        # Directories
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.needs_action_dir.mkdir(parents=True, exist_ok=True)
        
        self.processed_ids_path = self.vault_path.parent / "scripts" / "linkedin_processed_ids.txt"
        self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self) -> set:
        if self.processed_ids_path.exists():
            with open(self.processed_ids_path, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _save_processed_id(self, item_id: str):
        self.processed_ids.add(item_id)
        with open(self.processed_ids_path, 'a') as f:
            f.write(f"{item_id}\n")

    def _load_cookies(self):
        if self.cookies_path.exists():
            with open(self.cookies_path, 'r') as f:
                return json.load(f)
        return []
    
    def _sanitize_cookies(self, cookies):
        """Ensure cookies are in a format Selenium accepts."""
        sanitized = []
        for cookie in cookies:
            new_cookie = {}
            # Selenium needs: name, value. Optional: path, domain, secure, expiry
            if 'name' not in cookie or 'value' not in cookie:
                continue
                
            new_cookie['name'] = cookie['name']
            new_cookie['value'] = cookie['value']
            
            if 'path' in cookie:
                new_cookie['path'] = cookie['path']
            if 'domain' in cookie:
                # Selenium can be strict about domains. 
                # If domain starts with '.', keep it.
                new_cookie['domain'] = cookie['domain']
            if 'secure' in cookie:
                new_cookie['secure'] = cookie['secure']
            if 'expiry' in cookie:
                new_cookie['expiry'] = int(cookie['expiry'])
            elif 'expires' in cookie:
                new_cookie['expiry'] = int(cookie['expires'])
                
            sanitized.append(new_cookie)
        return sanitized

    def _init_driver(self):
        """Initialize Chrome Driver."""
        try:
            options = Options()
            if self.headless:
                options.add_argument("--headless=new")
            
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--log-level=3")  # Suppress console logs
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Chrome Driver initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Chrome Driver: {e}")
            return False

    def check_messages(self):
        """Navigate to messaging and check for unread conversations."""
        updates = []
        try:
            logger.info("Navigating to LinkedIn Messaging...")
            self.driver.get("https://www.linkedin.com/messaging/")
            
            # Wait for conversation list
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".msg-conversations-container__conversations-list"))
                )
            except TimeoutException:
                logger.warning("Timeout waiting for conversation list. Checking for login...")
                if len(self.driver.find_elements(By.ID, "username")) > 0:
                     logger.error("Redirected to login page. Cookies might be expired.")
                else:
                     # Identify if it's just slow or actually failed
                     source = self.driver.page_source[:500]
                     logger.warning(f"Page content preview: {source}...")
                return []

            # Find conversation cards
            conversations = self.driver.find_elements(By.CSS_SELECTOR, ".msg-conversation-card")
            logger.info(f"Found {len(conversations)} visible conversations.")
            
            for conv in conversations[:10]:
                try:
                    # Check for unread badge
                    # Selenium lookup is relative to the element
                    unread_badges = conv.find_elements(By.CSS_SELECTOR, ".msg-conversation-card__unread-count")
                    
                    if len(unread_badges) > 0 and unread_badges[0].is_displayed():
                        # Extract details
                        name_elem = conv.find_elements(By.CSS_SELECTOR, ".msg-conversation-card__participant-names")
                        preview_elem = conv.find_elements(By.CSS_SELECTOR, ".msg-conversation-card__message-snippet")
                        
                        sender_name = name_elem[0].text.strip() if name_elem else "Unknown"
                        preview_text = preview_elem[0].text.strip() if preview_elem else "No preview"
                        
                        # ID generation
                        conv_id = f"linkedin_msg_{sender_name.replace(' ', '_')}_{int(time.time())}"
                        
                        if conv_id not in self.processed_ids:
                            updates.append({
                                'type': 'message',
                                'id': conv_id,
                                'text': preview_text,
                                'actor': sender_name,
                                'timestamp': datetime.now().isoformat()
                            })
                            logger.info(f"New unread message detected from {sender_name}")
                except Exception as e:
                    logger.warning(f"Error processing a conversation card: {e}")
                    continue
                    
            logger.info(f"Found {len(updates)} unread conversations to process.")
            
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
            try:
                debug_path = self.vault_path.parent / "scripts" / "selenium_debug.png"
                self.driver.save_screenshot(str(debug_path))
                logger.info(f"Saved debug screenshot to {debug_path}")
            except:
                pass
                
        return updates

    def create_action_file(self, item) -> Path:
        """Create a markdown file in Needs_Action."""
        try:
            content = f"""---
type: linkedin_{item['type']}
id: {item['id']}
from: {item.get('actor', 'Unknown')}
received: {item['timestamp']}
priority: medium
status: pending
---
## LinkedIn {item['type'].title()}

**From:** {item.get('actor', 'Unknown')}

**Preview:**
{item.get('text', 'No content available')}

## Suggested Actions
- [ ] Open LinkedIn and read full message
- [ ] Reply if appropriate
- [ ] Archive after processing
"""
            safe_actor = "".join([c for c in item.get('actor', 'Unknown') if c.isalnum()]).strip()
            filename = f"LINKEDIN_{item['type'].upper()}_{safe_actor}_{int(time.time())}.md"
            filepath = self.needs_action_dir / filename
            
            if not filepath.exists():
                filepath.write_text(content, encoding='utf-8')
                logger.info(f"Created action file: {filename}")
            
            self._save_processed_id(item['id'])
            return filepath
        except Exception as e:
            logger.error(f"Error creating action file: {e}")
            return None

    def run(self):
        """Main loop."""
        logger.info(f"Starting LinkedIn Watcher (Selenium)...")
        
        # Load cookies first
        cookies = self._load_cookies()
        if not cookies:
             logger.error("No cookies found. Exiting.")
             return

        while True:
            try:
                if not self._init_driver():
                    logger.error("Driver failed to initialize. Retrying in 60s...")
                    time.sleep(60)
                    continue
                
                # Go to domain to set cookies
                try:
                    self.driver.get("https://www.linkedin.com")
                    
                    sanitized_cookies = self._sanitize_cookies(cookies)
                    for cookie in sanitized_cookies:
                        try:
                            self.driver.add_cookie(cookie)
                        except Exception as ce:
                            logger.warning(f"Could not add cookie {cookie.get('name')}: {ce}")
                    
                    logger.info("Cookies added. Refreshing/Navigating...")
                    
                    # Now do the check
                    updates = self.check_messages()
                    
                    for item in updates:
                        self.create_action_file(item)
                        
                except Exception as e:
                    logger.error(f"Error during check execution: {e}")
                finally:
                    if self.driver:
                        self.driver.quit()
                        self.driver = None
                        
                logger.info(f"Sleeping for {self.check_interval} seconds...")
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.critical(f"Critical error: {e}. Restarting process in 60 seconds...")
                time.sleep(60)

if __name__ == "__main__":
    VAULT = "d:/practice/AI_Employee/AI-Employee-Vault"
    
    # Check if cookies exist
    cookies_path = Path("d:/practice/AI_Employee/scripts/linkedin_cookies.json")
    if not cookies_path.exists():
        print("\n[ERROR] Cookies file not found! Please export cookies to 'd:/practice/AI_Employee/scripts/linkedin_cookies.json'")
    else:
        # Check if headless arg is passed
        headless_mode = "--headless" in sys.argv or "--visible" not in sys.argv
        if "--visible" in sys.argv:
            print("Running in visible mode...")
            headless_mode = False

        watcher = LinkedInWatcher(VAULT, headless=headless_mode)
        watcher.run()
