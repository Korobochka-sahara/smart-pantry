from app.db.database import SessionLocal
from app.services.auth_service import cleanup_refresh_tokens


def cleanup_tokens_job() -> None:
    db = SessionLocal()

    try:
        deleted_count = cleanup_refresh_tokens(db)

        print(
            f"Refresh token cleanup: "
            f"deleted {deleted_count} tokens"
        )

    finally:
        db.close()