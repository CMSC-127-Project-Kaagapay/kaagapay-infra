from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os

from models.entities.base import Base

from models.entities.volunteers import VolunteerEntity
from models.entities.programs import ProgramEntity
from models.entities.volunteerApplications import VolunteerApplicationEntity
from models.entities.alliedOffices import AlliedOfficeEntity
from models.entities.contactLines import ContactLineEntity
from models.entities.notifications import NotificationEntity
from models.entities.ticketStatusLogs import TicketStatusLogEntity
from models.entities.incidentTickets import IncidentTicketEntity

# Load environment variables from .env
load_dotenv()

# Check if a full DATABASE_URL is provided (e.g., for local testing)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to fetching individual variables (e.g., for Supabase)
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    PORT = os.getenv("port")
    DBNAME = os.getenv("dbname")

    # Construct the SQLAlchemy connection string
    DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

# If using Transaction Pooler or Session Pooler, we want to ensure we disable SQLAlchemy client side pooling -
engine = create_engine(DATABASE_URL, poolclass=NullPool)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Function to create tables (call this on application startup)
def create_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Test the connection
try:
    with engine.connect() as connection:
        # create_tables()
        print("Connection successful!")
except Exception as e:
    print(f"Failed to connect: {e}")
