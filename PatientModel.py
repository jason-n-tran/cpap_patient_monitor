from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Patient(Base):
    __tablename__ = 'patients'

    room_number = Column(Integer, primary_key=True)
    patient_mrn = Column(Integer)
    patient_name = Column(String)
    CPAP_pressure = Column(Text)  # Store as JSON string
    breath_rate = Column(Text)  # Store as JSON string
    apnea_count = Column(Text)  # Store as JSON string
    flow_image = Column(Text)  # Store as JSON string
    timestamp = Column(Text)  # Store as JSON string


# Database setup
engine = create_engine('sqlite:///patients.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
