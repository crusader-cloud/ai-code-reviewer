@echo off
echo Setting up AI PR Reviewer...

REM Check Python version
python --version

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit .env file with your credentials!
)

REM Initialize database
echo Initializing database...
python -c "from app.db.session import Base, engine; Base.metadata.create_all(bind=engine)"

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your API keys and GitHub credentials
echo 2. Run: uvicorn app.main:app --reload
echo 3. Open http://localhost:8000 in your browser
echo 4. Visit http://localhost:8000/docs for API documentation
echo.
pause
