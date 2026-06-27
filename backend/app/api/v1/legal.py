import os
import shutil
import tempfile
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.gemini_service import process_incident_audio
from app.schemas.legal import ComplaintDraftResponse

router = APIRouter()
logger = logging.getLogger("LegalIntake")

@router.post("/intake", response_model=ComplaintDraftResponse)
async def voice_intake(file: UploadFile = File(...)):
    """
    [P0] Voice-based intake: transcribes audio, returns AI-drafted legal complaint.
    """
    valid_extensions = ('.wav', '.mp3', '.m4a', '.ogg', '.webm')
    # Strip path injections from the filename before checking extension
    safe_filename = os.path.basename(file.filename)
    
    if not safe_filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=400, 
            detail="Invalid audio format. Please upload wav, mp3, m4a, ogg, or webm."
        )

    # Use NamedTemporaryFile to completely block directory traversal attacks
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(safe_filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
            
        # Process the file through your Gemini service
        result = process_incident_audio(temp_path)
        return result
        
    except Exception as e:
        # Log the real error to terminal, but give the client a safe generic message
        logger.error(f"Voice intake failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An internal error occurred while processing the audio."
        )
        
    finally:
        # Ensure cleanup always happens safely
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)