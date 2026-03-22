CLEANLINESS = {
    "light_dust",
    "moderate_dust",
    "heavy_dust",
    "debris",
    "foreign_object",
}

MECHANICAL = {
    "corrosion",
    "crack",
    "dent",
    "loose_lining",
    "damaged_joint",
}

MOISTURE = {
    "staining",
    "moisture_presence",
    "condensation_signs",
    "suspected_microbial_growth",
}

OBSTRUCTION = {
    "partial_blockage",
    "severe_blockage",
    "narrowing",
}

ALL_DEFECTS = CLEANLINESS | MECHANICAL | MOISTURE | OBSTRUCTION

URGENT_DEFECTS = {
    "severe_blockage",
    "moisture_presence",
    "suspected_microbial_growth",
    "crack",
}
