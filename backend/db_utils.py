#!/usr/bin/env python3
"""
Database Utilities Script for Meeting Analyzer

This script provides utilities for database maintenance:
- Backup the database
- Clean orphaned files (files without database records)
- Database status/health check
"""

import os
import sys
import shutil
import sqlite3
import datetime
import argparse
from pathlib import Path

# Add the current directory to the path to import app modules
sys.path.append(os.getcwd())

# Import settings after path setup
from app.core.config import settings

def check_database():
    """Check database status and print information"""
    db_path = os.path.join(settings.DATA_DIR, "meetings.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get meeting count
        cursor.execute("SELECT COUNT(*) FROM meetings")
        meeting_count = cursor.fetchone()[0]
        
        # Get PDF count
        cursor.execute("SELECT COUNT(*) FROM pdfs")
        pdf_count = cursor.fetchone()[0]
        
        # Get database file size
        db_size = os.path.getsize(db_path) / (1024 * 1024)  # Size in MB
        
        print(f"Database Status:")
        print(f"  - Location: {db_path}")
        print(f"  - Size: {db_size:.2f} MB")
        print(f"  - Meetings: {meeting_count}")
        print(f"  - PDF records: {pdf_count}")
        
        # Check for database integrity
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        print(f"  - Integrity check: {integrity}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return False

def backup_database():
    """Create a backup of the database"""
    db_path = os.path.join(settings.DATA_DIR, "meetings.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return False
    
    try:
        # Create backup with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(settings.DATA_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_path = os.path.join(backup_dir, f"meetings_{timestamp}.db")
        shutil.copy2(db_path, backup_path)
        
        print(f"Database backed up to: {backup_path}")
        return True
        
    except Exception as e:
        print(f"Error backing up database: {e}")
        return False

def clean_orphaned_files():
    """Find and clean orphaned files that don't have database records"""
    db_path = os.path.join(settings.DATA_DIR, "meetings.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all audio paths from the database
        cursor.execute("SELECT audio_path FROM meetings")
        db_audio_paths = [row[0] for row in cursor.fetchall() if row[0]]
        
        # Get all PDF paths from the database
        cursor.execute("SELECT file_path FROM pdfs")
        db_pdf_paths = [row[0] for row in cursor.fetchall() if row[0]]
        
        # Check uploads directory
        upload_files = []
        for file in os.listdir(settings.UPLOAD_DIR):
            file_path = os.path.join(settings.UPLOAD_DIR, file)
            if os.path.isfile(file_path) and file_path not in db_audio_paths:
                upload_files.append(file_path)
        
        # Check PDFs directory
        pdf_files = []
        for file in os.listdir(settings.PDF_DIR):
            file_path = os.path.join(settings.PDF_DIR, file)
            if os.path.isfile(file_path) and file_path not in db_pdf_paths:
                pdf_files.append(file_path)
        
        # Print results
        print(f"Found {len(upload_files)} orphaned upload files")
        print(f"Found {len(pdf_files)} orphaned PDF files")
        
        if not upload_files and not pdf_files:
            print("No orphaned files to clean up")
            return True
        
        # Ask for confirmation
        if input("Do you want to delete these orphaned files? (y/n): ").lower() != 'y':
            print("Cleanup aborted")
            return False
        
        # Delete orphaned files
        deleted_count = 0
        for file_path in upload_files + pdf_files:
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
        
        print(f"Deleted {deleted_count} orphaned files")
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error cleaning orphaned files: {e}")
        return False

def main():
    """Main function to parse arguments and execute commands"""
    parser = argparse.ArgumentParser(description='Database maintenance utilities')
    parser.add_argument('--check', action='store_true', help='Check database status')
    parser.add_argument('--backup', action='store_true', help='Create a database backup')
    parser.add_argument('--clean', action='store_true', help='Clean orphaned files')
    
    args = parser.parse_args()
    
    # If no arguments given, show help
    if not (args.check or args.backup or args.clean):
        parser.print_help()
        return
    
    # Create data directory if it doesn't exist
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    
    if args.check:
        check_database()
    
    if args.backup:
        backup_database()
    
    if args.clean:
        clean_orphaned_files()

if __name__ == "__main__":
    main()
