"""
Context Manager for MedflowAI.

This module defines the ContextManager class, responsible for managing the 
state, history, and other contextual information for a given session or 
interaction flow within the MedflowAI library.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class BaseContextStore(ABC):
    """
    Abstract base class for context storage backends (e.g., in-memory, Redis, database).
    """
    @abstractmethod
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieves the conversation history for a session."""
        pass

    @abstractmethod
    def add_to_history(self, session_id: str, message: Dict[str, str]):
        """Adds a message to the conversation history of a session."""
        pass

    @abstractmethod
    def get_variable(self, session_id: str, key: str) -> Any:
        """Retrieves a session-specific variable."""
        pass

    @abstractmethod
    def set_variable(self, session_id: str, key: str, value: Any):
        """Sets a session-specific variable."""
        pass

    @abstractmethod
    def clear_session(self, session_id: str):
        """Clears all context for a given session."""
        pass

class InMemoryContextStore(BaseContextStore):
    """
    A simple in-memory context store for demonstration and testing.
    This store is not persistent across application restarts.
    """
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        # print("InMemoryContextStore initialized.")

    def _ensure_session(self, session_id: str):
        """Ensures a session entry exists in the store."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {"history": [], "variables": {}}
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        self._ensure_session(session_id)
        # Return a copy to prevent external modification of the internal list
        return list(self.sessions[session_id]["history"])

    def add_to_history(self, session_id: str, message: Dict[str, str]):
        self._ensure_session(session_id)
        self.sessions[session_id]["history"].append(message)

    def get_variable(self, session_id: str, key: str) -> Any:
        self._ensure_session(session_id)
        return self.sessions[session_id]["variables"].get(key)

    def set_variable(self, session_id: str, key: str, value: Any):
        self._ensure_session(session_id)
        self.sessions[session_id]["variables"][key] = value

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
            # print(f"Session {session_id} cleared from InMemoryContextStore.")

class ContextManager:
    """
    Manages the context for a specific session, including conversation history
    and session-specific variables. It uses a pluggable context store.
    """
    def __init__(self, session_id: str, store: BaseContextStore):
        """
        Initializes the ContextManager for a given session.

        Args:
            session_id (str): The unique identifier for the session.
            store (BaseContextStore): The storage backend for context.
        """
        if not session_id:
            raise ValueError("session_id cannot be empty or None for ContextManager.")
        self.session_id = session_id
        self.store = store
        # print(f"ContextManager initialized for session {self.session_id} with store {store.__class__.__name__}.")

    def add_message(self, role: str, content: str):
        """
        Adds a message to the conversation history for the current session.
        Standard roles are "user" and "assistant". Others like "system" or "tool" can also be used.
        """
        if not role or not content:
            # Consider raising an error or logging more formally
            print(f"Warning: Attempted to add message with empty role or content for session {self.session_id}")
            return
        message = {"role": role, "content": content}
        self.store.add_to_history(self.session_id, message)

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Retrieves the conversation history for the current session.
        Optionally limits the number of messages returned (most recent entries).
        """
        history = self.store.get_history(self.session_id)
        if limit and limit > 0:
            return history[-limit:]
        return history
    
    def get_formatted_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Retrieves the conversation history, already in the list of dicts format suitable for LLMs.
        This might involve transformations in more complex store implementations.
        """
        return self.get_history(limit=limit)

    def set(self, key: str, value: Any):
        """
        Sets a session-specific variable for the current session.
        """
        self.store.set_variable(self.session_id, key, value)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Retrieves a session-specific variable for the current session.
        Returns the default value if the key is not found.
        """
        value = self.store.get_variable(self.session_id, key)
        return value if value is not None else default

    def clear(self):
        """
        Clears all context (history and variables) for the current session.
        """
        self.store.clear_session(self.session_id)

if __name__ == "__main__":
    print("MedflowAI ContextManager module (now in core package).")
    # Example Usage (can be uncommented for direct testing of this module):
    # global_store = InMemoryContextStore()
    
    # # Test session 1
    # ctx_mgr1 = ContextManager(session_id="session_alpha_001", store=global_store)
    # ctx_mgr1.add_message(role="user", content="Hello, this is Alpha.")
    # ctx_mgr1.add_message(role="assistant", content="Hello Alpha! How may I assist you today?")
    # ctx_mgr1.set("user_language", "en-US")
    # print(f"Alpha's History: {ctx_mgr1.get_history()}")
    # print(f"Alpha's Language: {ctx_mgr1.get('user_language')}")

    # # Test session 2 (demonstrates isolation)
    # ctx_mgr2 = ContextManager(session_id="session_beta_002", store=global_store)
    # ctx_mgr2.add_message(role="user", content="Hola, soy Beta.")
    # print(f"Beta's History: {ctx_mgr2.get_history()}")
    # print(f"Beta's Language (should be None): {ctx_mgr2.get('user_language')}")
    
    # # Show entire store content
    # print(f"\nGlobal InMemoryContextStore content: {global_store.sessions}")
    
    # # Clear session 1
    # ctx_mgr1.clear()
    # print(f"\nGlobal store after clearing Alpha's session: {global_store.sessions}")
