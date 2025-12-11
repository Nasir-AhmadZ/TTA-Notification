
def notification_helper(notification) -> dict:
    return {
        "id": str(notification["_id"]),
        "related_id": notification["related_id"],
        "timestamp": notification["created_at"]
    }
