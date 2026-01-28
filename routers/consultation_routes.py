from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import uuid
from datetime import datetime
from jose import jwt, JWTError

from database.database import get_db
from models.sql_models.consultation_models import ConsultationMessage, ConsultationMessageSenderRole
from models.sql_models.appointments_model import Appointment
from routers.authentication.authenticate import SECRET_KEY, ALGORITHM, get_current_user_from_token

# Import models to ensure we can query them if needed
from models.sql_models.patient_models import Patient
from models.sql_models.specialist_models import Specialists

router = APIRouter(
    prefix="/consultation",
    tags=["Consultation Chat"]
)

# -----------------------------------------------------------------------------
# Connection Manager
# -----------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        # Map appointment_id -> List of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, appointment_id: str):
        await websocket.accept()
        if appointment_id not in self.active_connections:
            self.active_connections[appointment_id] = []
        self.active_connections[appointment_id].append(websocket)

    def disconnect(self, websocket: WebSocket, appointment_id: str):
        if appointment_id in self.active_connections:
            if websocket in self.active_connections[appointment_id]:
                self.active_connections[appointment_id].remove(websocket)
            if not self.active_connections[appointment_id]:
                del self.active_connections[appointment_id]

    async def broadcast(self, message: str, appointment_id: str):
        """Send message to all connected clients in this appointment room"""
        if appointment_id in self.active_connections:
            for connection in self.active_connections[appointment_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    # If sending fails, we might want to remove the dead connection
                    # But typically disconnect() handles graceful closures.
                    pass

manager = ConnectionManager()

# -----------------------------------------------------------------------------
# WebSocket Endpoint
# -----------------------------------------------------------------------------

async def get_user_from_socket_token(token: str, db: Session):
    """
    Authenticate WebSocket user via query param token.
    Returns (user_id, user_type) tuple or raises generic Exception on failure.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        if not user_id or not user_type:
            raise Exception("Invalid token")
        return user_id, user_type
    except JWTError:
        raise Exception("Invalid token")

@router.websocket("/ws/{appointment_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    appointment_id: str, 
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Real-time chat WebSocket.
    Clients connect to /ws/consultation/{appointment_id}?token=JWT
    """
    try:
        user_id, user_type = await get_user_from_socket_token(token, db)
    except Exception:
        await websocket.close(code=4003, reason="Authentication failed")
        return

    # Verify user belongs to this appointment
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            await websocket.close(code=4004, reason="Appointment not found")
            return
            
        # Check permissions
        is_participant = False
        role = None
        
        if user_type == "patient" and str(appointment.patient_id) == user_id:
            is_participant = True
            role = ConsultationMessageSenderRole.PATIENT
        elif user_type == "specialist" and str(appointment.specialist_id) == user_id:
            is_participant = True
            role = ConsultationMessageSenderRole.SPECIALIST
            
        if not is_participant:
             await websocket.close(code=4003, reason="Not authorized for this appointment")
             return

        # Connect
        await manager.connect(websocket, appointment_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                # data is expected to be just the message content string
                # or a JSON string if we decide to support structured events
                
                # Save to DB
                new_msg = ConsultationMessage(
                    appointment_id=appointment_id,
                    sender_id=user_id,
                    sender_role=role,
                    content=data,
                    is_read=False
                )
                db.add(new_msg)
                db.commit()
                db.refresh(new_msg)
                
                # Broadcast format
                message_payload = {
                    "id": str(new_msg.id),
                    "sender_id": str(new_msg.sender_id),
                    "sender_role": new_msg.sender_role.value,
                    "content": new_msg.content,
                    "created_at": new_msg.created_at.isoformat()
                }
                
                await manager.broadcast(json.dumps(message_payload), appointment_id)
                
        except WebSocketDisconnect:
            manager.disconnect(websocket, appointment_id)
            
    except Exception as e:
        print(f"WebSocket Error: {e}")
        try:
            await websocket.close()
        except:
            pass

# -----------------------------------------------------------------------------
# REST Endpoints
# -----------------------------------------------------------------------------

@router.get("/{appointment_id}/messages")
async def get_chat_history(
    appointment_id: str,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Fetch chat history for an appointment.
    """
    user_id = str(current_user["user"].id)
    user_type = current_user["user_type"]
    
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    # Verify access
    if user_type == "patient" and str(appointment.patient_id) != user_id:
         raise HTTPException(status_code=403, detail="Access denied")
    if user_type == "specialist" and str(appointment.specialist_id) != user_id:
         raise HTTPException(status_code=403, detail="Access denied")
         
    messages = db.query(ConsultationMessage)\
        .filter(ConsultationMessage.appointment_id == appointment_id)\
        .order_by(ConsultationMessage.created_at.asc())\
        .all()
        
    return [
        {
            "id": str(msg.id),
            "sender_id": str(msg.sender_id),
            "sender_role": msg.sender_role.value,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
            "is_read": msg.is_read
        }
        for msg in messages
    ]
