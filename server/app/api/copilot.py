import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import CopilotRequest, CopilotResponse
from app.services.copilot_service import chat

router = APIRouter()


@router.post("/copilot/chat", response_model=CopilotResponse)
def copilot_chat(req: CopilotRequest, db: Session = Depends(get_db)):
    try:
        response_text, session_id = chat(db, req.message, req.session_id)
        return CopilotResponse(response=response_text, session_id=session_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM Provider error ({e.response.status_code}): {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Copilot error: {str(e)}"
        )
