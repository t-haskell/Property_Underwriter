from functools import lru_cache

@lru_cache(maxsize=512)
def memoize_key(key: str): 
    return key 