from models import *
from app import db

# Create all tables
db.drop_all()
db.create_all()