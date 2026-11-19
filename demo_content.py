"""Demo catalog.

Scheme eligibility and benefits are intentionally NOT invented.
Each scheme points to a public government website and tells the reader
to verify the rules there. Location rows are labelled samples.
"""

UNVERIFIED = (
    "Demonstration record only. SafeVillage does not publish official eligibility "
    "rules or benefit amounts. Verify this on the official government website before acting on it."
)

SCHEMES = [
    {
        "name": "Pradhan Mantri Awas Yojana",
        "short_name": "PMAY",
        "description": "A public housing programme. This demo card only identifies the programme and its official website.",
        "category": "housing",
        "state_applicability": "India (confirm state rules on the official site)",
        "official_url": "https://pmayg.nic.in/",
    },
    {
        "name": "Pradhan Mantri Kisan Samman Nidhi",
        "short_name": "PM-KISAN",
        "description": "A farmer income-support programme. This demo card only identifies the programme and its official website.",
        "category": "agriculture",
        "state_applicability": "India (confirm state rules on the official site)",
        "official_url": "https://pmkisan.gov.in/",
    },
    {
        "name": "Mahatma Gandhi National Rural Employment Guarantee Act",
        "short_name": "MGNREGA",
        "description": "A rural employment programme. This demo card only identifies the programme and its official website.",
        "category": "employment",
        "state_applicability": "India (confirm state rules on the official site)",
        "official_url": "https://nrega.nic.in/",
    },
    {
        "name": "Ayushman Bharat Pradhan Mantri Jan Arogya Yojana",
        "short_name": "PM-JAY",
        "description": "A public health-cover programme. This demo card only identifies the programme and its official website.",
        "category": "healthcare",
        "state_applicability": "India (confirm state rules on the official site)",
        "official_url": "https://pmjay.gov.in/",
    },
    {
        "name": "Jal Jeevan Mission",
        "short_name": "JJM",
        "description": "A rural tap-water programme. This demo card only identifies the programme and its official website.",
        "category": "drinking_water",
        "state_applicability": "India (confirm state rules on the official site)",
        "official_url": "https://jaljeevanmission.gov.in/",
    },
]

EMERGENCY_CONTACTS = [
    {
        "name": "National Emergency Number",
        "phone": "112",
        "description": "India's single emergency response number (ERSS). Informational listing only. SafeVillage cannot place the call for you.",
        "category": "national_emergency",
        "state": None,
        "district": None,
        "is_national": True,
    },
    {
        "name": "Fire",
        "phone": "101",
        "description": "Common fire-service number. Confirm local coverage. This is not live dispatch from SafeVillage.",
        "category": "fire",
        "state": None,
        "district": None,
        "is_national": True,
    },
    {
        "name": "Ambulance",
        "phone": "108",
        "description": "Ambulance number used in many states. Coverage differs by state. Confirm locally. Not live dispatch from SafeVillage.",
        "category": "ambulance",
        "state": None,
        "district": None,
        "is_national": True,
    },
    {
        "name": "Police",
        "phone": "100",
        "description": "Legacy police number. 112 is the unified emergency number. Informational listing only.",
        "category": "police",
        "state": None,
        "district": None,
        "is_national": True,
    },
    {
        "name": "Sample: Demo Gram help desk",
        "phone": "112",
        "description": "Sample location note for the hackathon. This is not an additional emergency service. Call 112 for a real emergency.",
        "category": "local_information",
        "state": "West Bengal",
        "district": "Demo District",
        "is_national": False,
    },
]

# Approximate public-area coordinates for distance sorting in the demo.
# Names are fictional samples. They are not claimed to be real facilities.
SAMPLE_PLACES = [
    {"name": "Sample: Demo Gram Primary Health Centre", "category": "hospital", "area": "Demo Gram, West Bengal", "lat": 23.67, "lng": 86.95},
    {"name": "Sample: Demo Gram Community Clinic", "category": "hospital", "area": "Demo Gram, West Bengal", "lat": 23.70, "lng": 86.98},
    {"name": "Sample: Demo Gram Primary School", "category": "school", "area": "Demo Gram, West Bengal", "lat": 23.66, "lng": 86.94},
    {"name": "Sample: Demo Gram High School", "category": "school", "area": "Demo Gram, West Bengal", "lat": 23.69, "lng": 86.97},
    {"name": "Sample: Demo Gram Police Outpost", "category": "police_station", "area": "Demo Gram, West Bengal", "lat": 23.68, "lng": 86.96},
    {"name": "Sample: Demo Block Office", "category": "government_office", "area": "Demo Gram, West Bengal", "lat": 23.71, "lng": 86.99},
    {"name": "Sample: Demo Gram Weekly Market", "category": "market", "area": "Demo Gram, West Bengal", "lat": 23.665, "lng": 86.955},
    {"name": "Sample: Demo Gram Pharmacy", "category": "pharmacy", "area": "Demo Gram, West Bengal", "lat": 23.672, "lng": 86.948},
    {"name": "Sample: Demo Gram ATM", "category": "atm", "area": "Demo Gram, West Bengal", "lat": 23.674, "lng": 86.962},
    {"name": "Sample: Demo Gram Community Hall", "category": "village_facility", "area": "Demo Gram, West Bengal", "lat": 23.668, "lng": 86.951},
]

LOCATION_DISCLAIMER = (
    "Sample directory for the hackathon. These are not verified live facilities and not emergency dispatch. "
    "Use the Google Maps search link to look up public places. In an emergency call 112."
)

SCHEME_NOTICE = (
    "These are demonstration records. Eligibility, benefits, documents, and the application steps "
    "must be confirmed on the official government website. SafeVillage is not a government portal."
)

AI_DISCLAIMER = (
    "SafeVillage shares general information only. This is not an official government decision, "
    "not a medical diagnosis, and not confirmation that any service is available in your village. "
    "For a medical emergency call 112."
)
