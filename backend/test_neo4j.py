import os
import asyncio
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv

# Load the .env file!
load_dotenv()

# Read from your environment or use defaults
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "Raksh@123")

async def test_connection():
    print(f"Attempting to connect to Neo4j at {uri} with user '{user}'...")
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        await driver.verify_connectivity()
        print("\n✅ SUCCESS: Successfully connected to Neo4j!")
        await driver.close()
    except Exception as e:
        print("\n❌ FAILED to connect to Neo4j.")
        print("Error details:")
        print(str(e))
        
        print("\n--- Troubleshooting Checklist ---")
        if "AuthError" in str(e) or "authentication failure" in str(e).lower():
            print("1. Authentication Failed: The password in your .env file is wrong.")
            print("   -> Did you change the default password when you installed Neo4j?")
            print("   -> Update the NEO4J_PASSWORD line in your .env file.")
        elif "ServiceUnavailable" in str(e) or "Cannot connect" in str(e):
            print("1. Database Not Started: Neo4j is not running.")
            print("   -> Open Neo4j Desktop, hover over your database, and click 'Start'.")
            print("2. Wrong Port: Is it running on a port other than 7687?")
        else:
            print("1. Make sure Neo4j Desktop is open and the database is active.")

if __name__ == "__main__":
    asyncio.run(test_connection())
