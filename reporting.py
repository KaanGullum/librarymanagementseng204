"""Sprint 3 reporting service.

This module is intentionally thin and reads from existing core models:
- Book
- Member
- BorrowingRecord
- User/Role context (indirectly through authenticated MainWindow flow)

No separate fine table exists in the current schema. Penalty is modeled as a
derived reporting value from `days_overdue` when needed for presentation.
"""

from datetime import date, datetime

from sqlalchemy import desc, func, or_

from models import Book, BorrowStatusEnum, BorrowingRecord, Member


def sync_overdue_records(db, reference_time=None):
    """Ensure borrowing statuses reflect due dates."""
    now = reference_time or datetime.utcnow()

    marked_overdue = (
        db.query(BorrowingRecord)
        .filter(
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.status == BorrowStatusEnum.ACTIVE,
            BorrowingRecord.due_date < now,
        )
        .update({BorrowingRecord.status: BorrowStatusEnum.OVERDUE}, synchronize_session=False)
    )

    reverted_to_active = (
        db.query(BorrowingRecord)
        .filter(
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.status == BorrowStatusEnum.OVERDUE,
            BorrowingRecord.due_date >= now,
        )
        .update({BorrowingRecord.status: BorrowStatusEnum.ACTIVE}, synchronize_session=False)
    )

    if marked_overdue or reverted_to_active:
        db.commit()

    return marked_overdue + reverted_to_active


def estimate_penalty(days_overdue, daily_rate=0.0):
    """Return a derived penalty estimate (not persisted in DB)."""
    safe_days = max(0, int(days_overdue))
    safe_rate = max(0.0, float(daily_rate))
    return round(safe_days * safe_rate, 2)


def fetch_dashboard_metrics(db):
    sync_overdue_records(db)
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    total_titles = db.query(func.count(Book.id)).scalar() or 0
    available_copies = db.query(func.coalesce(func.sum(Book.stock), 0)).scalar() or 0
    total_members = db.query(func.count(Member.id)).scalar() or 0

    active_loans = (
        db.query(func.count(BorrowingRecord.id))
        .filter(
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.status.in_([BorrowStatusEnum.ACTIVE, BorrowStatusEnum.OVERDUE]),
        )
        .scalar()
        or 0
    )

    overdue_loans = (
        db.query(func.count(BorrowingRecord.id))
        .filter(
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.status == BorrowStatusEnum.OVERDUE,
        )
        .scalar()
        or 0
    )

    returned_this_month = (
        db.query(func.count(BorrowingRecord.id))
        .filter(
            BorrowingRecord.return_date.is_not(None),
            BorrowingRecord.return_date >= month_start,
            BorrowingRecord.return_date <= now,
        )
        .scalar()
        or 0
    )

    top_books_query = (
        db.query(Book.title, func.count(BorrowingRecord.id).label("borrow_count"))
        .join(BorrowingRecord, BorrowingRecord.book_id == Book.id)
        .group_by(Book.id)
        .order_by(desc("borrow_count"), Book.title.asc())
        .limit(5)
        .all()
    )
    top_books = [{"title": row.title, "borrow_count": row.borrow_count} for row in top_books_query]

    recent_records = (
        db.query(BorrowingRecord)
        .order_by(BorrowingRecord.borrow_date.desc())
        .limit(8)
        .all()
    )
    recent_activity = []
    for record in recent_records:
        member_name = "Unknown Member"
        if record.member:
            member_name = f"{record.member.first_name} {record.member.last_name}"

        book_title = record.book.title if record.book else "Unknown Book"
        recent_activity.append(
            {
                "member": member_name,
                "book": book_title,
                "borrowed_on": record.borrow_date,
                "due_date": record.due_date,
                "status": record.status,
            }
        )

    overdue_preview = fetch_overdue_records(db, min_days_overdue=1, limit=8)

    return {
        "total_titles": total_titles,
        "available_copies": available_copies,
        "total_members": total_members,
        "active_loans": active_loans,
        "overdue_loans": overdue_loans,
        "returned_this_month": returned_this_month,
        "top_books": top_books,
        "recent_activity": recent_activity,
        "overdue_preview": overdue_preview,
    }


