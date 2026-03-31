"""
WhatsApp Watcher - Monitors WhatsApp Web for unread messages using Selenium.
Part of Silver Tier requirements.

Flow:
  1. Scan sidebar for all chats with unread badges
  2. Collect chat names first (to avoid stale DOM refs)
  3. For EACH chat: search & open → read ALL unread messages → reply or queue
  4. After processing, mark chat as unread (so owner sees activity)

Requirements:
    pip install selenium webdriver-manager
"""

import time
import re
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, StaleElementReferenceException,
    NoSuchElementException, ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains

import shutil
import json
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('WhatsAppWatcher')


class WhatsAppWatcher:
    def __init__(self, vault_path: str, check_interval: int = 60, headless: bool = False):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.headless = headless
        self.driver = None

        # Directories
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.needs_action_dir.mkdir(parents=True, exist_ok=True)

        self.pending_approval_dir = self.vault_path / "Pending_Approval"
        self.pending_approval_dir.mkdir(parents=True, exist_ok=True)

        self.approved_dir = self.vault_path / "Approved" / "whatsapp"
        self.approved_dir.mkdir(parents=True, exist_ok=True)

        self.done_dir = self.vault_path / "Done"
        self.done_dir.mkdir(parents=True, exist_ok=True)

        self.processed_ids_path = self.vault_path.parent / "scripts" / "whatsapp_processed_ids.txt"
        self.processed_ids = self._load_processed_ids()

        # Chrome User Data Directory for persistent session
        self.user_data_dir = self.vault_path.parent / "scripts" / "chrome_user_data"
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        # First scan flag: on startup, mark all existing messages as seen
        # without replying. Only reply to messages that arrive AFTER first scan.
        self._first_scan_done = False

    # ─────────────────────────────────────────────────────────────
    #  PROCESSED IDS
    # ─────────────────────────────────────────────────────────────
    def _load_processed_ids(self) -> set:
        if self.processed_ids_path.exists():
            with open(self.processed_ids_path, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _save_processed_id(self, item_id: str):
        self.processed_ids.add(item_id)
        with open(self.processed_ids_path, 'a') as f:
            f.write(f"{item_id}\n")

    # ─────────────────────────────────────────────────────────────
    #  DRIVER INIT
    # ─────────────────────────────────────────────────────────────
    def _init_driver(self):
        """Initialize Chrome Driver with persistent profile."""
        try:
            options = Options()
            if self.headless:
                options.add_argument("--headless=new")

            options.add_argument(f"user-data-dir={self.user_data_dir.absolute()}")
            options.add_argument("--profile-directory=Default")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--start-maximized")
            options.add_argument("--log-level=3")

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Chrome Driver initialized successfully.")
            return True
        except WebDriverException as e:
            if "user data directory is already in use" in str(e).lower():
                logger.error("CRITICAL: Chrome profile is already in use! Close other Chrome windows.")
            else:
                logger.error(f"WebDriver Error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Chrome Driver: {e}")
            return False

    # ─────────────────────────────────────────────────────────────
    #  AUTO-REPLIES CONFIG
    # ─────────────────────────────────────────────────────────────
    def _load_auto_replies(self):
        """Load auto-reply configuration."""
        reply_path = self.vault_path.parent / "scripts" / "whatsapp_auto_replies.json"
        if reply_path.exists():
            try:
                with open(reply_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading auto-replies: {e}")
        return {}

    # ─────────────────────────────────────────────────────────────
    #  MESSAGING HELPERS
    # ─────────────────────────────────────────────────────────────
    def _find_input_box(self, timeout=8):
        """Find the message input box with WebDriverWait + multiple fallback selectors."""
        selectors = [
            "div[contenteditable='true'][data-tab='10']",
            "div[contenteditable='true'][data-tab='6']",
            "footer div[contenteditable='true']",
            "div[title='Type a message']",
        ]
        # First try with explicit wait (most reliable)
        for sel in selectors:
            try:
                elem = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                if elem:
                    return elem
            except:
                continue
        # Fallback: instant lookup
        for sel in selectors:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                if elem:
                    return elem
            except:
                continue
        return None

    def _type_and_send(self, input_box, message_text):
        """Type a message into the input box and press Enter to send."""
        input_box.click()
        time.sleep(0.5)
        for line in message_text.split('\n'):
            if not line.strip():
                continue
            input_box.send_keys(line)
            input_box.send_keys(Keys.SHIFT + Keys.ENTER)
        time.sleep(0.8)
        input_box.send_keys(Keys.ENTER)
        time.sleep(1.5)

    def _send_reply_to_active_chat(self, message_text, max_retries=2):
        """Send a message to the currently open chat with retry logic."""
        for attempt in range(max_retries):
            try:
                input_box = self._find_input_box(timeout=5)
                if not input_box:
                    logger.warning(f"Input box not found (attempt {attempt+1}/{max_retries}). Waiting...")
                    time.sleep(2)
                    continue
                self._type_and_send(input_box, message_text)
                logger.info(f"Reply sent successfully.")
                return True
            except StaleElementReferenceException:
                logger.warning(f"Stale input box (attempt {attempt+1}/{max_retries}). Retrying...")
                time.sleep(2)
                continue
            except Exception as e:
                logger.error(f"Error replying (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(2)
                continue
        logger.error("Failed to send reply after all retries.")
        return False

    def send_message(self, contact_name, message_text):
        """Send a message to a specific contact by searching for their name."""
        try:
            logger.info(f"Sending message to: {contact_name}")
            if not self._open_chat_by_name(contact_name):
                return False

            input_box = self._find_input_box()
            if not input_box:
                logger.error(f"Could not find input box for {contact_name}")
                return False

            self._type_and_send(input_box, message_text)
            logger.info(f"Message sent to {contact_name}")
            return True

        except Exception as e:
            logger.error(f"Error sending message to {contact_name}: {e}")
            return False

    def _open_chat_by_name(self, contact_name, max_retries=2):
        """Open a chat by searching for the contact name in the search box.
        Includes retry logic for reliability."""
        for attempt in range(max_retries):
            try:
                # Find search box
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']"))
                )
                search_box.click()
                time.sleep(0.5)
                
                # Clear thoroughly
                search_box.send_keys(Keys.CONTROL + "a")
                time.sleep(0.2)
                search_box.send_keys(Keys.BACKSPACE)
                time.sleep(0.5)

                # Type contact name
                search_box.send_keys(contact_name)
                time.sleep(2.5)  # Give search results time to populate
                
                # Try multiple strategies to click the first search result
                clicked = False

                # Strategy 1: span with matching title
                try:
                    results = self.driver.find_elements(
                        By.XPATH,
                        f"//span[@title and contains(translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{contact_name.lower()[:20]}')]"
                    )
                    if results:
                        results[0].click()
                        clicked = True
                except:
                    pass

                # Strategy 2: first item in search results pane
                if not clicked:
                    try:
                        first_result = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//div[@aria-label='Search results.']/div[1]")
                            )
                        )
                        first_result.click()
                        clicked = True
                    except:
                        pass

                # Strategy 3: press Enter as last resort
                if not clicked:
                    search_box.send_keys(Keys.ENTER)
                
                time.sleep(2)

                # Verify chat opened by checking header
                try:
                    header_elem = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "header span[title]"))
                    )
                    opened_name = header_elem.get_attribute("title")
                    # Check if any meaningful word of contact name appears in header
                    name_words = contact_name.lower().split()
                    name_match = any(w in opened_name.lower() for w in name_words if len(w) > 2)
                    if name_match or contact_name.lower()[:10] in opened_name.lower():
                        # Clear the search box so sidebar resets
                        try:
                            search_box2 = self.driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']")
                            search_box2.send_keys(Keys.CONTROL + "a")
                            search_box2.send_keys(Keys.BACKSPACE)
                        except: pass
                        return True
                    else:
                        logger.warning(f"Attempt {attempt+1}: Header mismatch: expected '{contact_name}', got '{opened_name}'. Proceeding anyway.")
                        try:
                            search_box2 = self.driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']")
                            search_box2.send_keys(Keys.CONTROL + "a")
                            search_box2.send_keys(Keys.BACKSPACE)
                        except: pass
                        return True  # Proceed even on mismatch
                except:
                    logger.warning(f"Attempt {attempt+1}: Could not verify chat header.")
                    return True  # Proceed anyway, might still be correct

            except Exception as e:
                logger.error(f"Attempt {attempt+1}: Failed to open chat for '{contact_name}': {e}")
                time.sleep(1)

        logger.error(f"Could not open chat for '{contact_name}' after {max_retries} attempts.")
        return False

    def _go_back_to_chat_list(self):
        """Press Escape to go back to the chat list / side panel."""
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            pass



    # ─────────────────────────────────────────────────────────────
    #  COLLECT UNREAD CHAT NAMES (step 1 – safe from stale refs)
    # ─────────────────────────────────────────────────────────────
    def _collect_unread_chat_names(self):
        """Scan the sidebar and collect names of all chats that have unread badges.
        Returns a list of unique contact names.
        Uses multiple strategies to handle different WhatsApp Web DOM structures.
        """
        chat_names = []
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "pane-side"))
            )
        except TimeoutException:
            logger.warning("Timeout waiting for chat list. Ensure you are logged in.")
            return []

        # Small wait for sidebar to fully render
        time.sleep(1)

        unread_icons = self.driver.find_elements(By.CSS_SELECTOR, "span[aria-label*='unread message']")
        if not unread_icons:
            return []

        logger.info(f"Found {len(unread_icons)} unread chat(s) in sidebar.")

        for idx, icon in enumerate(unread_icons[:15]):
            try:
                name = None

                # STRATEGY 1: Walk up to a listitem / row and find span[title]
                ancestor_xpaths = [
                    "./ancestor::div[@role='row']",
                    "./ancestor::div[@role='listitem']",
                    "./ancestor::div[contains(@class, 'x10l6tqk')]",
                    "./ancestor::div[@data-testid]",
                    "./ancestor::div[.//span[@title]]",  # any ancestor that contains span[title]
                ]
                for xpath in ancestor_xpaths:
                    try:
                        chat_row = icon.find_element(By.XPATH, xpath)
                        name_elem = chat_row.find_element(By.CSS_SELECTOR, "span[title]")
                        candidate = name_elem.get_attribute("title")
                        if candidate and not self._is_ui_text(candidate):
                            name = candidate
                            break
                    except:
                        continue

                # STRATEGY 2: Go up N levels manually and look for span[title]
                if not name:
                    current = icon
                    for _ in range(8):  # Walk up max 8 levels
                        try:
                            current = current.find_element(By.XPATH, "..")
                            try:
                                name_elem = current.find_element(By.CSS_SELECTOR, "span[title]")
                                candidate = name_elem.get_attribute("title")
                                if candidate and not self._is_ui_text(candidate):
                                    name = candidate
                                    break
                            except:
                                continue
                        except:
                            break

                if name and name not in chat_names:
                    chat_names.append(name)
                    logger.info(f"  [{idx+1}] Unread chat: '{name}'")
                elif not name:
                    logger.warning(f"  [{idx+1}] Could not extract chat name for unread icon.")

            except StaleElementReferenceException:
                logger.warning(f"  [{idx+1}] Stale element, skipping.")
                continue
            except Exception as e:
                logger.error(f"  [{idx+1}] Error extracting chat name: {e}")
                continue

        logger.info(f"Collected {len(chat_names)} unread chat name(s) to process.")
        return chat_names

    def _is_ui_text(self, text):
        """Check if a string looks like WhatsApp UI text rather than a real contact name."""
        ui_patterns = [
            r"last seen",
            r"online",
            r"typing",
            r"profile details",
            r"click here",
            r"^\d{1,2}:\d{2}",  # starts with time like "3:06 PM"
        ]
        lower = text.lower().strip()
        for pat in ui_patterns:
            if re.search(pat, lower):
                return True
        return False

    # ─────────────────────────────────────────────────────────────
    #  EXTRACT MESSAGES FROM OPEN CHAT
    # ─────────────────────────────────────────────────────────────
    def _extract_incoming_messages(self, sender_name):
        """Extract all recent incoming (message-in) messages from the currently open chat.
        Returns list of dicts with 'text', 'stable_id', 'meta_info'.
        Only returns messages NOT yet in processed_ids.
        """
        messages = []
        msg_containers = self.driver.find_elements(By.CSS_SELECTOR, "div.message-in")

        if not msg_containers:
            logger.info(f"No incoming messages found for {sender_name}")
            return []

        # Scan the last 15 messages to catch all unread ones
        recent_containers = msg_containers[-15:]
        logger.info(f"Scanning last {len(recent_containers)} incoming messages from '{sender_name}'...")

        for container in recent_containers:
            try:
                # Extract text
                msg_text = ""
                try:
                    text_elements = container.find_elements(By.CSS_SELECTOR, "span.selectable-text, .copyable-text")
                    if text_elements:
                        msg_text = text_elements[-1].text
                except:
                    pass

                if not msg_text or msg_text.strip() == "" or msg_text == "[No Text]":
                    continue

                # Extract metadata for stable ID
                meta_info = ""
                try:
                    copyable = container.find_element(By.CSS_SELECTOR, ".copyable-text")
                    meta_info = copyable.get_attribute("data-pre-plain-text") or ""
                except:
                    pass

                # Generate stable ID
                if not meta_info:
                    id_basis = f"{sender_name}|NO_TIME|{msg_text}"
                else:
                    id_basis = f"{sender_name}|{meta_info}|{msg_text}"

                msg_hash = hashlib.md5(id_basis.encode()).hexdigest()[:16]
                stable_id = f"wa_{msg_hash}"

                # Skip already processed
                if stable_id in self.processed_ids:
                    continue

                messages.append({
                    'text': msg_text,
                    'stable_id': stable_id,
                    'meta_info': meta_info,
                })

            except StaleElementReferenceException:
                continue
            except Exception as e:
                logger.error(f"Error extracting message container: {e}")
                continue

        logger.info(f"Found {len(messages)} NEW message(s) from '{sender_name}'.")
        return messages

    # ─────────────────────────────────────────────────────────────
    #  MAIN CHECK MESSAGES – COLLECT-THEN-PROCESS PATTERN
    # ─────────────────────────────────────────────────────────────
    def check_messages(self):
        """Check for unread messages, auto-reply to each, and queue the rest.
        
        Pattern:
          1. Collect all unread chat names from the sidebar (safe snapshot)
          2. FIRST SCAN: mark all existing messages as 'seen' (no replies)
          3. SUBSEQUENT SCANS: reply to truly new messages only
          4. Opening chat removes green dot naturally (WhatsApp marks as read)
        """
        updates = []
        auto_replies = self._load_auto_replies()

        # STEP 1: Collect all unread chat names from sidebar
        chat_names = self._collect_unread_chat_names()
        if not chat_names:
            if not self._first_scan_done:
                # Even with no unread chats, mark first scan as done
                self._first_scan_done = True
                logger.info("FIRST SCAN: No unread chats. Ready to watch for new messages.")
            return []

        # FIRST SCAN: Mark all existing messages as processed WITHOUT replying
        if not self._first_scan_done:
            logger.info("="*60)
            logger.info("FIRST SCAN: Marking all existing messages as SEEN (no replies)")
            logger.info("Only messages arriving AFTER this scan will be replied to.")
            logger.info("="*60)
            
            for chat_name in chat_names:
                try:
                    if not self._open_chat_by_name(chat_name):
                        continue
                    time.sleep(1)
                    
                    # Extract sender name
                    sender_name = chat_name
                    try:
                        for sel in ["header span[title]", "header div[title]"]:
                            try:
                                hdr = self.driver.find_element(By.CSS_SELECTOR, sel)
                                hdr_name = hdr.get_attribute("title")
                                if hdr_name and not self._is_ui_text(hdr_name):
                                    sender_name = hdr_name
                                    break
                            except: continue
                    except: pass
                    
                    # Mark all messages as processed (no reply)
                    all_msgs = self._extract_incoming_messages(sender_name)
                    for msg in all_msgs:
                        self._save_processed_id(msg['stable_id'])
                        logger.info(f"  Marked as seen: [{msg['stable_id']}] {msg['text'][:40]}...")
                    
                    logger.info(f"  → Marked {len(all_msgs)} message(s) from '{sender_name}' as seen.")
                    
                    # Go back (opening chat already removed green dot)
                    self._go_back_to_chat_list()
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error during first scan for '{chat_name}': {e}")
                    self._go_back_to_chat_list()
                    continue
            
            self._first_scan_done = True
            logger.info("FIRST SCAN COMPLETE. Now watching for NEW messages only.")
            return []

        # STEP 2: Process each chat one by one (only runs after first scan)
        for chat_name in chat_names:
            try:
                logger.info(f"\n{'='*50}")
                logger.info(f"Processing chat: '{chat_name}'")
                logger.info(f"{'='*50}")

                # Open the chat by searching
                # NOTE: Opening the chat REMOVES the green dot (WhatsApp marks as read)
                if not self._open_chat_by_name(chat_name):
                    logger.error(f"Could not open chat for '{chat_name}'. Skipping.")
                    continue

                time.sleep(1)

                # Verify sender name from header
                sender_name = chat_name
                try:
                    for sel in ["header span[title]", "header div[title]"]:
                        try:
                            header_elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                            hdr_name = header_elem.get_attribute("title")
                            if hdr_name and not self._is_ui_text(hdr_name):
                                sender_name = hdr_name
                                break
                        except:
                            continue
                except:
                    pass

                # STEP 3: Extract ALL new incoming messages
                new_messages = self._extract_incoming_messages(sender_name)

                if not new_messages:
                    logger.info(f"No new messages to process for '{sender_name}'.")
                    self._go_back_to_chat_list()
                    continue

                # STEP 4: Process EACH message – auto-reply or queue for approval
                for msg in new_messages:
                    msg_text = msg['text']
                    stable_id = msg['stable_id']

                    logger.info(f"  → Message [{stable_id}]: {msg_text[:50]}...")

                    # Try auto-reply
                    reply_sent = False
                    if auto_replies:
                        clean_msg = msg_text.lower().strip()
                        for keyword, response in auto_replies.items():
                            k_lower = keyword.lower().strip()
                            # Use regex matching with word boundaries to avoid partial matches
                            # e.g. "ship" should not match "hi", "pricey" should not match "price"
                            pattern = r'(?:\b|^)' + re.escape(k_lower) + r'(?:\b|$)'
                            if re.search(pattern, clean_msg):
                                logger.info(f"    AUTO-REPLY MATCH! Keyword: '{keyword}'. Replying...")
                                if self._send_reply_to_active_chat(response):
                                    reply_sent = True
                                    self._save_processed_id(stable_id)
                                    time.sleep(2)  # Extra wait for DOM to settle before next reply
                                    break
                                else:
                                    logger.warning(f"    Reply FAILED for keyword '{keyword}'. Will queue for approval.")

                    # If no auto-reply match (or reply failed), queue for approval
                    if not reply_sent:
                        logger.info(f"    No auto-reply match. Queuing for approval.")
                        updates.append({
                            'type': 'whatsapp',
                            'id': stable_id,
                            'text': msg_text,
                            'actor': sender_name,
                            'timestamp': datetime.now().isoformat()
                        })
                        self._save_processed_id(stable_id)  # Mark processed to avoid re-queue

                # Done with this chat – go back to sidebar
                # Green dot is already gone because we opened the chat
                self._go_back_to_chat_list()
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error processing chat '{chat_name}': {e}")
                self._go_back_to_chat_list()
                continue

        return updates

    # ─────────────────────────────────────────────────────────────
    #  CHECK OUTBOX (approved replies to send)
    # ─────────────────────────────────────────────────────────────
    def check_outbox(self):
        """Check Approved/whatsapp for messages to send."""
        for task_file in self.approved_dir.glob('*.md'):
            try:
                logger.info(f"Processing approved message for delivery: {task_file.name}")
                content = task_file.read_text(encoding='utf-8')

                # Parse target (From:)
                target = "Unknown"
                message = ""

                lines = content.split('\n')
                for line in lines:
                    clean_line = line.strip()
                    if clean_line.lower().startswith("from:"):
                        target = clean_line.split(":", 1)[1].strip()
                        break
                    elif clean_line.startswith("**From:**"):
                        target = clean_line.replace("**From:**", "").strip()
                        break
                    elif clean_line.startswith("## From:"):
                        target = clean_line.replace("## From:", "").strip()
                        break

                # Extract Message Content
                if "## Agent Response" in content:
                    message_part = content.split("## Agent Response", 1)[1]
                    message = message_part.split("\n##", 1)[0].strip()
                elif "Response:" in content:
                    message = content.split("Response:", 1)[1].strip()
                elif "Message:" in content:
                    message = content.split("Message:", 1)[1].strip()

                # Skip placeholder
                if "[Type your reply here" in message:
                    logger.warning(f"Approval file {task_file.name} still contains placeholder. Skipping.")
                    continue

                if target != "Unknown" and message:
                    logger.info(f"Sending approved response to '{target}'...")
                    if self.send_message(target, message.strip()):
                        # Move to Done
                        done_path = self.done_dir / task_file.name
                        if done_path.exists():
                            done_path = self.done_dir / f"{int(time.time())}_{task_file.name}"
                        shutil.move(str(task_file), str(done_path))
                        logger.info(f"Successfully sent and archived: {task_file.name}")

                        # Chat is already marked as read (green dot removed)
                        # by opening it via send_message → _open_chat_by_name
                    else:
                        logger.error(f"Failed to send to {target}. Will retry next cycle.")
                else:
                    logger.warning(f"Could not parse Target ({target}) or Message (len={len(message)}) from {task_file.name}")

            except Exception as e:
                logger.error(f"Error processing outbox file {task_file.name}: {e}")

    # ─────────────────────────────────────────────────────────────
    #  CREATE PENDING APPROVAL FILE
    # ─────────────────────────────────────────────────────────────
    def create_action_file(self, item) -> Path:
        """Create a markdown file in Pending_Approval for Dashboard review."""
        try:
            content = f"""---
type: {item['type']}
id: {item['id']}
from: {item.get('actor', 'Unknown')}
received: {item['timestamp']}
priority: high
status: pending_approval
---
## WhatsApp Message

**From:** {item.get('actor', 'Unknown')}

**Content:**
{item.get('text', 'No content available')}

## Agent Response
[Type your reply here or let AI generate it]

## Suggested Actions
- [ ] Approve to send the above 'Agent Response' to {item.get('actor', 'Unknown')}
- [ ] Edit the 'Agent Response' section before approving
- [ ] Reject if no action needed
"""
            raw_actor = item.get('actor', 'Unknown')
            if len(raw_actor) > 50:
                raw_actor = raw_actor[:47] + "..."

            safe_actor = "".join([c for c in raw_actor if c.isalnum()]).strip()
            safe_filename_part = safe_actor[:30]
            filename = f"WHATSAPP_{safe_filename_part}_{int(time.time())}.md"
            filepath = self.pending_approval_dir / filename

            if not filepath.exists():
                filepath.write_text(content, encoding='utf-8')
                logger.info(f"Created approval file: {filename} in Pending_Approval")

            self._save_processed_id(item['id'])
            return filepath
        except Exception as e:
            logger.error(f"Error creating action file: {e}")
            return None

    # ─────────────────────────────────────────────────────────────
    #  MAIN LOOP
    # ─────────────────────────────────────────────────────────────
    def run(self):
        """Main loop with auto-reconnection."""
        logger.info("Starting WhatsApp Watcher (Selenium)...")

        while True:
            try:
                if not self.driver:
                    if not self._init_driver():
                        logger.error("Initialization failed. Retrying in 30 seconds...")
                        time.sleep(30)
                        continue

                try:
                    self.driver.get("https://web.whatsapp.com")
                    logger.info("Opened WhatsApp Web. Please scan QR code if not logged in.")

                    # Wait for initial load
                    time.sleep(10)

                    while True:
                        try:
                            # 1. Check Messages (Auto-Replies + Pending Approval)
                            updates = self.check_messages()

                            for item in updates:
                                self.create_action_file(item)

                            # 2. Check Outbox (Approved Replies)
                            self.check_outbox()

                        except (WebDriverException, ConnectionError) as e:
                            logger.error(f"Browser connection lost: {e}")
                            break
                        except Exception as e:
                            logger.error(f"Error in check loop: {e}")

                        time.sleep(self.check_interval)

                except WebDriverException as e:
                    logger.error(f"Failed to navigate to WhatsApp: {e}. Retrying...")
                    time.sleep(15)

            except KeyboardInterrupt:
                logger.info("Stopping watcher...")
                break
            except Exception as e:
                logger.critical(f"Critical error in outer loop: {e}")
                time.sleep(30)
            finally:
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None


if __name__ == "__main__":
    VAULT = "d:/practice/AI_Employee/AI-Employee-Vault"

    import sys
    headless_mode = "--headless" in sys.argv

    watcher = WhatsAppWatcher(VAULT, headless=headless_mode)
    watcher.run()
