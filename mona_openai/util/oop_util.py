"""
Utility logic for object-oriented stuff.
"""
import inspect


def create_combined_object(instances):
    """
    Create a new object that has the same methods as the given instances.

    This function takes an iterable of instances of a given class and returns
    a new object that has the same methods as the given instances. When calling
    these methods, it returns a tuple containing all the results of running
    that method for all instances.

    Args:
        instances: An iterable of instances of a given class.

    Returns:
        A new object that has the same methods as the given instances.
    """

    class CombinedObject:
        def __init__(self, instances):
            self._instances = instances

        def __getattr__(self, name):
            def method(*args, **kwargs):
                results = []
                for instance in self._instances:
                    func = getattr(instance, name)
                    if inspect.ismethod(func) or inspect.isfunction(func):
                        results.append(func(*args, **kwargs))
                return tuple(results)

            return method

    return CombinedObject(instances)
