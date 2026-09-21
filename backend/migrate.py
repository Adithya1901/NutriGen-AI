import sqlite3

try:
    conn = sqlite3.connect("nutrigen.db")
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE custom_grocery_lists ADD COLUMN budget VARCHAR DEFAULT 'Medium'")
    conn.commit()
    print("MIGRATION SUCCESS: Added budget column to custom_grocery_lists table.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
        print("MIGRATION INFO: Column already exists.")
    else:
        print("MIGRATION ERROR:", e)
finally:
    if conn:
        conn.close()
