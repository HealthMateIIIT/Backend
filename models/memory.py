from datetime import datetime, timedelta
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client['healthmate']
memories_collection = db['user_memories']

class UserMemory:
    def __init__(self, user_id):
        self.user_id = user_id
        self._ensure_memory_exists()
    
    def _ensure_memory_exists(self):
        """Ensure a memory document exists for the user"""
        if not memories_collection.find_one({"user_id": self.user_id}):
            memories_collection.insert_one({
                "user_id": self.user_id,
                "long_term": {},
                "recent": [],
                "updated_at": datetime.utcnow()
            })
    
    def get_memory(self):
        """Retrieve both long-term and recent memories"""
        memory = memories_collection.find_one({"user_id": self.user_id})
        if not memory:
            return {"long_term": {}, "recent": []}
        
        # Clean up old recent memories (older than 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_memories = [m for m in memory.get('recent', []) 
                          if m.get('timestamp', datetime.utcnow()) > thirty_days_ago]
        
        # Update if we removed old memories
        if len(recent_memories) != len(memory.get('recent', [])):
            self._update_memory({"recent": recent_memories})
        
        return {
            "long_term": memory.get('long_term', {}),
            "recent": recent_memories
        }
    
    def update_long_term(self, updates):
        """Update long-term memory with new information"""
        if not isinstance(updates, dict):
            raise ValueError("Updates must be a dictionary")
            
        return memories_collection.update_one(
            {"user_id": self.user_id},
            {
                "$set": {
                    f"long_term.{k}": v for k, v in updates.items()
                },
                "$currentDate": {"updated_at": True}
            },
            upsert=True
        )
    
    def add_recent_memory(self, memory_text, memory_type="general"):
        """Add a new recent memory"""
        memory_entry = {
            "text": memory_text,
            "type": memory_type,
            "timestamp": datetime.utcnow()
        }
        
        return memories_collection.update_one(
            {"user_id": self.user_id},
            {
                "$push": {
                    "recent": {
                        "$each": [memory_entry],
                        "$position": 0,
                        "$slice": 50  # Keep only the 50 most recent memories
                    }
                },
                "$currentDate": {"updated_at": True}
            },
            upsert=True
        )
    
    def _update_memory(self, updates):
        """Internal method to update memory document"""
        return memories_collection.update_one(
            {"user_id": self.user_id},
            {
                "$set": updates,
                "$currentDate": {"updated_at": True}
            },
            upsert=True
        )
