from backend.database import get_sync_db
from backend.models import BotContent
from sqlalchemy.exc import SQLAlchemyError

class ContentManager:
    _instance = None
    _cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContentManager, cls).__new__(cls)
            cls._instance._load_cache()
        return cls._instance

    def _load_cache(self):
        """Load all content from DB to memory"""
        try:
            with get_sync_db() as session:
                contents = session.query(BotContent).all()
                self._cache = {c.key: c.value for c in contents}
                print(f"DEBUG: Loaded {len(self._cache)} content items.")
        except Exception as e:
            print(f"ERROR: Failed to load content cache: {e}")
            self._cache = {}

    def get(self, key, default=None):
        """Get text from cache. If missing and default provided, save default to DB."""
        val = self._cache.get(key)
        if val is None and default is not None:
            # Lazy seed
            self.set(key, default)
            return default
        return val if val is not None else default

    def set(self, key, value, description=None, category="general"):
        """Update text in DB and Cache"""
        try:
            with get_sync_db() as session:
                content = session.query(BotContent).filter(BotContent.key == key).first()
                if content:
                    content.value = value
                    if description: content.description = description
                    if category: content.category = category
                else:
                    content = BotContent(key=key, value=value, description=description, category=category)
                    session.add(content)
                
                # Update cache immediately
                self._cache[key] = value
                return True
        except SQLAlchemyError as e:
            print(f"ERROR: Failed to update content {key}: {e}")
            return False

    def get_all(self):
        """Get all cached content"""
        return self._cache

content_manager = ContentManager()
