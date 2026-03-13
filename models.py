import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Date
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class RoleEnum(enum.Enum):
    ADMIN = "Admin"
    LIBRARIAN = "Librarian"
    ASSISTANT = "Assistant"

class BookStatusEnum(enum.Enum):
    AVAILABLE = "Available"
    BORROWED = "Borrowed"
    LOST = "Lost"

class BorrowStatusEnum(enum.Enum):
    ACTIVE = "Active"
    RETURNED = "Returned"
    OVERDUE = "Overdue"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.ASSISTANT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User(username={self.username}, role={self.role.value})>"

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    author = Column(String(100), nullable=False)
    category = Column(String(50))
    stock = Column(Integer, default=1)
    status = Column(Enum(BookStatusEnum), default=BookStatusEnum.AVAILABLE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    borrowings = relationship("BorrowingRecord", back_populates="book", cascade="all, delete")

    def __repr__(self):
        return f"<Book(title={self.title}, isbn={self.isbn})>"

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20))
    membership_date = Column(DateTime, default=datetime.utcnow)

    borrowings = relationship("BorrowingRecord", back_populates="member", cascade="all, delete")

    def __repr__(self):
        return f"<Member(name={self.first_name} {self.last_name})>"

class BorrowingRecord(Base):
    __tablename__ = "borrowing_records"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    borrow_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)
    status = Column(Enum(BorrowStatusEnum), default=BorrowStatusEnum.ACTIVE, nullable=False)

    book = relationship("Book", back_populates="borrowings")
    member = relationship("Member", back_populates="borrowings")

    def __repr__(self):
        return f"<BorrowingRecord(book_id={self.book_id}, member_id={self.member_id}, status={self.status.value})>"
