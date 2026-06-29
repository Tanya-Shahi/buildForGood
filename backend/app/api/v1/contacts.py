from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user import User, EmergencyContact

router = APIRouter()

# --- Pydantic Schemas ---
class ContactCreate(BaseModel):
    name: str
    phone_number: str

class ContactResponse(BaseModel):
    id: int
    name: str
    phone_number: str

# --- Routes ---
@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def add_emergency_contact(
    contact_in: ContactCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """[P1] Adds a new emergency contact for the authenticated user."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Optional: Limit to 5 contacts to prevent spam
    existing_count = db.query(EmergencyContact).filter(EmergencyContact.user_id == user.id).count()
    if existing_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum of 5 emergency contacts allowed.")

    new_contact = EmergencyContact(
        user_id=user.id,
        name=contact_in.name,
        phone_number=contact_in.phone_number
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    
    return new_contact

@router.get("/", response_model=List[ContactResponse])
def get_emergency_contacts(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """[P1] Fetches all emergency contacts for the authenticated user."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == user.id).all()
    return contacts

@router.delete("/{contact_id}")
def delete_emergency_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """[P1] Deletes a specific emergency contact."""
    user = db.query(User).filter(User.username == current_user).first()
    
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.user_id == user.id # 🔥 BOLA Protection: Ensure they own this contact!
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found or access denied.")
        
    db.delete(contact)
    db.commit()
    return {"status": "Success", "message": "Emergency contact removed."}