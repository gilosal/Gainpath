from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import UserProfile
from ..schemas.user import UserProfileRead, UserProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


def _get_or_create_profile(db: Session) -> UserProfile:
    """Single-user app — always work with the one profile row."""
    profile = db.query(UserProfile).first()
    if not profile:
        profile = UserProfile()
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=UserProfileRead)
def get_profile(db: Session = Depends(get_db)):
    return _get_or_create_profile(db)


@router.put("", response_model=UserProfileRead)
def update_profile(payload: UserProfileUpdate, db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    update_data = payload.model_dump(exclude_unset=True)
    update_data.pop("id", None)
    for field, value in update_data.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
