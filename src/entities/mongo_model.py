from pymongo import MongoClient
from src.constants.properties import MONGODB_URL

client = MongoClient(MONGODB_URL)
db = client.taskingo_db

# Collections
notes_collection = db["notes"]
ai_insights_collection = db["ai_insights"]

def init_mongo_indexes():
    notes_collection.create_index("goal_id")
    ai_insights_collection.create_index("goal_id")

    return "MongoDB indexes created successfully"

init_mongo_indexes()