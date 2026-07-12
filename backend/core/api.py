"""
Znova-style decorators for field computation and onchange logic.
"""

def depends(*args):
    """
    Decorator for compute fields indicating dependencies.
    """
    def decorator(func):
        func._depends = args
        return func
    return decorator

def onchange(*args):
    """
    Decorator for onchange methods.
    """
    def decorator(func):
        func._onchange = args
        return func
    return decorator

def constrains(*args):
    """
    Decorator for constraint methods.
    """
    def decorator(func):
        func._constrains = args
        return func
    return decorator

def model(func):
    """
    Decorator for model-level methods (cls instead of self).
    """
    func._model = True
    return classmethod(func)
