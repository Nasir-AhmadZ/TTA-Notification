
def notification_helper(notification) -> dict:
    return {
        "id": str(notification["_id"]),
        "related_id": notification["related_id"],
        "message": str(notification["message"]),
        "timestamp": notification["created_at"]
    }
