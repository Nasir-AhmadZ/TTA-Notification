from fastapi import FastAPI, HTTPException
from datetime import datetime
from bson import ObjectId

#from .schemas import EntryStart, Entry, ProjectCreate, Project, EntryUpdate
#from .models import entry_helper, project_helper
from .configurations import db
app = FastAPI(title="Notifications API")

currentUser = "691c8bf8d691e46d00068bf3"

#******************************Notifications endpoints****************************************


# python -m uvicorn app.main:app --reload
