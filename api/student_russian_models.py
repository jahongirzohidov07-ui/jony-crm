"""Private Russian course practice; never awards XP or coins."""
from sqlalchemy import Column, ForeignKey, Integer, String
from database import Base


class StudentRussianProgress(Base):
    __tablename__ = "student_russian_progress"

    student_id = Column(Integer, ForeignKey("students.id"), primary_key=True)
    lesson_no = Column(Integer, primary_key=True)
    kind = Column(String(16), primary_key=True)
    best_score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    attempts = Column(Integer, nullable=False)
