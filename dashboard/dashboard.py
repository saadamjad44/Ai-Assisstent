from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import time
import subprocess
import shutil
from pathlib import Path
import glob

app = Flask(__name__)

# Configuration
BASE_DIR = Path(__file__).parent.parent
VAULT_PATH = BASE_DIR / "AI-Employee-Vault"
INBOX_DIR = VAULT_PATH / "Inbox"
DONE_DIR = VAULT_PATH / "Done"
LOGS_DIR = VAULT_PATH / "Logs"
PENDING_APPROVAL_DIR = VAULT_PATH / "Pending_Approval"
APPROVED_DIR = VAULT_PATH / "Approved"

# Ensure directories exist
for d in [PENDING_APPROVAL_DIR, APPROVED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        filename = file.filename
        file.save(INBOX_DIR / filename)
        return jsonify({"success": True, "message": f"Task '{filename}' sent to Agent SAZA."}), 200

@app.route('/api/projects')
def get_projects():
    # List folders in Done
    if not DONE_DIR.exists():
        return jsonify([])
    
    projects = [f.name for f in DONE_DIR.iterdir() if f.is_dir()]
    # Sort by modification time (newest first)
    projects.sort(key=lambda x: (DONE_DIR / x).stat().st_mtime, reverse=True)
    return jsonify(projects)

@app.route('/api/logs')
def get_logs():
    # Get latest log file
    list_of_files = glob.glob(str(LOGS_DIR / "*.md"))
    if not list_of_files:
        return jsonify({"log": "No logs found."})
    
    latest_file = max(list_of_files, key=os.path.getctime)
    
    with open(latest_file, 'r') as f:
        # Read last 20 lines
        lines = f.readlines()
        recent_lines = lines[-20:]
        return jsonify({"log": "".join(recent_lines)})

@app.route('/api/status')
def get_status():
    # Check if any python process is running ccr (simple check)
    list_of_files = glob.glob(str(LOGS_DIR / "*.md"))
    status = "Idle"
    if list_of_files:
        latest_file = max(list_of_files, key=os.path.getctime)
        last_mod = os.path.getmtime(latest_file)
        if time.time() - last_mod < 60: # Updated in last minute
            status = "Processing..."
            
    return jsonify({"status": status})

@app.route('/api/stats')
def get_stats():
    # 1. Projects Created Today
    today_count = 0
    now = time.time()
    day_in_seconds = 24 * 3600
    
    if DONE_DIR.exists():
        for f in DONE_DIR.iterdir():
            if f.is_dir():
                if now - f.stat().st_ctime < day_in_seconds:
                    today_count += 1
                    
    # 2. Files In Progress (in Inbox)
    in_progress_count = 0
    if INBOX_DIR.exists():
        # Count .txt and .md files (excluding 'Processed' dir)
        in_progress_count = len([f for f in INBOX_DIR.iterdir() if f.is_file() and f.suffix.lower() in ['.txt', '.md']])
        
    return jsonify({
        "today_projects": today_count,
        "in_progress": in_progress_count
    })

@app.route('/projects/<path:project_name>/<path:filename>')
def serve_project_file(project_name, filename):
    # Serve files from the specific project folder in Done
    project_folder = DONE_DIR / project_name
    return send_from_directory(project_folder, filename)

@app.route('/projects/<path:project_name>/')
def serve_project_index(project_name):
    # Serve index.html by default
    project_folder = DONE_DIR / project_name
    return send_from_directory(project_folder, 'index.html')

@app.route('/api/projects/delete/<path:project_name>', methods=['POST', 'DELETE'])
def delete_project(project_name):
    print(f"[Dashboard] Deletion request received for: {project_name}")
    project_path = DONE_DIR / project_name
    print(f"[Dashboard] Target path: {project_path}")
    
    if not project_path.exists():
        print(f"[Dashboard] Error: Project path does not exist.")
        return jsonify({"error": "Project not found"}), 404
    
    try:
        import shutil
        shutil.rmtree(project_path)
        print(f"[Dashboard] Successfully deleted: {project_name}")
        return jsonify({"success": True, "message": f"Project '{project_name}' deleted."}), 200
    except Exception as e:
        print(f"[Dashboard] Error during deletion: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/watchers')
def get_watchers():
    """Check status of all watcher processes."""
    watchers = {
        "Gmail Watcher": False,
        "LinkedIn Watcher": False,
        "WhatsApp Watcher": False,
        "Inbox Watcher": False,
        "Orchestrator": False
    }
    
    try:
        # Use wmic to get command lines of running python processes
        cmd = 'wmic process where "name=\'python.exe\' or name=\'pythonw.exe\'" get commandline'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        running_cmdlines = result.stdout.lower()
        
        if "gmail_watcher.py" in running_cmdlines: watchers["Gmail Watcher"] = True
        if "linkedin_watcher.py" in running_cmdlines: watchers["LinkedIn Watcher"] = True
        if "whatsapp_watcher.py" in running_cmdlines: watchers["WhatsApp Watcher"] = True
        if "inbox_watcher.py" in running_cmdlines: watchers["Inbox Watcher"] = True
        if "orchestrator.py" in running_cmdlines: watchers["Orchestrator"] = True
        
    except Exception as e:
        print(f"[Dashboard] Error checking watchers: {e}")
        
    return jsonify(watchers)

@app.route('/api/approvals')
def get_approvals():
    """List all pending approvals."""
    if not PENDING_APPROVAL_DIR.exists():
        return jsonify([])
        
    # Find all .md files in Pending_Approval and its subdirectories
    approvals = []
    for f in PENDING_APPROVAL_DIR.rglob("*.md"):
        if f.is_file():
            approvals.append({
                "filename": f.name,
                "path": str(f.relative_to(PENDING_APPROVAL_DIR)).replace("\\", "/"),
                "mtime": f.stat().st_mtime,
                "display_name": f.stem.replace("_", " ").title()
            })
            
    # Sort by newest first
    approvals.sort(key=lambda x: x["mtime"], reverse=True)
    return jsonify(approvals)

@app.route('/api/approvals/content/<path:filepath>')
def get_approval_content(filepath):
    """Get content of a specific approval file."""
    full_path = PENDING_APPROVAL_DIR / filepath
    if not full_path.exists() or not full_path.is_file():
        return jsonify({"error": "File not found"}), 404
        
    try:
        content = full_path.read_text(encoding='utf-8')
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/approvals/process', methods=['POST'])
def process_approval():
    """Approve or reject a task."""
    data = request.json
    filepath = data.get('path')
    action = data.get('action') # 'approve' or 'reject'
    
    source_path = PENDING_APPROVAL_DIR / filepath
    if not source_path.exists():
        return jsonify({"error": "File not found"}), 404
        
    try:
        if action == 'approve':
            # Create subdirectories if they exist in source path
            target_path = APPROVED_DIR / filepath
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(target_path))
            return jsonify({"success": True, "message": "Task approved and moved to execution queue."})
        elif action == 'reject':
            # Move to a subfolder in Done or just mark as rejected
            rejected_dir = DONE_DIR / "Rejected"
            rejected_dir.mkdir(parents=True, exist_ok=True)
            target_path = rejected_dir / source_path.name
            shutil.move(str(source_path), str(target_path))
            return jsonify({"success": True, "message": "Task rejected and archived."})
        else:
            return jsonify({"error": "Invalid action"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting SAZA Dashboard on http://localhost:5000")
    app.run(debug=True, port=5000)
