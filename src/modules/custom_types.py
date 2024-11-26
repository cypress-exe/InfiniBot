class _Missing:
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

class _Unset_Value:
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