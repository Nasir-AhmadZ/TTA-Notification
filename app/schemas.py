from pydantic import BaseModel, Field, BeforeValidator
from typing import Optional, Annotated
from datetime import datetime
from bson import ObjectId

#general way to validate a mongoid
def validate_object_id(value: str) -> str:
    if not ObjectId.is_valid(value):
        raise ValueError("Invalid MongoDB ObjectId")
    return value
    
MongoId = Annotated[str, BeforeValidator(validate_object_id)]


#*********************Notification models*************************
class NotificationUpdate(BaseModel):
    opened: bool

class GetNotifications(BaseModel):
    id: MongoId
    related_id: MongoId
    timestamp: datetime

class Notification(BaseModel):
    id: MongoId
    user_id: MongoId
    related_id: MongoId  # project or entry id
    timestamp: datetime
    opened: bool = False
