from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    reports = relationship('Report', back_populates='owner')

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))
    extracted_text = Column(Text)
    owner = relationship('User', back_populates='reports')
    parameters = relationship('Parameter', back_populates='report')

class Parameter(Base):
    __tablename__ = 'parameters'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)
    unit = Column(String)
    reference_range = Column(String)
    report_id = Column(Integer, ForeignKey('reports.id'))
    report = relationship('Report', back_populates='parameters')
    status = Column(String) 