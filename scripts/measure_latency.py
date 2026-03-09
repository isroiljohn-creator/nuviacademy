
import time
import requests
import os
from backend.database import get_sync_db
from backend.models import User
from sqlalchemy import text

def measure_db_read():
    start = time.time()
    with get_sync_db() as session:
        # Simulate simple user lookup (Most common op)
        # Scan for a user (limit 1)
        session.query(User).filter(User.telegram_id == 123456789).first()
    return (time.time() - start) * 1000

def measure_db_write():
    start = time.time()
    with get_sync_db() as session:
        # Create dummy user
        try:
            session.execute(text("CREATE TEMP TABLE IF NOT EXISTS temp_perf_test (id serial);"))
            session.execute(text("INSERT INTO temp_perf_test DEFAULT VALUES;"))
            session.commit()
        except Exception as e:
            print(f"Write test error: {e}")
            session.rollback()
    return (time.time() - start) * 1000

def measure_network_telegram():
    start = time.time()
    try:
        requests.get("https://api.telegram.org", timeout=5)
    except Exception as e:
        print(f"Network error: {e}")
        return 9999
    return (time.time() - start) * 1000

def run_tests():
    print("🚀 Boshlanyapti... Latency Test")
    
    # Warup
    measure_db_read()
    
    # DB Read
    db_read_times = [measure_db_read() for _ in range(5)]
    avg_db_read = sum(db_read_times) / len(db_read_times)
    print(f"📊 DB Read (User Lookup): {avg_db_read:.2f} ms")
    
    # DB Write
    db_write_times = [measure_db_write() for _ in range(3)]
    avg_db_write = sum(db_write_times) / len(db_write_times)
    print(f"📝 DB Write (Commit): {avg_db_write:.2f} ms")
    
    # Network
    net_times = [measure_network_telegram() for _ in range(3)]
    avg_net = sum(net_times) / len(net_times)
    print(f"🌐 Telegram API Latency: {avg_net:.2f} ms")
    
    if avg_net > 500:
        print("\n⚠️  XULOSA: Tarmoq (Internet) juda sekin. Bot Telegramga ulanishda qiynalyapti.")
    elif avg_db_read > 100:
        print("\n⚠️  XULOSA: Baza sekin. Indexlash kerak.")
    else:
        print("\n✅ XULOSA: Tizim tez ishlayapti.")

if __name__ == "__main__":
    run_tests()
