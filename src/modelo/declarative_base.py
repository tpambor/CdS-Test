import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ.get('CAJA_DB', 'sqlite:///aplicacion.sqlite'), echo='CAJA_DB_DEBUG' in os.environ)
Session = sessionmaker(bind=engine)
Base = declarative_base()
