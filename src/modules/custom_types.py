import threading
import time

class FalseType(type):
    # Override __bool__ to make the class itself falsy
    def __bool__(cls):
        return False

class _Missing(metaclass=FalseType):
    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

    def __bool__(self):
        return False

    def __repr__(self):
        return "_Missing()"
    
    def __str__(self):
        return "MISSING"

MISSING = _Missing
'''A constant value used for cases when there is no value when there should be.'''

class _Unset_Value(metaclass=FalseType):
    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

    def __bool__(self):
        return False

    def __repr__(self):
        return "_Unset_Value()"
    
    def __str__(self):
        return "UNSET_VALUE"

UNSET_VALUE = _Unset_Value
'''A constant value used as a placeholder value.'''


class ExpiringSet:
    def __init__(self, expiration_time=5):
        self.expiration_time = expiration_time
        # Store item as key, expiration timestamp as value
        self.store = {}
        self.lock = threading.Lock()

    def add(self, item):
        with self.lock:
            # Overwriting the timestamp effectively "renews" the item
            self.store[item] = time.time() + self.expiration_time

    def __contains__(self, item):
        with self.lock:
            self._purge_expired()
            return item in self.store

    def _purge_expired(self):
        """Internal helper to clean up expired items. Assumes lock is already held."""
        now = time.time()
        # Create a list of expired keys to avoid 'size changed' error during dict iteration
        expired = [item for item, expiry in self.store.items() if now > expiry]
        for item in expired:
            del self.store[item]

    def __iter__(self):
        with self.lock:
            self._purge_expired()
            # Return a list copy to ensure iteration is thread-safe
            return iter(list(self.store.keys()))

    def __repr__(self):
        with self.lock:
            self._purge_expired()
            return f"ExpiringSet({list(self.store.keys())})"