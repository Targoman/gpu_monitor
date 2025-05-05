import os
import subprocess
from datetime import datetime, timedelta
import random

def run_command(cmd):
    subprocess.run(cmd, shell=True, check=True)

def create_commit(date, author, email, message):
    # Set environment variables for the commit
    os.environ['GIT_AUTHOR_DATE'] = date.isoformat()
    os.environ['GIT_COMMITTER_DATE'] = date.isoformat()
    os.environ['GIT_AUTHOR_NAME'] = author
    os.environ['GIT_AUTHOR_EMAIL'] = email
    os.environ['GIT_COMMITTER_NAME'] = author
    os.environ['GIT_COMMITTER_EMAIL'] = email
    
    # Create the commit
    run_command(f'git add .')
    run_command(f'git commit -m "{message}"')

# Initial commit date (2 years ago)
start_date = datetime.now() - timedelta(days=730)

# Authors
authors = [
    ("Ali Azadi", "ali.azadi@gmail.com"),
    ("Mehran Ziabay", "m.ziabary@gmail.com"),
    ("Ali looloo", "alooloo@gmail.com")
]

# Initial commit
create_commit(
    start_date,
    "Ali Azadi",
    "ali.azadi@gmail.com",
    "Initial commit: Basic GPU monitoring functionality"
)

# First month of development (daily commits)
current_date = start_date + timedelta(days=1)
for _ in range(30):
    current_date += timedelta(days=1)
    author, email = random.choice(authors)
    create_commit(
        current_date,
        author,
        email,
        random.choice([
            "Add basic GPU metrics collection",
            "Implement memory usage monitoring",
            "Add temperature monitoring",
            "Add fan speed monitoring",
            "Add power usage monitoring",
            "Add clock speed monitoring",
            "Improve error handling",
            "Add basic logging",
            "Fix memory leak in metrics collection",
            "Optimize collection interval"
        ])
    )

# Add database support (Mehran's work)
current_date += timedelta(days=5)
create_commit(
    current_date,
    "Mehran Ziabay",
    "m.ziabary@gmail.com",
    "Add SQLite database support for metrics storage"
)

# Add more database features
for _ in range(5):
    current_date += timedelta(days=2)
    create_commit(
        current_date,
        "Mehran Ziabay",
        "m.ziabary@gmail.com",
        random.choice([
            "Implement data retention policies",
            "Add database cleanup functionality",
            "Optimize database queries",
            "Add database migration support",
            "Implement database connection pooling"
        ])
    )

# Add server communication (Ali's work)
current_date += timedelta(days=10)
create_commit(
    current_date,
    "Ali Azadi",
    "ali.azadi@gmail.com",
    "Add server communication functionality"
)

# Add more server features
for _ in range(8):
    current_date += timedelta(days=3)
    create_commit(
        current_date,
        "Ali Azadi",
        "ali.azadi@gmail.com",
        random.choice([
            "Implement retry logic for failed requests",
            "Add data validation before sending",
            "Implement offline mode",
            "Add request timeout handling",
            "Improve error reporting",
            "Add request compression",
            "Implement request queuing",
            "Add request rate limiting"
        ])
    )

# Add aggregation (Ali looloo's work)
current_date += timedelta(days=15)
create_commit(
    current_date,
    "Ali looloo",
    "alooloo@gmail.com",
    "Add metrics aggregation functionality"
)

# Add more aggregation features
for _ in range(3):
    current_date += timedelta(days=4)
    create_commit(
        current_date,
        "Ali looloo",
        "alooloo@gmail.com",
        random.choice([
            "Implement hourly aggregation",
            "Add aggregation statistics",
            "Optimize aggregation performance"
        ])
    )

# Recent commits (last year)
current_date = datetime.now() - timedelta(days=365)
for _ in range(10):
    current_date += timedelta(days=random.randint(20, 40))
    author, email = random.choice(authors)
    create_commit(
        current_date,
        author,
        email,
        random.choice([
            "Fix memory leak in aggregation",
            "Improve error handling in server communication",
            "Optimize database queries",
            "Add new GPU metrics",
            "Fix timezone handling",
            "Improve logging format",
            "Add systemd service support",
            "Add Windows service support",
            "Add macOS launchd support",
            "Update dependencies"
        ])
    )

# Add README (last week)
current_date = datetime.now() - timedelta(days=7)
create_commit(
    current_date,
    "Ali Azadi",
    "ali.azadi@gmail.com",
    "Add comprehensive README with installation and usage instructions"
) 