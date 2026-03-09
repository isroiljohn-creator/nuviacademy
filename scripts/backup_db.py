
import os
import subprocess
import datetime
import sys
from glob import glob

# Ensure backup directory exists
BACKUP_DIR = "backups"
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def create_backup():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return False

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(BACKUP_DIR, f"yasha_pg_backup_{timestamp}.dump")
    
    print(f"🔄 Starting backup: {backup_file}")
    
    try:
        # Run pg_dump
        # Note: pg_dump must be installed in the environment
        env = os.environ.copy()
        
        # PGPASSWORD needs to be extracted or passed differently if DB_URL is complex
        # But generic pg_dump accepts connection string as argument in newer versions?
        # or just pass db_url as the dbname argument
        
        cmd = ["pg_dump", db_url, "-F", "c", "-f", backup_file]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Backup successful: {backup_file}")
            
            # Retention Policy (14 days)
            cleanup_old_backups()
            return True
        else:
            print(f"❌ Backup failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Backup error: {e}")
        return False

def cleanup_old_backups(days=14):
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    for f in glob(os.path.join(BACKUP_DIR, "*.dump")):
        ctime = datetime.datetime.fromtimestamp(os.path.getctime(f))
        if ctime < cutoff:
            print(f"🗑️ Deleting old backup: {f}")
            os.remove(f)

if __name__ == "__main__":
    create_backup()
