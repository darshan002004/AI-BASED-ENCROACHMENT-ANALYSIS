import asyncio
from app.database import db_manager

async def main():
    await db_manager.connect()
    print("==================================================")
    print(f"DATABASE INSPECTION (Mode: {db_manager.mode})")
    print("==================================================")
    cols = [
        "users", "incidents", "audit_logs", 
        "ai_feedback_dataset", "service_feedback", 
        "model_evaluations", "notifications", "sla_rules"
    ]
    for c in cols:
        col = db_manager.get_collection(c)
        count = await col.count_documents({})
        print(f"Collection '{c}': {count} documents")

    print("\n--- User Accounts ---")
    users = await db_manager["users"].find({}).to_list(100)
    for u in users:
        print(f"  {u.get('email')} [{u.get('role')}]: {u.get('full_name')} (ID: {u.get('id')})")

    print("\n--- Recent Incidents (first 5) ---")
    incidents = await db_manager["incidents"].find({}).limit(5).to_list(5)
    for inc in incidents:
        print(f"  {inc.get('incident_number')} | {inc.get('title')} | Status: {inc.get('status')} | Reporter: {inc.get('reporter_id')}")

    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
