import threading

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
        """
        Initialize the set with a specified expiration time for elements.
        
        :param expiration_time: Time in seconds after which elements expire.
        """
        self.store = set()
        self.expiration_time = expiration_time
        self.lock = threading.Lock()

    def add(self, item):
        """
        Add an item to the set with an expiration time.

        :param item: Item to add.
        """
        with self.lock:
            self.store.add(item)

        # Schedule removal of the item after expiration_time seconds
        threading.Timer(self.expiration_time, self._remove_item, args=[item]).start()

    def remove(self, item):
        """
        Remove an item from the set.

        :param item: Item to remove.
        """
        self._remove_item(item)

    def __contains__(self, item):
        """
        Check if an item exists in the set and hasn't expired.

        :param item: Item to check.
        :return: True if the item exists, False otherwise.
        """
        with self.lock:
            return item in self.store

    def _remove_item(self, item):
        """
        Remove an item from the set. This is called internally by the timer.

        :param item: Item to remove.
        """
        with self.lock:
            self.store.discard(item)   # Use discard to avoid KeyError if the item is not present

    def __repr__(self):
        """
        String representation of the set for debugging.
        """
        with self.lock:
            return repr(self.store)
        
    def __iter__(self):
        """
        Iterate over the items in the set.
        """
        with self.lock:
            return iter(self.store)