import sqlite3
import os

def run_migrations(db_path="nutrigen.db"):
    if not os.path.exists(db_path) and os.path.exists("app/nutrigen.db"):
        db_path = "app/nutrigen.db"
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add budget to custom_grocery_lists if missing
        try:
            cursor.execute("ALTER TABLE custom_grocery_lists ADD COLUMN budget VARCHAR DEFAULT 'Medium'")
        except sqlite3.OperationalError:
            pass

        # Add weight, height, meal_preferences to members table if missing
        for col in [("weight", "VARCHAR"), ("height", "VARCHAR"), ("meal_preferences", "VARCHAR")]:
            try:
                cursor.execute(f"ALTER TABLE members ADD COLUMN {col[0]} {col[1]}")
                print(f"[MIGRATION] Added {col[0]} column to members table.")
            except sqlite3.OperationalError:
                pass
                
        conn.commit()
        print("[MIGRATION] Migrations completed successfully.")
    except Exception as e:
        print("[MIGRATION ERROR]:", e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migrations()

