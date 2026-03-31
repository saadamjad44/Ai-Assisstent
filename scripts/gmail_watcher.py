import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from pathlib import Path
from base_watcher import BaseWatcher

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, credentials_path: str):
        super().__init__(vault_path, check_interval=120)
        self.credentials_path = Path(credentials_path)
        self.token_path = self.credentials_path.parent / 'token.json'
        self.processed_ids_path = self.credentials_path.parent / 'processed_ids.txt'
        self.service = self._get_gmail_service()
        self.processed_ids = self._load_processed_ids()
        
    def _load_processed_ids(self):
        if self.processed_ids_path.exists():
            with open(self.processed_ids_path, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _save_processed_id(self, msg_id):
        self.processed_ids.add(msg_id)
        with open(self.processed_ids_path, 'a') as f:
            f.write(f"{msg_id}\n")

    def _get_gmail_service(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(f"Missing credentials.json at {self.credentials_path}. Please follow the instructions in implementation_plan.md")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)

    def mark_as_read(self, message_id):
        try:
            self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': [message_id],
                    'removeLabelIds': ['UNREAD']
                }
            ).execute()
            self.logger.info(f"Marked message {message_id} as read.")
        except HttpError as error:
            self.logger.error(f'An error occurred while marking as read: {error}')

    def check_for_updates(self) -> list:
        try:
            # Search for unread emails in the INBOX
            results = self.service.users().messages().list(
                userId='me', q='label:INBOX is:unread'
            ).execute()
            messages = results.get('messages', [])
            
            new_messages = []
            for m in messages:
                m_id = m['id']
                if m_id not in self.processed_ids:
                    # Double check if any file with this ID exists in the vault (all folders)
                    exists_in_vault = any(
                        list((self.vault_path / "Inbox").glob(f"EMAIL_{m_id}*")) +
                        list((self.vault_path / "Inbox" / "Processed").glob(f"EMAIL_{m_id}*"))
                    )
                    
                    if not exists_in_vault:
                        new_messages.append(m)
                    else:
                        self.logger.info(f"ID {m_id} already exists in vault, adding to local persistence.")
                        self._save_processed_id(m_id)
            
            return new_messages
        except HttpError as error:
            self.logger.error(f'An error occurred: {error}')
            return []

    def create_action_file(self, message) -> Path:
        try:
            msg = self.service.users().messages().get(
                userId='me', id=message['id']
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
            
            subject = headers.get('Subject', 'No Subject')
            sender = headers.get('From', 'Unknown')
            date_received = headers.get('Date', datetime.now().isoformat())
            snippet = msg.get('snippet', '')
            
            content = f"""---
type: email
id: {message['id']}
from: {sender}
subject: {subject}
received: {date_received}
priority: high
status: pending
---

## Email Content
{snippet}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
"""
            # Clean filename
            safe_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '-', '_')]).rstrip()
            filename = f"EMAIL_{message['id']}_{safe_subject[:30]}.md"
            filepath = self.needs_action / filename
            
            # Check one last time before writing
            if not filepath.exists():
                filepath.write_text(content, encoding='utf-8')
                self.logger.info(f"Created action file: {filename}")
            
            # Persist and mark as read
            self._save_processed_id(message['id'])
            self.mark_as_read(message['id'])
            
            return filepath
        except Exception as e:
            self.logger.error(f'Failed to create action file for {message["id"]}: {e}')
            return None

if __name__ == "__main__":
    VAULT = "d:/practice/AI_Employee/AI-Employee-Vault"
    CREDS = "d:/practice/AI_Employee/scripts/credentials.json"
    
    watcher = GmailWatcher(VAULT, CREDS)
    watcher.run()
