from sqlalchemy import Column, Integer, String, Date, Boolean, Float, ForeignKey, Time, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Cohort(Base):
    __tablename__ = 'Cohort'
    
    Cohort_id = Column(Integer, primary_key=True)
    CohortName = Column(String, unique=True)
    DOB = Column(Date)

    Mice = relationship("MouseData", back_populates="Cohort")
    Groups = relationship("Group", back_populates="Cohort")

class Group(Base):
    __tablename__ = 'Group'
    
    Number = Column(Integer, primary_key=True)
    Cohort_id = Column(Integer, ForeignKey('Cohort.Cohort_id'))
    Rapamycin = Column(String)
    HSCs = Column(String)
    Senolytic = Column(String)
    Mobilization = Column(String)
    AAV9 = Column(String)

    Cohort = relationship("Cohort", back_populates="Groups")
    Mice = relationship("MouseData", back_populates="Group")
    
    # __table_args__ = (
    #     CheckConstraint(Rapamycin.in_(['naive', 'mock', 'active'])),
    #     CheckConstraint(HSCs.in_(['naive', 'mock', 'active'])),
    #     CheckConstraint(Senolytic.in_(['naive', 'mock', 'active'])),
    # )

class MouseData(Base):
    __tablename__ = 'MouseData'
    
    EarTag = Column(Integer, primary_key=True)
    Sex = Column(String)
    DOB = Column(Date)
    DOD = Column(Date, nullable=True)
    DeathDetails = Column(String, nullable=True)
    DeathNotes = Column(String, nullable=True)
    Necropsy = Column(Boolean, nullable=True)
    Stagger = Column(Integer, nullable=True)
    Group_Number = Column(Integer, ForeignKey('Group.Number'), nullable=True)
    Cohort_id = Column(Integer, ForeignKey('Cohort.Cohort_id'), nullable=True)
    
    Group = relationship("Group", back_populates="Mice")
    Cohort = relationship("Cohort", back_populates="Mice")
    Weights = relationship("Weight", back_populates="Mouse")
    Rotarod = relationship("Rotarod", back_populates="Mouse")
    GripStrength = relationship("GripStrength", back_populates="Mouse")

class Weight(Base):
    __tablename__ = 'Weights'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    EarTag = Column(Integer, ForeignKey('MouseData.EarTag'))
    Date = Column(Date)
    Baseline = Column(Boolean)
    Weight = Column(Float)
    
    Mouse = relationship("MouseData", back_populates="Weights")

class Rotarod(Base):
    __tablename__ = 'Rotarod'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    EarTag = Column(Integer, ForeignKey('MouseData.EarTag'))
    Baseline = Column(Boolean)
    Cull_date = Column(Date)
    Date = Column(Date)
    Time = Column(Time)
    Speed = Column(Float)
    
    Mouse = relationship("MouseData", back_populates="Rotarod")

class GripStrength(Base):
    __tablename__ = 'GripStrength'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    EarTag = Column(Integer, ForeignKey('MouseData.EarTag'))
    Date = Column(Date)
    ValueIndex = Column(Integer)
    Value = Column(Float)
    
    Mouse = relationship("MouseData", back_populates="GripStrength") 