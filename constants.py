"""Shared values stored in the database and accepted by the API."""

ROLES = ("citizen", "administrator")

COMPLAINT_CATEGORIES = (
    "road_damage",
    "drinking_water",
    "electricity",
    "sanitation",
    "healthcare",
    "education",
    "agriculture",
    "other",
)

COMPLAINT_STATUSES = (
    "pending",
    "under_review",
    "in_progress",
    "resolved",
    "rejected",
)

LOCATION_CATEGORIES = (
    "hospital",
    "school",
    "police_station",
    "government_office",
    "market",
    "pharmacy",
    "atm",
    "village_facility",
)

CATEGORY_LABELS = {
    "road_damage": "Road damage",
    "drinking_water": "Drinking water",
    "electricity": "Electricity",
    "sanitation": "Sanitation",
    "healthcare": "Healthcare",
    "education": "Education",
    "agriculture": "Agriculture",
    "other": "Other",
}

STATUS_LABELS = {
    "pending": "Pending",
    "under_review": "Under Review",
    "in_progress": "In Progress",
    "resolved": "Resolved",
    "rejected": "Rejected",
}
