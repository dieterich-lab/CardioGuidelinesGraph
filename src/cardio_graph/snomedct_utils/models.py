from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SnapFSN(Base):
    __tablename__ = "snap_fsn"
    conceptId = Column(String(32), primary_key=True)
    term = Column(String(255))
    active = Column(Boolean)
    # Add other columns as needed


class SnapPref(Base):
    __tablename__ = "snap_pref"
    conceptId = Column(String(32), primary_key=True)
    term = Column(String(255))
    active = Column(Boolean)
    # Add other columns as needed


class SnapDescription(Base):
    __tablename__ = "snap_description"
    id = Column(String(32), primary_key=True)
    conceptId = Column(String(32))
    term = Column(String(255))
    active = Column(Boolean)
    # Add other columns as needed


class SnapRelDefFSN(Base):
    __tablename__ = "snap_rel_def_fsn"
    sourceId = Column(String(32), primary_key=True)
    destinationId = Column(String(32), primary_key=True)
    sourceTerm = Column(String(255))
    destinationTerm = Column(String(255))
    # Add other columns as needed


# Additional SNOMED CT relationship models
class SnapRelationship(Base):
    __tablename__ = "snap_relationship"
    id = Column(String(32), primary_key=True)
    sourceId = Column(String(32))
    destinationId = Column(String(32))
    typeId = Column(String(32))
    active = Column(Boolean)
    # Add other columns as needed


class SnapRelDefPref(Base):
    __tablename__ = "snap_rel_def_pref"
    sourceId = Column(String(32), primary_key=True)
    destinationId = Column(String(32), primary_key=True)
    sourceTerm = Column(String(255))
    destinationTerm = Column(String(255))
    # Add other columns as needed


class SnapRelChildFSN(Base):
    __tablename__ = "snap_rel_child_fsn"
    id = Column(String(32), primary_key=True)
    term = Column(String(255))
    conceptID = Column(String(255))
    # Add other columns as needed
