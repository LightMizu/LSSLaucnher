def find_by_key(items, key, value):
    return next((item for item in items if item.get(key) == value), None)

def get_uuid_file(s3_key):
    return s3_key.split('/')[-1].split('.')[0]