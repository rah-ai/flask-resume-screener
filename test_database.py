import sqlite3
import os

def test_database():
    print("🧪 Testing database setup...")
    
    # Ensure directory exists
    os.makedirs('database', exist_ok=True)
    
    # Remove any existing database file
    db_path = os.path.join('database', 'candidates.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ Removed old database file")
    
    try:
        # Create new database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test table creation
        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        ''')
        
        # Test insert
        cursor.execute("INSERT INTO test_table (name) VALUES ('test')")
        
        # Test select
        cursor.execute("SELECT * FROM test_table")
        result = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        print("✅ Database test successful!")
        print(f"✅ Database created at: {db_path}")
        print(f"✅ Test result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_database()
    if success:
        print("\n🎉 Database is working! You can now run: python app.py")
    else:
        print("\n❌ Database setup failed. Check the error above.")