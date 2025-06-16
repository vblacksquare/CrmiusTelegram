
import enum


class EventType(enum.Enum):
    new_message = "new_message"
    send_message = "send_message"
    
    new_task = "new_task"
    new_lead = "new_lead"
