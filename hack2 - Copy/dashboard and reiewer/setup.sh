#!/bin/bash

echo "🚀 Setting up AI PR Reviewer..."

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python -m venv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your credentials!"
fi

# Initialize database
echo "🗄️  Initializing database..."
python -c "from app.db.session import Base, engine; Base.metadata.create_all(bind=engine)"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys and GitHub credentials"
echo "2. Run: uvicorn app.main:app --reload"
echo "3. Open http://localhost:8000 in your browser"
echo "4. Visit http://localhost:8000/docs for API documentation"
echo ""
