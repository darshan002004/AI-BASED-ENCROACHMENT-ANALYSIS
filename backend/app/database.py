import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

logger = logging.getLogger("encrowatch.database")

# In-memory / JSON-backed MongoDB-compatible fallback store
class LocalCollection:
    def __init__(self, name: str, data_dir: str):
        self.name = name
        self.filepath = os.path.join(data_dir, f"{name}.json")
        self._lock = asyncio.Lock()
        self._cache: List[Dict[str, Any]] = []
        self._loaded = False

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def _load(self):
        if not self._loaded:
            self._ensure_dir()
            if os.path.exists(self.filepath):
                try:
                    with open(self.filepath, "r", encoding="utf-8") as f:
                        self._cache = json.load(f)
                except Exception as e:
                    logger.warning(f"Error loading {self.filepath}: {e}")
                    self._cache = []
            else:
                self._cache = []
            self._loaded = True

    def _save(self):
        self._ensure_dir()
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, default=str, indent=2)

    def _matches_filter(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        if not query:
            return True
        for k, v in query.items():
            if k == "$or" and isinstance(v, list):
                if not any(self._matches_filter(doc, sub_q) for sub_q in v):
                    return False
                continue
            if k == "$and" and isinstance(v, list):
                if not all(self._matches_filter(doc, sub_q) for sub_q in v):
                    return False
                continue

            val = doc.get(k)
            if isinstance(v, dict):
                # Operator checks
                if "$in" in v and val not in v["$in"]:
                    return False
                if "$nin" in v and val in v["$nin"]:
                    return False
                if "$ne" in v and val == v["$ne"]:
                    return False
                if "$gt" in v and not (val is not None and val > v["$gt"]):
                    return False
                if "$gte" in v and not (val is not None and val >= v["$gte"]):
                    return False
                if "$lt" in v and not (val is not None and val < v["$lt"]):
                    return False
                if "$lte" in v and not (val is not None and val <= v["$lte"]):
                    return False
                if "$regex" in v:
                    import re
                    pattern = v["$regex"]
                    options = v.get("$options", "")
                    flags = re.IGNORECASE if "i" in options else 0
                    if not (isinstance(val, str) and re.search(pattern, val, flags)):
                        return False
            else:
                if val != v:
                    return False
        return True

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with self._lock:
            self._load()
            for doc in self._cache:
                if self._matches_filter(doc, query):
                    return dict(doc)
            return None

    def find(self, query: Optional[Dict[str, Any]] = None):
        return LocalCursor(self, query or {})

    async def insert_one(self, doc: Dict[str, Any]):
        async with self._lock:
            self._load()
            new_doc = dict(doc)
            if "_id" not in new_doc:
                new_doc["_id"] = str(datetime.utcnow().timestamp())
            self._cache.append(new_doc)
            self._save()
            class InsertResult:
                inserted_id = new_doc["_id"]
            return InsertResult()

    async def insert_many(self, docs: List[Dict[str, Any]]):
        async with self._lock:
            self._load()
            inserted_ids = []
            for doc in docs:
                new_doc = dict(doc)
                if "_id" not in new_doc:
                    new_doc["_id"] = str(datetime.utcnow().timestamp()) + str(len(inserted_ids))
                self._cache.append(new_doc)
                inserted_ids.append(new_doc["_id"])
            self._save()
            class InsertManyResult:
                inserted_ids = inserted_ids
            return InsertManyResult()

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]):
        async with self._lock:
            self._load()
            matched = False
            for idx, doc in enumerate(self._cache):
                if self._matches_filter(doc, query):
                    if "$set" in update:
                        for k, v in update["$set"].items():
                            doc[k] = v
                    if "$inc" in update:
                        for k, v in update["$inc"].items():
                            doc[k] = doc.get(k, 0) + v
                    if "$push" in update:
                        for k, v in update["$push"].items():
                            if k not in doc or not isinstance(doc[k], list):
                                doc[k] = []
                            if isinstance(v, dict) and "$each" in v:
                                doc[k].extend(v["$each"])
                            else:
                                doc[k].append(v)
                    if "$addToSet" in update:
                        for k, v in update["$addToSet"].items():
                            if k not in doc or not isinstance(doc[k], list):
                                doc[k] = []
                            if isinstance(v, dict) and "$each" in v:
                                for item in v["$each"]:
                                    if item not in doc[k]:
                                        doc[k].append(item)
                            else:
                                if v not in doc[k]:
                                    doc[k].append(v)
                    self._cache[idx] = doc
                    matched = True
                    break
            if matched:
                self._save()
            class UpdateResult:
                matched_count = 1 if matched else 0
                modified_count = 1 if matched else 0
            return UpdateResult()

    async def update_many(self, query: Dict[str, Any], update: Dict[str, Any]):
        async with self._lock:
            self._load()
            matched_count = 0
            for idx, doc in enumerate(self._cache):
                if self._matches_filter(doc, query):
                    matched_count += 1
                    if "$set" in update:
                        for k, v in update["$set"].items():
                            doc[k] = v
                    if "$inc" in update:
                        for k, v in update["$inc"].items():
                            doc[k] = doc.get(k, 0) + v
                    if "$push" in update:
                        for k, v in update["$push"].items():
                            if k not in doc or not isinstance(doc[k], list):
                                doc[k] = []
                            if isinstance(v, dict) and "$each" in v:
                                doc[k].extend(v["$each"])
                            else:
                                doc[k].append(v)
                    if "$addToSet" in update:
                        for k, v in update["$addToSet"].items():
                            if k not in doc or not isinstance(doc[k], list):
                                doc[k] = []
                            if isinstance(v, dict) and "$each" in v:
                                for item in v["$each"]:
                                    if item not in doc[k]:
                                        doc[k].append(item)
                            else:
                                if v not in doc[k]:
                                    doc[k].append(v)
                    self._cache[idx] = doc
            if matched_count > 0:
                self._save()
            from types import SimpleNamespace
            return SimpleNamespace(matched_count=matched_count, modified_count=matched_count)

    async def delete_one(self, query: Dict[str, Any]):
        async with self._lock:
            self._load()
            deleted = False
            for idx, doc in enumerate(self._cache):
                if self._matches_filter(doc, query):
                    del self._cache[idx]
                    deleted = True
                    break
            if deleted:
                self._save()
            class DeleteResult:
                deleted_count = 1 if deleted else 0
            return DeleteResult()

    async def count_documents(self, query: Dict[str, Any]) -> int:
        async with self._lock:
            self._load()
            return sum(1 for doc in self._cache if self._matches_filter(doc, query))


