# TTA-Database

python -m venv venv
source venv/Scripts/activate

pip install -r requirements.txt

python -m uvicorn app.main:app --reload --port 8001

python -m pytest --cov=app tests/

set -a 
source .env 
set +a  