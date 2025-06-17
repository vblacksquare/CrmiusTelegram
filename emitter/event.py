
import enum


class EventType(enum.Enum):
    new_message = "new_message"
    send_message = "send_message"
    public_log_message = "public_log_message"
    private_log_message = "private_log_message"

    new_task = "new_task"
    send_task = "send_task"

    new_lead = "new_lead"
