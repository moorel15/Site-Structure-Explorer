# Deliberately excluded
# - str.capitalize (can be composed with ucfirst(lower(string)) and is non-obviously named)
# - str.title (will make title_case more powerful)

def lower(string):
    """
    Convert all cased characters in a string to lowercase.
    """
    return string.lower()

def ucfirst(string):
    """
    Capitalize the first character of a string.
    """
    return upper(string[:1]) + string[1:]

def upper(string):
    """
    Convert all cased characters in a string to uppercase.
    """
    return string.upper()
