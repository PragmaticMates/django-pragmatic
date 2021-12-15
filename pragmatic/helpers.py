def method_overridden(object, method_name):
    return getattr(type(object), method_name) is not getattr(type(object).__bases__[0], method_name)
