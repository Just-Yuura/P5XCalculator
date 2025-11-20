def validate_integer(value):
    if value == "":
        return True

    try:
        int (value)
        return True
    except ValueError:
        return False