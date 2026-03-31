"""
LinkedIn Poster - Posts content to LinkedIn on behalf of the user.
Uses cookie-based authentication for personal account access.

Posts are read from /Pending_Approval/linkedin/ folder.
After approval (moved to /Approved/linkedin/), the post is published.
"""

import json
import time
from pathlib import Path
from datetime import datetime
import logging
import requests
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LinkedInPoster:
    """
    Posts content to LinkedIn.
    Monitors /Approved/linkedin/ for approved posts.
    """
    
    def __init__(self, vault_path: str, cookies_path: str = None):
        self.vault_path = Path(vault_path)
        self.session = requests.Session()
        self.cookies_path = Path(cookies_path) if cookies_path else self.vault_path.parent / "scripts" / "linkedin_cookies.json"
        self.base_url = "https://www.linkedin.com"
        self.api_url = "https://www.linkedin.com/voyager/api"
        
        # Folders
        self.pending_dir = self.vault_path / "Pending_Approval" / "linkedin"
        self.approved_dir = self.vault_path / "Approved" / "linkedin"
        self.done_dir = self.vault_path / "Done" / "linkedin_posts"
        
        # Ensure directories exist
        self.pending_dir.mkdir(parents=True, exist_ok=True)
        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.done_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_cookies()
        self.csrf_token = self._get_csrf_token()
        
    def _load_cookies(self):
        """Load LinkedIn cookies from file."""
        if self.cookies_path.exists():
            with open(self.cookies_path, 'r') as f:
                cookies = json.load(f)
                for cookie in cookies:
                    self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', '.linkedin.com'))
            logger.info("LinkedIn cookies loaded successfully.")
        else:
            logger.warning(f"No cookies file found at {self.cookies_path}")
    
    def _get_csrf_token(self) -> str:
        """Extract CSRF token from JSESSIONID cookie."""
        jsessionid = self.session.cookies.get('JSESSIONID', '')
        # CSRF token is the JSESSIONID without quotes
        return jsessionid.replace('"', '')
    
    def _get_headers(self):
        """Get headers required for LinkedIn API requests."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/vnd.linkedin.normalized+json+2.1',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0',
            'X-Li-Lang': 'en_US',
            'csrf-token': self.csrf_token,
        }
    
    def parse_post_file(self, filepath: Path) -> dict:
        """Parse a markdown post file to extract content."""
        content = filepath.read_text(encoding='utf-8')
        
        # Extract YAML frontmatter
        metadata = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_content = parts[1].strip()
                for line in yaml_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
                content = parts[2].strip()
        
        # Extract post text (everything after ## Post Content header or main content)
        post_text = content
        if '## Post Content' in content:
            post_text = content.split('## Post Content', 1)[1].strip()
        
        # Clean up markdown formatting for plain text
        post_text = re.sub(r'\*\*(.+?)\*\*', r'\1', post_text)  # Bold
        post_text = re.sub(r'\*(.+?)\*', r'\1', post_text)  # Italic
        
        return {
            'text': post_text,
            'visibility': metadata.get('visibility', 'PUBLIC'),
            'scheduled': metadata.get('scheduled', None)
        }
    
    def create_post(self, text: str, visibility: str = 'PUBLIC') -> dict:
        """
        Create a post on LinkedIn.
        
        Args:
            text: The post content
            visibility: PUBLIC, CONNECTIONS, or LOGGED_IN
            
        Returns:
            Response dict with success status
        """
        try:
            # Get user profile URN first
            me_url = f"{self.api_url}/me"
            me_response = self.session.get(me_url, headers=self._get_headers())
            
            if me_response.status_code != 200:
                return {'success': False, 'error': f'Failed to get profile: {me_response.status_code}'}
            
            profile_data = me_response.json()
            member_urn = profile_data.get('entityUrn', profile_data.get('miniProfile', {}).get('entityUrn', ''))
            
            # Create post payload
            post_payload = {
                "author": member_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }
            
            # Post to LinkedIn
            post_url = f"{self.api_url}/ugcPosts"
            response = self.session.post(post_url, json=post_payload, headers=self._get_headers())
            
            if response.status_code in [200, 201]:
                logger.info("Post created successfully!")
                return {'success': True, 'response': response.json()}
            else:
                logger.error(f"Failed to create post: {response.status_code} - {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_approved_posts(self):
        """Process all approved posts in the /Approved/linkedin/ folder."""
        for post_file in self.approved_dir.glob('*.md'):
            logger.info(f"Processing approved post: {post_file.name}")
            
            try:
                post_data = self.parse_post_file(post_file)
                result = self.create_post(post_data['text'], post_data.get('visibility', 'PUBLIC'))
                
                if result['success']:
                    # Move to Done folder
                    done_path = self.done_dir / f"POSTED_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{post_file.name}"
                    post_file.rename(done_path)
                    logger.info(f"Post successful! Moved to {done_path}")
                else:
                    logger.error(f"Post failed: {result['error']}")
                    # Leave in approved folder for retry
                    
            except Exception as e:
                logger.error(f"Error processing post {post_file.name}: {e}")
    
    def run(self, check_interval: int = 60):
        """Run the poster in continuous mode."""
        logger.info(f"Starting LinkedIn Poster. Monitoring: {self.approved_dir}")
        
        while True:
            try:
                self.process_approved_posts()
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            
            time.sleep(check_interval)


# Template for creating a new post
POST_TEMPLATE = """---
type: linkedin_post
visibility: PUBLIC
scheduled: null
created: {timestamp}
status: pending_approval
---

## Post Content

Write your LinkedIn post here.

#hashtag1 #hashtag2

---
*Move this file to /Approved/linkedin/ to publish.*
"""


def create_post_template(vault_path: str, title: str = "new_post"):
    """Create a new post template in the Pending_Approval folder."""
    vault = Path(vault_path)
    pending_dir = vault / "Pending_Approval" / "linkedin"
    pending_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    filename = f"POST_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{title}.md"
    filepath = pending_dir / filename
    
    content = POST_TEMPLATE.format(timestamp=timestamp)
    filepath.write_text(content, encoding='utf-8')
    
    print(f"Created post template: {filepath}")
    return filepath


if __name__ == "__main__":
    import sys
    
    VAULT = "d:/practice/AI_Employee/AI-Employee-Vault"
    
    if len(sys.argv) > 1 and sys.argv[1] == '--create':
        title = sys.argv[2] if len(sys.argv) > 2 else "new_post"
        create_post_template(VAULT, title)
    else:
        print("Starting LinkedIn Poster...")
        print(f"Monitoring: {VAULT}/Approved/linkedin/")
        print("\nTo create a new post template, run:")
        print("  python linkedin_poster.py --create [title]")
        print("")
        
        poster = LinkedInPoster(VAULT)
        poster.run()
