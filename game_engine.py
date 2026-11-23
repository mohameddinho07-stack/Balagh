import random

from data import (
    CHARACTERS,
    LOCATIONS,
    VICTIMS,
    INVESTIGATION_RESULTS
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

def investigate(action):

    if action in INVESTIGATION_RESULTS:
        return random.choice(
            INVESTIGATION_RESULTS[action]
        )

    return "لا توجد معلومات جديدة."
