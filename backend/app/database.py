import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the Cloud SQL Python Connector and its interface
from google.cloud.sql.connector import Connector, IPTypes

# Import the Base from your models file to be used here
from models import Base

# This function uses the official Google Cloud Connector to create a database engine.
def get_engine():
    """
    Initializes a connection pool for a Cloud SQL instance of Postgres.
    Uses the Cloud SQL Python Connector package.
    """
    # These environment variables are set by the gcloud run deploy command
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASSWORD"]
    db_name = os.environ["DB_NAME"]
    instance_connection_name = os.environ["DB_INSTANCE_CONNECTION_NAME"]

    # The Cloud SQL Python Connector automatically handles the secure connection.
    connector = Connector()

    # This function is called by SQLAlchemy to create a new database connection
    def getconn():
        # Use PUBLIC IP for connecting from your local machine, and PRIVATE IP for Cloud Run
        # For this project, PUBLIC is sufficient and simpler.
        conn = connector.connect(
            instance_connection_name,
            "pg8000",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=IPTypes.PUBLIC,
        )
        return conn

    # The create_engine function uses our 'getconn' function to create all new connections.
    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
    return engine

# Create the engine when the application starts
engine = get_engine()

# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

