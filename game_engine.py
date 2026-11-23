import random

from data import (
    CHARACTERS,
    LOCATIONS,
    VICTIMS
)

def generate_case():

    location = random.choice(LOCATIONS)

    victim = random.choice(VICTIMS)

    suspects = random.sample(CHARACTERS, 4)

    killer = random.choice(suspects)

    return {
        "victim": victim,
        "location": location,
        "suspects": suspects,
        "killer": killer
    }
