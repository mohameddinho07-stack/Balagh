import random

from data import (
    CRIME_TYPES,
    LOCATIONS,
    SUSPECTS,
    CLUES
)

def generate_case():

    crime = random.choice(CRIME_TYPES)

    location = random.choice(LOCATIONS)

    suspects = random.sample(SUSPECTS, 4)

    killer = random.choice(suspects)

    clues = random.sample(CLUES, 3)

    return {
        "crime": crime,
        "location": location,
        "suspects": suspects,
        "killer": killer,
        "clues": clues
    }