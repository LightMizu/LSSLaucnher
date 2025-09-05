import uuid

def find_by_key(items, key, value) -> dict[str, str]|None:
    return next((item for item in items if item.get(key) == value), None) 

def get_uuid_file(id) -> str:
    namespace = uuid.NAMESPACE_DNS
    return str(uuid.uuid5(namespace, str(id)))