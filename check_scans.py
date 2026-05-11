#!/usr/bin/env python3
import sqlite3
import os

db_file = 'neuropent_local.db'
if os.path.exists(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    print("=== RECENT SCANS ===")
    cursor.execute("SELECT id, status, target_url, created_at FROM scans ORDER BY created_at DESC LIMIT 5")
    scans = cursor.fetchall()
    
    if scans:
        for scan_id, status, target, created in scans:
            print(f"\nScan {scan_id}:")
            print(f"  Status: {status}")
            print(f"  Target: {target}")
            print(f"  Created: {created}")
            
            # Check endpoints
            cursor.execute(f"SELECT COUNT(*) FROM endpoints WHERE scan_id = {scan_id}")
            endpoint_count = cursor.fetchone()[0]
            print(f"  Endpoints: {endpoint_count}")
    else:
        print("No scans found")
    
    conn.close()
else:
    print(f"Database file not found: {db_file}")