class LocalCursor:
    def __init__(self, collection: LocalCollection, query: Dict[str, Any]):
        self.collection = collection
        self.query = query
        self._sort_key = None
        self._sort_dir = 1
        self._skip = 0
        self._limit = None

    def sort(self, key_or_list, direction=1):
        if isinstance(key_or_list, list):
            self._sort_key, self._sort_dir = key_or_list[0]
        else:
            self._sort_key = key_or_list
            self._sort_dir = direction
        return self

    def skip(self, n: int):
        self._skip = n
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        async with self.collection._lock:
            self.collection._load()
            results = [dict(doc) for doc in self.collection._cache if self.collection._matches_filter(doc, self.query)]
            
            if self._sort_key:
                def safe_sort_val(x):
                    val = x.get(self._sort_key)
                    return "" if val is None else str(val)
                results.sort(key=safe_sort_val, reverse=(self._sort_dir == -1))

            if self._skip:
                results = results[self._skip:]
            limit_val = length if length is not None else self._limit
            if limit_val is not None:
                results = results[:limit_val]
            return results

    def __aiter__(self):
        self._iter_data = None
        self._iter_idx = 0
        return self

    async def __anext__(self):
        if self._iter_data is None:
            self._iter_data = await self.to_list()
        if self._iter_idx < len(self._iter_data):
            doc = self._iter_data[self._iter_idx]
            self._iter_idx += 1
            return doc
        raise StopAsyncIteration


class DatabaseManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Any = None
        self.is_connected: bool = False
        self.mode: str = "disconnected"
        self._fallback_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        self._collections: Dict[str, LocalCollection] = {}

    async def connect(self):
        try:
            logger.info(f"Attempting MongoDB connection: {settings.MONGODB_URI}")
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=1500
            )
            # Ping test
            await self.client.admin.command('ping')
            self.db = self.client[settings.DATABASE_NAME]
            self.is_connected = True
            self.mode = "mongodb"
            logger.info(f"Connected to live MongoDB at {settings.MONGODB_URI}")
        except Exception as e:
            logger.warning(f"MongoDB not available ({e}). Using embedded document store: {self._fallback_dir}")
            self.mode = "local_json"
            self.is_connected = True
            self.db = self

    def get_collection(self, name: str):
        if self.mode == "mongodb":
            return self.db[name]
        if name not in self._collections:
            self._collections[name] = LocalCollection(name, self._fallback_dir)
        return self._collections[name]

    def __getitem__(self, name: str):
        return self.get_collection(name)

    async def close(self):
        if self.client and self.mode == "mongodb":
            self.client.close()
            logger.info("MongoDB connection closed.")

db_manager = DatabaseManager()

def get_db():
    return db_manager
