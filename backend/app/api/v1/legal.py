import os
import shutil
import tempfile
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from app.services.gemini_service import process_incident_audio
from app.schemas.legal import ComplaintDraftResponse
from app.api.deps import get_current_user  # 🔥 NEW: Security dependency

router = APIRouter()
logger = logging.getLogger("LegalIntake")

# Limit audio uploads to 10 MB to prevent disk exhaustion (Bug 3.5)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 

def save_and_process_audio(upload_file: UploadFile, safe_filename: str) -> dict:
    """Synchronous helper function to be run in a separate thread."""
    # 🔥 FIX (Bug 2.4): Use NamedTemporaryFile to block path traversal
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(safe_filename)[1]) as tmp:
        shutil.copyfileobj(upload_file.file, tmp)
        temp_path = tmp.name
        
    try:
        # Pass the secure temp file to the Gemini service
        return process_incident_audio(temp_path)
    finally:
        # ALWAYS clean up the temporary file, even if Gemini crashes
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/intake", response_model=ComplaintDraftResponse)
async def voice_intake(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)  # 🔥 FIX (Bug 2.1): Secure Endpoint
):
    """
    [P0] Voice-based intake: transcribes audio, returns AI-drafted legal complaint.
    """
    valid_extensions = ('.wav', '.mp3', '.m4a', '.ogg', '.webm')
    safe_filename = os.path.basename(file.filename)
    
    # 1. Validate Extension
    if not safe_filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=400, 
            detail="Invalid audio format. Please upload wav, mp3, m4a, ogg, or webm."
        )

    # 2. Validate File Size (Bug 3.5)
    if file.size and file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413, 
            detail="File too large. Maximum audio size is 10MB."
        )

    try:
        # 🔥 FIX (Bug 3.1): Delegate file I/O and network calls to a background thread!
        # This keeps the async event loop wide open for WebSockets and SOS alerts.
        result = await run_in_threadpool(save_and_process_audio, file, safe_filename)
        return result
        
    except Exception as e:
        logger.error(f"Voice intake failed: {str(e)}", exc_info=True)
        # Protect internal stack traces from leaking to the frontend (Bug 2.7)
        raise HTTPException(
            status_code=500, 
            detail="An internal error occurred while processing the audio."
        )