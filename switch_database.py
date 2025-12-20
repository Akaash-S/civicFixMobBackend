#!/usr/bin/env python3
"""
Database Configuration Switcher
Easily switch between SQLite (development) and RDS (production)
"""

import os
import shutil
from pathlib import Path

def backup_env():
    """Backup current .env file"""
    if os.path.exists('.env'):
        shutil.copy('.env', '.env.backup')
        print("Backed up current .env to .env.backup")

def switch_to_sqlite():
    """Switch to SQLite for development"""
    print("Switching to SQLite for development...")
    
    backup_env()
    
    # Read current .env
    env_content = []
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.readlines()
    
    # Update database configuration
    new_content = []
    for line in env_content:
        if line.startswith('DATABASE_URL=postgresql'):
            new_content.append('# ' + line)  # Comment out RDS
            new_content.append('DATABASE_URL=sqlite:///civicfix.db\n')
        elif line.startswith('DATABASE_URL=sqlite'):
            new_content.append(line)  # Keep SQLite
        elif line.startswith('# DATABASE_URL=sqlite'):
            new_content.append('DATABASE_URL=sqlite:///civicfix.db\n')  # Uncomment SQLite
        elif line.startswith('DB_HOST=') or line.startswith('DB_PORT=') or line.startswith('DB_NAME=') or line.startswith('DB_USER=') or line.startswith('DB_PASSWORD='):
            new_content.append('# ' + line)  # Comment out RDS settings
        else:
            new_content.append(line)
    
    # Write updated .env
    with open('.env', 'w') as f:
        f.writelines(new_content)
    
    print("SUCCESS: Switched to SQLite")
    print("Database file: civicfix.db")
    print("\nTo initialize the database:")
    print("  python init_database.py")

def switch_to_rds():
    """Switch to RDS for production"""
    print("Switching to RDS...")
    
    backup_env()
    
    # Read current .env
    env_content = []
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.readlines()
    
    # Update database configuration
    new_content = []
    for line in env_content:
        if line.startswith('DATABASE_URL=sqlite'):
            new_content.append('# ' + line)  # Comment out SQLite
        elif line.startswith('# DATABASE_URL=postgresql'):
            new_content.append(line[2:])  # Uncomment RDS
        elif line.startswith('# DB_HOST=') or line.startswith('# DB_PORT=') or line.startswith('# DB_NAME=') or line.startswith('# DB_USER=') or line.startswith('# DB_PASSWORD='):
            new_content.append(line[2:])  # Uncomment RDS settings
        else:
            new_content.append(line)
    
    # Write updated .env
    with open('.env', 'w') as f:
        f.writelines(new_content)
    
    print("SUCCESS: Switched to RDS")
    print("\nTo test RDS connection:")
    print("  python fix_rds_connection.py")

def show_current_config():
    """Show current database configuration"""
    print("Current database configuration:")
    print("-" * 40)
    
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if 'DATABASE_URL=' in line and not line.strip().startswith('#'):
                    if 'sqlite' in line:
                        print("Database: SQLite (Development)")
                        print(f"File: {line.split('=')[1].strip()}")
                    elif 'postgresql' in line:
                        print("Database: PostgreSQL (RDS)")
                        print(f"URL: {line.split('=')[1].strip()}")
                    break
            else:
                print("No DATABASE_URL found in .env")
    else:
        print(".env file not found")

def main():
    print("=" * 50)
    print("CivicFix Database Configuration Switcher")
    print("=" * 50)
    
    show_current_config()
    
    print("\nOptions:")
    print("1. Switch to SQLite (Development)")
    print("2. Switch to RDS (Production)")
    print("3. Show current configuration")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            switch_to_sqlite()
        elif choice == '2':
            switch_to_rds()
        elif choice == '3':
            show_current_config()
        elif choice == '4':
            print("Goodbye!")
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    main()