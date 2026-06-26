"""
Curated category hierarchy for the-klein-store (Hand Tool Outlet).

Klein's app can't read `menus` and the store has no subcollections_list / templates / vendor
rules — so there is NO structural signal for a hierarchy. This is a Claude-authored grouping of
the store's tag-defined collections into a sensible category tree, by TAG (tags ~= collection
titles, with a few exceptions noted). Easy to adjust.
"""

# parent TAG -> child TAGs (all are real Klein collection tags)
HIERARCHY = {
    "Hand Tools": [
        "Pliers", "Screwdrivers", "Wrenches", "Sockets", "Allen Wrenches",
        "Hammers and Striking Tools", "Knives", "Bolt Cutters", "Chisels",
        "Files and Rasps", "Punch", "Cutters", "Nippers Snips And Scissors",
        "Scissors and Snips", "Clamps and Vises", "Staplers", "Tool Sets", "Saws",
    ],
    "Electricians Tools": [
        "Cable Termination", "Conduit Benders", "Fish Tape", "Pulling Grips",
        "Pulling Accessories", "Knockouts", "Voltage Ticks", "Wire Strippers", "Pulleys",
    ],
    "Test and Measurement": [
        "Clamp Meters", "Multimeters", "Electrical Testers", "Temperature Testers",
    ],
    "Tool Belts and Storage": [
        "Tool Belt Bags", "Tool Belt Systems", "Tool Holsters", "Carry Bags",
        "Canvas Buckets", "Tool Boxes", "Tool Totes", "Aprons", "Pant Belts",
        "Suspenders", "Tethers", "Jobsite Storage",
    ],
    "Power Tool Accessories": ["Drill Bits", "Bit Tips", "Hole Saws"],
    "Masonry": ["Rebar Benders"],  # "Masonry Tools" collection's tag is "Masonry"
}

# top-level categories with no children
STANDALONE = ["Levels", "Layout Tools", "Lasers", "Apparel", "Lights", "Accessories", "Replacement Parts"]

# operational / test / promo collections that are NOT real categories
EXCLUDE_TAGS = {"best-seller", "AL-Categorized", "New Item V2"}
EXCLUDE_TITLES = {
    "All Products", "Home page", "SHOPIFY BOT TEST", "TEST SOCKETS", "TESTETSTSTS",
    "Saw Blades", "Best Sellers", "Review Categorized", "VA Categorization Review",
}


def category_tags():
    s = set(HIERARCHY) | set(STANDALONE)
    for kids in HIERARCHY.values():
        s.update(kids)
    return s


def parent_of_tag():
    out = {}
    for parent, kids in HIERARCHY.items():
        for k in kids:
            out[k] = parent
    return out
