import re

def build_character_name_string(input):
    return re.sub(r'_', ' ', re.sub(r'-(.+)', r' (\1)', input)).title()