from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "SafeVillage",
        "message": "API is running. This is a community information demo, not a government system.",
    }
