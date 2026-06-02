import os
import asyncio
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Read target password from .env
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
target_password = os.getenv("NEO4J_PASSWORD", "Raksh@123")

# Common default passwords to try
PASSWORDS_TO_TRY = [
    "neo4j",                 # Default
    "password",              # Common
    "RakshAI123",            # In config.py
    "neuropent_graph_pass",  # In diagnostics hint
    "root",
    "admin"
]

async def fix_neo4j():
    print(f"--- Neo4j Password Auto-Fix ---")
    print(f"Target Password (from .env): {target_password}")
    
    # 1. Check if already connected
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=(user, target_password))
        await driver.verify_connectivity()
        print(f"✅ Neo4j is already working with the password in your .env!")
        await driver.close()
        return
    except Exception:
        print(f"❌ Current .env password failed. Trying defaults...")

    # 2. Try common passwords and update if one works
    for pwd in PASSWORDS_TO_TRY:
        print(f"Attempting login with: '{pwd}'...")
        try:
            driver = AsyncGraphDatabase.driver(uri, auth=(user, pwd))
            await driver.verify_connectivity()
            
            print(f"🎉 SUCCESS! Logged in with password: '{pwd}'")
            print(f"Changing password to match your .env: '{target_password}'...")
            
            async with driver.session() as session:
                # Command to change password
                await session.run(f"ALTER CURRENT USER SET PASSWORD FROM '{pwd}' TO '{target_password}'")
                
            print(f"✅ Password successfully updated!")
            await driver.close()
            
            # Verify new password
            print(f"Verifying new password...")
            driver = AsyncGraphDatabase.driver(uri, auth=(user, target_password))
            await driver.verify_connectivity()
            print(f"✅ Verified! Neo4j is now fully configured.")
            await driver.close()
            return
            
        except Exception as e:
            if "ServiceUnavailable" in str(e):
                print(f"❌ Neo4j service is not running at {uri}. Please start Neo4j Desktop.")
                return
            continue

    print("\n--- Manual Fix Required ---")
    print(f"None of the common passwords worked.")
    print(f"1. Open Neo4j Browser (http://localhost:7474)")
    print(f"2. Log in with your password.")
    print(f"3. Run this command to sync with the application:")
    print(f"   ALTER CURRENT USER SET PASSWORD FROM 'your_current_pass' TO '{target_password}'")

if __name__ == "__main__":
    asyncio.run(fix_neo4j())
