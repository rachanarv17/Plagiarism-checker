import sqlite3
import os

db_paths = ['instance/users.db', 'users.db']

for db_path in db_paths:
    if not os.path.exists(db_path):
        continue
        
    print(f"Checking {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            print(f"Table 'user' not found in {db_path}")
            continue

        # Check if column exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'profile_pic' not in columns:
            print(f"Adding profile_pic column to {db_path}...")
            cursor.execute("ALTER TABLE user ADD COLUMN profile_pic VARCHAR(255)")
            conn.commit()
            print("Column added successfully.")
        else:
            print(f"profile_pic column already exists in {db_path}.")

    except Exception as e:
        print(f"Migration error in {db_path}: {e}")
    finally:
        conn.close()