def fetch_overdue_records(db, search_text="", min_days_overdue=1, limit=None):
    """Read overdue borrowings by joining borrowing, member, and book models."""
    sync_overdue_records(db)
    now = datetime.utcnow()

    query = (
        db.query(BorrowingRecord)
        .join(Member, BorrowingRecord.member_id == Member.id)
        .join(Book, BorrowingRecord.book_id == Book.id)
        .filter(
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.status == BorrowStatusEnum.OVERDUE,
            BorrowingRecord.due_date < now,
        )
        .order_by(BorrowingRecord.due_date.asc())
    )

    term = (search_text or "").strip()
    if term:
        like_term = f"%{term}%"
        query = query.filter(
            or_(
                Member.first_name.ilike(like_term),
                Member.last_name.ilike(like_term),
                Member.email.ilike(like_term),
                Book.title.ilike(like_term),
                Book.isbn.ilike(like_term),
            )
        )

    if limit:
        query = query.limit(limit)

    min_days = max(1, int(min_days_overdue))
    rows = []
    for record in query.all():
        member_name = "Unknown Member"
        member_email = ""
        if record.member:
            member_name = f"{record.member.first_name} {record.member.last_name}"
            member_email = record.member.email or ""

        days_overdue = max(1, (now.date() - record.due_date.date()).days)
        if days_overdue < min_days:
            continue

        rows.append(
            {
                "record_id": record.id,
                "member_name": member_name,
                "member_email": member_email,
                "book_title": record.book.title if record.book else "Unknown Book",
                "isbn": record.book.isbn if record.book else "",
                "borrow_date": record.borrow_date,
                "due_date": record.due_date,
                "days_overdue": days_overdue,
                "estimated_penalty": estimate_penalty(days_overdue),
                "status": record.status,
            }
        )

    return rows


def validate_summary_range(start_date, end_date, max_days=366):
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        return False, "Please choose a valid start and end date."

    if start_date > end_date:
        return False, "Start date cannot be after end date."

    if end_date > datetime.utcnow().date():
        return False, "End date cannot be in the future."

    if (end_date - start_date).days > max_days:
        return False, f"Date range cannot exceed {max_days} days."

    return True, ""


def fetch_borrowing_summary(db, start_date, end_date):
    sync_overdue_records(db)
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    issued_count = (
        db.query(func.count(BorrowingRecord.id))
        .filter(BorrowingRecord.borrow_date >= start_dt, BorrowingRecord.borrow_date <= end_dt)
        .scalar()
        or 0
    )

    returned_count = (
        db.query(func.count(BorrowingRecord.id))
        .filter(BorrowingRecord.return_date.is_not(None))
        .filter(BorrowingRecord.return_date >= start_dt, BorrowingRecord.return_date <= end_dt)
        .scalar()
        or 0
    )

    overdue_started_in_range = (
        db.query(func.count(BorrowingRecord.id))
        .filter(
            BorrowingRecord.status == BorrowStatusEnum.OVERDUE,
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.due_date >= start_dt,
            BorrowingRecord.due_date <= end_dt,
        )
        .scalar()
        or 0
    )

    current_open_loans = (
        db.query(func.count(BorrowingRecord.id))
        .filter(
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.status.in_([BorrowStatusEnum.ACTIVE, BorrowStatusEnum.OVERDUE]),
        )
        .scalar()
        or 0
    )

    new_members = (
        db.query(func.count(Member.id))
        .filter(Member.membership_date >= start_dt, Member.membership_date <= end_dt)
        .scalar()
        or 0
    )

    top_book_row = (
        db.query(Book.title, func.count(BorrowingRecord.id).label("borrow_count"))
        .join(BorrowingRecord, BorrowingRecord.book_id == Book.id)
        .filter(BorrowingRecord.borrow_date >= start_dt, BorrowingRecord.borrow_date <= end_dt)
        .group_by(Book.id)
        .order_by(desc("borrow_count"), Book.title.asc())
        .first()
    )

    return_rate = round((returned_count / issued_count) * 100, 1) if issued_count else 0.0

    return {
        "issued_count": issued_count,
        "returned_count": returned_count,
        "overdue_started_in_range": overdue_started_in_range,
        "current_open_loans": current_open_loans,
        "new_members": new_members,
        "return_rate": return_rate,
        "top_book_title": top_book_row.title if top_book_row else "N/A",
        "top_book_borrows": top_book_row.borrow_count if top_book_row else 0,
    }
