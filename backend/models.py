from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Time, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from database import Base

# Association table for Interaction <-> Material (Many-to-Many)
interaction_materials = Table(
    'interaction_materials',
    Base.metadata,
    Column('interaction_id', Integer, ForeignKey('interactions.id', ondelete='CASCADE'), primary_key=True),
    Column('material_id', Integer, ForeignKey('materials.id', ondelete='CASCADE'), primary_key=True)
)

# Association table for Interaction <-> Sample (Many-to-Many)
interaction_samples = Table(
    'interaction_samples',
    Base.metadata,
    Column('interaction_id', Integer, ForeignKey('interactions.id', ondelete='CASCADE'), primary_key=True),
    Column('sample_id', Integer, ForeignKey('samples.id', ondelete='CASCADE'), primary_key=True)
)

class HCP(Base):
    __tablename__ = 'hcps'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    specialty = Column(String(100), nullable=False)
    clinic = Column(String(200), nullable=False)
    contact_number = Column(String(50), nullable=True)
    email = Column(String(100), nullable=False, unique=True)
    preferences = Column(Text, nullable=True)  # JSON or text containing preferences

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")
    email_logs = relationship("EmailLog", back_populates="hcp", cascade="all, delete-orphan")


class Material(Base):
    __tablename__ = 'materials'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True)
    type = Column(String(50), nullable=False)  # Brochure, Clinical Trial, Product Brief
    file_size = Column(String(20), nullable=True)
    url = Column(String(255), nullable=True)

    interactions = relationship("Interaction", secondary=interaction_materials, back_populates="materials")


class Sample(Base):
    __tablename__ = 'samples'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    interactions = relationship("Interaction", secondary=interaction_samples, back_populates="samples")


class Interaction(Base):
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey('hcps.id', ondelete='CASCADE'), nullable=False)
    interaction_type = Column(String(50), nullable=False, default="Meeting")  # Meeting, Call, Email, Webcast
    date = Column(String(20), nullable=False)  # Store as YYYY-MM-DD or MM/DD/YYYY
    time = Column(String(20), nullable=False)  # Store as HH:MM or HH:MM AM/PM
    attendees = Column(Text, nullable=True)  # Comma-separated or JSON list of attendee names
    topics_discussed = Column(Text, nullable=True)
    sentiment = Column(String(20), nullable=True)  # Positive, Neutral, Negative
    outcomes = Column(Text, nullable=True)
    follow_up_actions = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="Draft")  # Draft or Logged

    hcp = relationship("HCP", back_populates="interactions")
    materials = relationship("Material", secondary=interaction_materials, back_populates="interactions")
    samples = relationship("Sample", secondary=interaction_samples, back_populates="interactions")


class EmailLog(Base):
    __tablename__ = 'email_logs'

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey('hcps.id', ondelete='CASCADE'), nullable=False)
    subject = Column(String(200), nullable=False)
    materials_sent = Column(Text, nullable=False)  # Comma-separated list of materials
    timestamp = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="Sent")  # Sent, Pending, Failed

    hcp = relationship("HCP", back_populates="email_logs")
