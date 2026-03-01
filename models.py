import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class RoleEnum(enum.Enum):
    ADMIN = "Admin"
    LIBRARIAN = "Librarian"
    ASSISTANT = "Assistant"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.ASSISTANT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User(username={self.username}, role={self.role.value})>"
