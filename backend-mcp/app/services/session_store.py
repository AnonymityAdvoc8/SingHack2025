"""
Simple session store for conversation persistence
Stores sessions in a local JSON file to survive server restarts
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading
from pathlib import Path


class SessionStore:
    """Thread-safe session storage with file persistence"""
    
    def __init__(self, storage_path: str = ".sessions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.lock = threading.Lock()
        
    def _get_session_file(self, session_id: str) -> Path:
        """Get the file path for a session"""
        # Use first 8 chars of session_id for filename
        safe_id = "".join(c for c in session_id if c.isalnum())[:32]
        return self.storage_path / f"{safe_id}.json"
    
    def save_session(
        self,
        session_id: str,
        conversation_history: List[Dict[str, Any]],
        extracted_trip_details: Optional[Dict[str, Any]] = None,
        trip_context: Optional[Dict[str, Any]] = None,
        gmail_authorized: Optional[bool] = None,
        gmail_scan_results: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Save session to disk with trip context, Gmail auth, and scan results"""
        if not session_id:
            return False
            
        with self.lock:
            try:
                session_data = {
                    "session_id": session_id,
                    "conversation_history": conversation_history,
                    "extracted_trip_details": extracted_trip_details or {},
                    "trip_context": trip_context or {},
                    "gmail_authorized": gmail_authorized or False,
                    "gmail_scan_results": gmail_scan_results or [],  # NEW: Persist scan results
                    "last_updated": datetime.utcnow().isoformat(),
                    "created_at": datetime.utcnow().isoformat()
                }
                
                session_file = self._get_session_file(session_id)
                
                # Load existing to preserve created_at
                if session_file.exists():
                    with open(session_file, 'r') as f:
                        existing = json.load(f)
                        session_data["created_at"] = existing.get("created_at", session_data["created_at"])
                
                with open(session_file, 'w') as f:
                    json.dump(session_data, f, indent=2)
                
                return True
            except Exception as e:
                print(f"Error saving session {session_id}: {e}")
                return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session from disk"""
        if not session_id:
            return None
            
        with self.lock:
            try:
                session_file = self._get_session_file(session_id)
                
                if not session_file.exists():
                    return None
                
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                # Check if session is too old (> 24 hours)
                last_updated = datetime.fromisoformat(session_data.get("last_updated"))
                if datetime.utcnow() - last_updated > timedelta(hours=24):
                    # Session expired
                    self.delete_session(session_id)
                    return None
                
                return session_data
            except Exception as e:
                print(f"Error loading session {session_id}: {e}")
                return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session from disk"""
        if not session_id:
            return False
            
        with self.lock:
            try:
                session_file = self._get_session_file(session_id)
                if session_file.exists():
                    session_file.unlink()
                return True
            except Exception as e:
                print(f"Error deleting session {session_id}: {e}")
                return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up sessions older than max_age_hours"""
        with self.lock:
            try:
                for session_file in self.storage_path.glob("*.json"):
                    try:
                        with open(session_file, 'r') as f:
                            session_data = json.load(f)
                        
                        last_updated = datetime.fromisoformat(session_data.get("last_updated"))
                        if datetime.utcnow() - last_updated > timedelta(hours=max_age_hours):
                            session_file.unlink()
                    except Exception:
                        # If we can't read it, delete it
                        session_file.unlink()
            except Exception as e:
                print(f"Error during session cleanup: {e}")


# Global session store instance
_session_store = None


def get_session_store() -> SessionStore:
    """Get or create the global session store"""
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store

