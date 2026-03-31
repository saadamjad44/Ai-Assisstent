"""
Approved Watcher - Monitors /Approved for tasks and triggers AI response generation.
Part of the SAZA AI Employee automated workflow.
"""

import os
import time
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Configuration (Relative to script location)
BASE_DIR = Path(__file__).parent.parent
VAULT_PATH = BASE_DIR / "AI-Employee-Vault"
APPROVED_DIR = VAULT_PATH / "Approved"
WA_READY_DIR = APPROVED_DIR / "whatsapp"
CCR_SCRIPT = Path(__file__).parent / "ccr.bat"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ApprovedWatcher')

def log_to_vault(message, level="INFO"):
    """Log to the central SAZA logs."""
    timestamp = datetime.now()
    log_dir = VAULT_PATH / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"approved_watcher_{timestamp.strftime('%Y-%m')}.md"
    
    log_entry = f"- **{timestamp.strftime('%Y-%m-%d %H:%M:%S')}** [{level}]: {message}\n"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    if level == "ERROR":
        logger.error(message)
    else:
        logger.info(message)

def process_file(action_file: Path):
    """Analyze file and trigger Claude if needed."""
    try:
        content = action_file.read_text(encoding='utf-8')
        
        # We only handle WhatsApp for now as requested
        if 'type: whatsapp' in content:
            log_to_vault(f"Processing WhatsApp approval: {action_file.name}")
            
            # Check if it needs AI generation (placeholder exists)
            if "[Type your reply here" in content or "Agent Response" not in content:
                log_to_vault(f"Triggering Claude AI for: {action_file.name}")
                
                # Build skill-aware prompt
                skill_file = BASE_DIR / "skills" / "whatsapp_mimicry" / "SKILL.md"
                skill_instructions = ""
                if skill_file.exists():
                    skill_instructions = skill_file.read_text(encoding='utf-8')
                
                prompt = (
                    f"You are the 'Communicator (WhatsApp Agent)' from AGENTS.md. "
                    f"Your task is to write a reply for the WhatsApp message in '{action_file}'. "
                    f"\n\nCRITICAL RULES (read these FIRST before writing):\n"
                    f"1. First read the skill file at '{skill_file}' for detailed reply guidelines.\n"
                    f"2. MATCH THE LANGUAGE: If the message is in Roman Urdu, reply in Roman Urdu. "
                    f"If in English, reply in English. If in Urdu, reply in Urdu. NEVER switch languages.\n"
                    f"3. KEEP IT SHORT: Maximum 1-2 short sentences. WhatsApp is for quick chats, NOT essays.\n"
                    f"4. SOUND HUMAN: Never say 'I am an AI', 'How can I assist you', or use formal closings. "
                    f"Write like a real friend chatting on WhatsApp.\n"
                    f"5. Read the '**Content:**' section for the incoming message.\n"
                    f"6. Write your reply in the '## Agent Response' section (REPLACE the placeholder text).\n"
                    f"7. Keep the markdown format exactly as it is. DO NOT change anything else in the file.\n"
                    f"\nHere are the mimicry skill rules:\n{skill_instructions}\n"
                    f"DO NOT add any conversational fluff, ONLY update the file."
                )
                
                # Align with Inbox Watcher visibility
                print("="*60)
                print("TRIGGERING CLAUDE AI FOR APPROVED TASK")
                print(f"File: {action_file.name}")
                print("="*60)

                # Call CCR - Pass only the prompt since ccr.bat already adds -p
                command = f'"{CCR_SCRIPT}" "{prompt}"'
                print(f"[Watcher] Executing: {command}")
                subprocess.run(command, shell=True, check=False)
                
                # VERIFICATION: Read back and check if placeholder is still there
                updated_content = action_file.read_text(encoding='utf-8')
                if "[Type your reply here" in updated_content:
                    log_to_vault(f"AI generation FAILED for {action_file.name}: Placeholder still exists.", "ERROR")
                    print("[Error] Claude did not update the file. Keeping in Approved for retry.")
                    return False
                
                log_to_vault(f"AI generated response successfully for {action_file.name}")
            
            # Move to WhatsApp Outbox ONLY if placeholder is gone
            WA_READY_DIR.mkdir(parents=True, exist_ok=True)
            target_path = WA_READY_DIR / action_file.name
            
            # Handle collision
            if target_path.exists():
                target_path = WA_READY_DIR / f"{int(time.time())}_{action_file.name}"
            
            shutil.move(str(action_file), str(target_path))
            log_to_vault(f"Handoff complete: {target_path.name} moved to delivery queue.")
            return True
            
        return False
    except Exception as e:
        log_to_vault(f"Error processing {action_file.name}: {e}", "ERROR")
        return False

def run_watcher():
    """Main loop."""
    logger.info("=" * 50)
    logger.info("SAZA Approved Watcher Started")
    logger.info(f"Watching: {APPROVED_DIR}")
    logger.info("=" * 50)
    
    # Ensure folder exists
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            # Look for markdown files in Approved (not in subfolders)
            for f in APPROVED_DIR.glob('*.md'):
                if f.is_file():
                    process_file(f)
            
            time.sleep(5) # Frequent check for responsiveness
        except KeyboardInterrupt:
            logger.info("Stopping watcher...")
            break
        except Exception as e:
            logger.error(f"Watcher loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_watcher()
