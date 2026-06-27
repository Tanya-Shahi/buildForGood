import os
import json
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from app.core.config import settings

# Initialize the SDK with your API key
genai.configure(api_key=settings.GEMINI_API_KEY)

# We use 1.5 Flash because it natively supports audio and is incredibly fast
model = genai.GenerativeModel("gemini-3.5-flash")

def process_incident_audio(audio_file_path: str) -> dict:
    """
    [P0] Takes raw audio, transcribes it, and structures it into a 
    legal complaint draft using LLM reasoning.
    """
    # 1. Upload the temporary audio file to Gemini's servers
    audio_file = genai.upload_file(path=audio_file_path)
    
    # 2. Prompt the AI for structured output
    prompt = """
    You are a legal assistant for a women's safety platform in India.
    Listen to this audio (which may be in Hindi, regional languages, or English) 
    and provide a structured JSON response with the following keys:
    - "transcription": The raw text of what was said (translated to English if necessary).
    - "summary": A concise 2-sentence summary of the incident.
    - "complaint_draft": A structured, formal complaint draft (First Information Report style) ready for NGO/human review.
    - "severity": Classify as 'High', 'Medium', or 'Low'.
    - "next_steps": A list of 3 immediate safety or legal steps the user should take.
    """
    
    # 3. Generate the response and explicitly force JSON format
    response = model.generate_content(
        [prompt, audio_file],
        generation_config=GenerationConfig(
            response_mime_type="application/json"
        )
    )
    
    # 4. Clean up the file from Gemini to prevent quota/privacy issues
    genai.delete_file(audio_file.name)
    
    # 5. Parse the guaranteed JSON string back into a Python dictionary
    return json.loads(response.text)