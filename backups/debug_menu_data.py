from core.db import db
from backend.database import get_sync_db
import json

def debug_menu():
    with get_sync_db() as conn:
        from core.db import UserMenuLink, MenuTemplate
        # Get first link
        link = conn.query(UserMenuLink).first()
        if not link:
            print("❌ No UserMenuLink found.")
            return
            
        print(f"✅ Found Link for User {link.user_id}")
        print(f"Current Day Index in DB: {link.current_day_index}")
        
        template = conn.query(MenuTemplate).filter(MenuTemplate.id == link.menu_template_id).first()
        if not template:
            print("❌ No Template found for link.")
            return
            
        menu_list = json.loads(template.menu_json)
        print(f"✅ Menu JSON Loaded. Total Days: {len(menu_list)}")
        
        if len(menu_list) > 0:
            print("Day 1:", menu_list[0].get('day', 'No Day Key'))
        if len(menu_list) > 1:
            print("Day 2:", menu_list[1].get('day', 'No Day Key'))

if __name__ == "__main__":
    debug_menu()
