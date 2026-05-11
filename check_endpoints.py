#!/usr/bin/env python3
"""Check endpoints in the database for scan 97"""
import sqlite3
import sys
import os

# Try SQLite first
db_files = [
    'neuropent_local.db',
    'd:\\RakshAI\\rakshaidb_local.db',
]

for db_file in db_files:
    if os.path.exists(db_file):
        print(f"Using database: {db_file}")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get scan 97
        cursor.execute("SELECT id, scan_id, status FROM scans WHERE scan_id LIKE '%97' LIMIT 1")
        scan = cursor.fetchone()
        if scan:
            scan_id_db = scan[0]
            print(f"\nFound scan in DB: ID={scan_id_db}, scan_id={scan[1]}, status={scan[2]}")
            
            # Check endpoints for this scan
            cursor.execute(f"SELECT COUNT(*), GROUP_CONCAT(url, '\n') FROM endpoints WHERE scan_id = {scan_id_db}")
            result = cursor.fetchone()
            endpoint_count = result[0]
            urls = result[1]
            
            print(f"\nEndpoints count: {endpoint_count}")
            if urls:
                print("Endpoints:")
                for url in urls.split('\n')[:10]:
                    print(f"  - {url}")
        else:
            print("Scan not found")
        
        conn.close()
        sys.exit(0)

print("Database not found")
