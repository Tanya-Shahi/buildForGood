import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.gemini_service import process_incident_audio
from app.schemas.legal import ComplaintDraftResponse

router = APIRouter()

@router.post("/intake", response_model=ComplaintDraftResponse)
async def voice_intake(file: UploadFile = File(...)):
    """
    [P0] Voice-based intake: accepts an audio file, transcribes it, 
    and returns an AI-drafted legal complaint.
    """
    # Quick validation to ensure they are sending audio
    valid_extensions = ('.wav', '.mp3', '.m4a', '.ogg', '.webm')
    if not file.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=400, 
            detail="Invalid audio format. Please upload wav, mp3, m4a, ogg, or webm."
        )

    # Use UUID to prevent file overwrites if two users hit the API at the exact same time
    temp_path = f"temp_{uuid.uuid4()}_{file.filename}"
    
    try:
        # Save the incoming file to your local disk temporarily
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process the file through your Gemini service
        result = process_incident_audio(temp_path)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # The finally block ensures the temp file is ALWAYS deleted, 
        # even if the API crashes or Gemini throws an error.
        if os.path.exists(temp_path):
            os.remove(temp_path)