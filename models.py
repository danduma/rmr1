from sqlalchemy import Column, Integer, String, Date, Boolean, Float, ForeignKey, Time, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Cohort(Base):
    __tablename__ = 'cohort'
    
    cohort_id = Column(Integer, primary_key=True)
    cohort_name = Column(String, unique=True)
    dob = Column(Date)
    
    mice = relationship("MouseData", back_populates="cohort")
    groups = relationship("Group", back_populates="cohort")

class Group(Base):
    __tablename__ = 'group'
    
    number = Column(Integer, primary_key=True)
    cohort_id = Column(Integer, ForeignKey('cohort.cohort_id'))
    rapamycin = Column(String)
    hscs = Column(String)
    senolytic = Column(String)
    mobilization = Column(String)
    aav9 = Column(String)
    
    cohort = relationship("Cohort", back_populates="groups")
    mice = relationship("MouseData", back_populates="group")
    
    __table_args__ = (
        CheckConstraint(rapamycin.in_(['naive', 'mock', 'active'])),
        CheckConstraint(hscs.in_(['naive', 'mock', 'active'])),
        CheckConstraint(senolytic.in_(['naive', 'mock', 'active'])),
    )

class MouseData(Base):
    __tablename__ = 'mouse_data'
    
    ear_tag = Column(Integer, primary_key=True)
    sex = Column(String)
    dob = Column(Date)
    dod = Column(Date, nullable=True)
    death_details = Column(String, nullable=True)
    death_notes = Column(String, nullable=True)
    necropsy = Column(Boolean, nullable=True)
    stagger = Column(Integer, nullable=True)
    group_number = Column(Integer, ForeignKey('group.number'), nullable=True)
    cohort_id = Column(Integer, ForeignKey('cohort.cohort_id'), nullable=True)
    
    group = relationship("Group", back_populates="mice")
    cohort = relationship("Cohort", back_populates="mice")
    weights = relationship("Weight", back_populates="mouse")
    rotarod_results = relationship("Rotarod", back_populates="mouse")
    grip_strength_results = relationship("GripStrength", back_populates="mouse")

class Weight(Base):
    __tablename__ = 'weights'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ear_tag = Column(Integer, ForeignKey('mouse_data.ear_tag'))
    date = Column(Date)
    baseline = Column(Boolean)
    weight = Column(Float)
    
    mouse = relationship("MouseData", back_populates="weights")

class Rotarod(Base):
    __tablename__ = 'rotarod'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ear_tag = Column(Integer, ForeignKey('mouse_data.ear_tag'))
    baseline = Column(Boolean)
    cull_date = Column(Date)
    date = Column(Date)
    time = Column(Time)
    speed = Column(Float)
    
    mouse = relationship("MouseData", back_populates="rotarod_results")

class GripStrength(Base):
    __tablename__ = 'grip_strength'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ear_tag = Column(Integer, ForeignKey('mouse_data.ear_tag'))
    date = Column(Date)
    value_index = Column(Integer)
    value = Column(Float)
    
    mouse = relationship("MouseData", back_populates="grip_strength_results") 