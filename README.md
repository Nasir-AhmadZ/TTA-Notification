# TTA-Database

python -m venv venv
source venv/Scripts/activate

pip install -r requirements.txt

python -m uvicorn app.main:app --reload --port 8001


set -a 
source .env 
set +a  