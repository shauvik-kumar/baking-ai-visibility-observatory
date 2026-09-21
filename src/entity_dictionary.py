"""
Controlled entity dictionary for the Baking AI Visibility Observatory.

This is a research validation layer, not a general NLP entity recognizer.

Each query has a controlled set of canonical entities and the exact
aliases/phrases we are willing to map to that entity.
"""

ENTITY_DICTIONARY = {

    # Q7:
    # What are the best online baking classes for beginners in India?
    7: {
        "Lavonne Academy": [
            "Lavonne Academy",
            "Lavonne",
        ],

        "Academy of Pastry & Culinary Arts": [
            "Academy of Pastry & Culinary Arts",
            "APCA",
        ],

        "Bake with Shivesh": [
            "Bake with Shivesh",
            "Shivesh Bhatia",
        ],

        "La Folie Academy": [
            "La Folie Academy",
        ],

        "Chef Sanjana Patel": [
            "Chef Sanjana Patel",
        ],

        "Truffle Nation": [
            "Truffle Nation",
        ],

        "Udemy": [
            "Udemy",
        ],

        "Skillshare": [
            "Skillshare",
        ],

        "Alpa Pereira": [
            "Alpa Pereira",
        ],

        "Deepali Arora": [
            "Deepali Arora",
        ],

        "Reema's Swad Cooking Classes": [
            "Reema’s Swad Cooking Classes",
            "Reema's Swad Cooking Classes",
            "Reema's Swad",
            "Reema’s Swad",
        ],

        "Truffles 'n' Hazelnut": [
            "Truffles 'n' Hazelnut",
        ],

        "Sonali Garewal": [
            "Sonali Garewal",
        ],

        "Anyone Can Cook with Rashmi": [
            "Anyone Can Cook with Rashmi",
        ],

        "Gokul Kitchen": [
            "Gokul Kitchen",
        ],
    },

        # Q9:
    # What is a good oven for home baking in India?
    9: {
        "Borosil Prima 42L": [
            "Borosil Prima 42-Litre OTG",
            "Borosil Prima 42L",
        ],

        "Borosil Prima 60L": [
            "Borosil Prima 60-Litre OTG",
            "Borosil Prima 60L",
        ],

        "Borosil PRO 30L": [
            "Borosil PRO 30L OTG",
            "Borosil PRO 30L",
        ],

        "Borosil PRO 60L": [
            "Borosil PRO 60L OTG",
            "Borosil PRO 60L",
        ],

        "Philips HD6976/00": [
            "Philips HD6976/00",
            "Philips HD6976",
        ],

        "Agaro Marvel 28L": [
            "Agaro Marvel 28-Litre OTG",
            "Agaro Marvel 28L OTG",
            "Agaro Marvel 28L",
        ],

        "Agaro Grand 40L / 48L": [
            "Agaro Grand 40L / 48L OTG",
            "Agaro Grand 40L / 48L",
        ],

        "Bajaj Majestic 28L": [
            "Bajaj Majestic 28-Litre OTG",
            "Bajaj Majestic 28L OTG",
            "Bajaj Majestic 28L",
        ],

        "Morphy Richards 52RCSS": [
            "Morphy Richards 52RCSS (52 Litre)",
            "Morphy Richards 52RCSS",
        ],

        "Morphy Richards 60L (Besto / RCSS)": [
            "Morphy Richards 60-Litre (Besto / RCSS)",
        ],

        "Morphy Richards Bestron 60RCSS": [
            "Morphy Richards Bestron 60 RCSS (60 Litre)",
            "Morphy Richards Bestron 60 RCSS",
            "Morphy Richards Bestron 60RCSS",
        ],

        "IFB 30L Convection Microwave": [
            "IFB 30 L Convection Microwave (30BR2 / 30FRC2)",
            "IFB 30 L Convection Microwave",
            "IFB 30L Convection Microwave",
        ],

        "Samsung 28L Convection Microwave": [
            "Samsung 28 L Convection Microwave (CE1041DSB2)",
            "Samsung 28 L Convection Microwave",
            "Samsung 28L Convection Microwave",
            "Samsung CE1041DSB2",
            "CE1041DSB2",
        ],
    },
    
}


def get_entities_for_query(query_id):
    """Return the controlled entity dictionary for a query."""
    return ENTITY_DICTIONARY.get(query_id, {})


def get_all_aliases(query_id):
    """Return alias -> canonical entity mappings for a query."""
    mapping = {}

    for canonical_entity, aliases in get_entities_for_query(query_id).items():
        for alias in aliases:
            mapping[alias.lower()] = canonical_entity

    return mapping