from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Boolean

Base = declarative_base()

class SnapFSN(Base):
    __tablename__ = 'snap_fsn'
    conceptId = Column(String(32), primary_key=True)
    term = Column(String(255))
    active = Column(Boolean)
    # Add other columns as needed

class SnapPref(Base):
    __tablename__ = 'snap_pref'
    conceptId = Column(String(32), primary_key=True)
    term = Column(String(255))
    active = Column(Boolean)
    # Add other columns as needed

class SnapDescription(Base):
    __tablename__ = 'snap_description'
    id = Column(String(32), primary_key=True)
    conceptId = Column(String(32))
    term = Column(String(255))
    active = Column(Boolean)
    # Add other columns as needed

class SnapRelDefFSN(Base):
    __tablename__ = 'snap_rel_def_fsn'
    id = Column(Integer, primary_key=True)
    sourceId = Column(String(32))
    sourceTerm = Column(String(255))
    destinationId = Column(String(32))
    destinationTerm = Column(String(255))
    # Add other columns as needed
