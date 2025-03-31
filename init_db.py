from app import app, db
import os

# Remove the database file if it exists
if os.path.exists('database.db'):
    os.remove('database.db')

with app.app_context():
    # Drop all tables first
    db.drop_all()
    # Create all tables
    db.create_all()
    print("Database initialized successfully!") 