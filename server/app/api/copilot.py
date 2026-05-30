from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import CopilotRequest, CopilotResponse
from app.services.copilot_service import chat

router = APIRouter()


@router.post("/copilot/chat", response_model=CopilotResponse)
def copilot_chat(req: CopilotRequest, db: Session = Depends(get_db)):
    response_text, session_id = chat(db, req.message, req.session_id)
    return CopilotResponse(response=response_text, session_id=session_id)
