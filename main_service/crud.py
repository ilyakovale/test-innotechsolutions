from sqlalchemy.orm import Session

from models import Message


def create_message(
    db: Session,
    text: str,
    username: str | None = None,
    is_authenticated: bool = False,
) -> Message:
    msg = Message(text=text, username=username, is_authenticated=is_authenticated)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_all_messages(db: Session) -> list[Message]:
    return db.query(Message).order_by(Message.created_at.desc()).all()