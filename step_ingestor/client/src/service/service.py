import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import g

from step_ingestor.db import Base, db_url
from step_ingestor.dto import ActivitySummaryDTO, StepSampleDTO
from step_ingestor.interfaces import StepIngestorRepository, AccessLink
from step_ingestor.adapters import Adapter
from step_ingestor.services.ingestion import IngestionService

api_interface = AccessLink(api_url=os.environ["POLAR_API_URL"],
                           auth_url=os.environ["POLAR_AUTHORIZATION_URL"],
                           token_url=os.environ["POLAR_ACCESS_TOKEN_URL"],
                           client_id=os.environ["POLAR_CLIENT_ID"],
                           client_secret=os.environ["POLAR_CLIENT_SECRET"],
                           redirect_url=os.environ["POLAR_CALLBACK_URL"])

data_provider = Adapter(adaptee=api_interface,
                        dto_dact=ActivitySummaryDTO,
                        dto_step=StepSampleDTO)

engine = create_engine(db_url, pool_pre_ping=True)
Base.metadata.create_all(engine)
session_factory = sessionmaker(bind=engine)

def get_db_session():
    if "db_session" not in g:
        g.db_session = session_factory()
    return g.db_session

def get_repo():
    return StepIngestorRepository(session=get_db_session(), autocommit=True)

def get_service():
    return IngestionService(provider=data_provider, repo=get_repo())
