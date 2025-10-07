"""
Миграция базы данных для добавления поддержки комментариев
"""
import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Add parent_id and is_comment columns to reviews table"""
    
    db_path = 'instance/reviews.db'
    
    if not os.path.exists(db_path):
        logger.warning(f"Database not found at {db_path}. Creating new database with updated schema.")
        logger.info("Please run your application to initialize the database with the new schema.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(reviews)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add parent_id column if it doesn't exist
        if 'parent_id' not in columns:
            logger.info("Adding parent_id column...")
            cursor.execute("ALTER TABLE reviews ADD COLUMN parent_id INTEGER")
            logger.info("✓ parent_id column added")
        else:
            logger.info("parent_id column already exists")
        
        # Add is_comment column if it doesn't exist
        if 'is_comment' not in columns:
            logger.info("Adding is_comment column...")
            cursor.execute("ALTER TABLE reviews ADD COLUMN is_comment BOOLEAN DEFAULT 0")
            logger.info("✓ is_comment column added")
        else:
            logger.info("is_comment column already exists")
        
        # Commit changes
        conn.commit()
        
        logger.info("=" * 60)
        logger.info("Database migration completed successfully!")
        logger.info("=" * 60)
        logger.info("New features:")
        logger.info("- Comments can now be linked to parent articles")
        logger.info("- Use collect_with_comments() in collectors to parse comments")
        logger.info("- Set collect_comments=True in Telegram and Zen collectors")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    migrate_database()
