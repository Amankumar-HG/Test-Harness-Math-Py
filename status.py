import random

def get_status_score():
    """Returns a status score between 0 and 100 with up to 2 decimal points."""
    return round(random.uniform(0, 100), 2)
