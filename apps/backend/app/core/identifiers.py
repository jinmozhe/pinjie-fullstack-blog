import uuid


def new_uuid7() -> uuid.UUID:
    """Generate the only UUID v7 representation exposed to application code."""
    generator = getattr(uuid, "uuid7", None)
    if generator is None:
        raise RuntimeError("Python 3.14 or newer is required for UUID v7 generation")
    value = generator()
    if type(value) is not uuid.UUID or value.version != 7:
        raise RuntimeError("the UUID v7 generator returned an invalid value")
    return value
