from datetime import datetime, timedelta, timezone
import sys

UZ_TZ = timezone(timedelta(hours=5))

def test_tz():
    now_utc = datetime.now(timezone.utc)
    now_uz = datetime.now(UZ_TZ)
    
    print(f"UTC Time: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"UZ Time:  {now_uz.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test current_time string for reminders
    current_time = now_uz.strftime("%H:%M")
    print(f"Reminder Format (UZ): {current_time}")
    
    if now_uz.hour - now_utc.hour not in [5, -19]: # handling day wrap
        print("ERROR: Timezone offset is not 5 hours!")
    else:
        print("SUCCESS: Timezone offset is correct (+5).")

if __name__ == "__main__":
    test_tz()
