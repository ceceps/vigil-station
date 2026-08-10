#!/bin/bash
# PostgreSQL Database Setup Script for Mission Planning Assistant

echo "🚀 Setting up PostgreSQL database for Mission Planning Assistant..."

# Database configuration
DB_NAME="mission_planning"
DB_USER="mission_user"
DB_PASSWORD="mission_password"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL first."
    echo ""
    echo "Installation instructions:"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "  macOS: brew install postgresql"
    echo "  Windows: Download from https://www.postgresql.org/download/windows/"
    exit 1
fi

echo "✅ PostgreSQL is installed"

# Check if PostgreSQL service is running
if ! pg_isready &> /dev/null; then
    echo "⚠️  PostgreSQL service is not running. Starting it..."
    
    # Try to start PostgreSQL based on OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start postgresql
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start postgresql
    fi
    
    sleep 2
    
    if ! pg_isready &> /dev/null; then
        echo "❌ Failed to start PostgreSQL service. Please start it manually."
        exit 1
    fi
fi

echo "✅ PostgreSQL service is running"

# Create database and user
echo "📦 Creating database and user..."

sudo -u postgres psql <<EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

\c $DB_NAME

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO $DB_USER;
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database '$DB_NAME' and user '$DB_USER' created successfully"
else
    echo "❌ Failed to create database or user"
    exit 1
fi

# Run Alembic migrations
echo "🔄 Running database migrations..."

cd "$(dirname "$0")"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "⚠️  Alembic not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Run migrations
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully"
else
    echo "❌ Failed to run migrations"
    exit 1
fi

echo ""
echo "🎉 PostgreSQL setup complete!"
echo ""
echo "Database connection details:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo ""
echo "Connection string for .env file:"
echo "  DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
echo ""
echo "Next steps:"
echo "  1. Update your .env file with the connection string above"
echo "  2. Run: python -m app.main"
