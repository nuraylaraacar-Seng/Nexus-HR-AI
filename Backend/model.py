from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String, index=True)
    department = Column(String)
    salary = Column(Float)
    engagement_survey = Column(float)
    performance_score = Column(String)
    
