import os
import shutil
import datetime
from core.db import db
from core.config import DATABASE_URL

def create_backup():
    # 1. Setup Directory
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    reports = []

    # 2. Database File Backup (SQLite only)
    if "sqlite" in DATABASE_URL or not DATABASE_URL:
        db_file = "fitness_bot.db"
        if os.path.exists(db_file):
            backup_db_name = f"fitness_bot_{timestamp}.db"
            backup_db_path = os.path.join(backup_dir, backup_db_name)
            shutil.copy2(db_file, backup_db_path)
            reports.append(f"✅ Database: {backup_db_path}")
        else:
            reports.append(f"⚠️ Database file not found: {db_file}")

    # 3. CSV Export
    try:
        csv_data = db.export_csv()
        if csv_data:
            csv_name = f"users_{timestamp}.csv"
            csv_path = os.path.join(backup_dir, csv_name)
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write(csv_data)
            reports.append(f"✅ Users CSV: {csv_path}")
        else:
             reports.append("⚠️ CSV Export returned empty.")
    except Exception as e:
        reports.append(f"❌ CSV Export Failed: {e}")

    # 4. Report
    print("\n".join(reports))

if __name__ == "__main__":
    create_backup()
