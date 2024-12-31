
def ensure_type(var:any, *expected_types:list[type]):
    if None in expected_types and var is None:
        return var
    expected_types = [t for t in expected_types if t is not None]
    if all(map(lambda t: not isinstance(var, t), expected_types)):
        raise TypeError(f"[ensure_type] Invalid type: expected one of {expected_types}, got {type(var)}")
    return var
    
def indent(text:str, nspaces=2):
    if text=="": return ""
    tab = " " * nspaces
    return tab + f"\n{tab}".join(text.splitlines())

class IdProvider:
    def __init__(self):
        self._id = 0
    
    def create_id(self):
        self._id += 1
        return self._id
        
    def __call__(self): return self.create_id()