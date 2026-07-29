from datetime import datetime, timedelta, timezone

def get_current_ist_week():
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    start_of_week = now - timedelta(days=now.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d")
