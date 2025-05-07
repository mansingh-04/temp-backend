#!/usr/bin/env python3
import os
import sys
import subprocess

def check_directory_structure():
    print("Current directory:", os.getcwd())
    print("Directory contents:", os.listdir())
    
    if os.path.exists("backend"):
        print("Backend directory exists. Contents:", os.listdir("backend"))
    else:
        print("Backend directory not found!")
        
    if os.path.exists("backend/app.py"):
        print("app.py found in backend directory.")
    else:
        print("app.py NOT found in backend directory!")

    if os.path.exists("components"):
        print("Components directory exists. Contents:", os.listdir("components"))
    else:
        print("Components directory not found!")

def check_environment():
    print("Environment variables:")
    for key, value in os.environ.items():
        if key in ['PORT', 'PYTHONPATH', 'RAILWAY_ENVIRONMENT', 'GEMINI_API_KEY']:
            if key == 'GEMINI_API_KEY' and value:
                print(f"{key}: [REDACTED]")
            else:
                print(f"{key}: {value}")

def start_app():
    try:
        check_directory_structure()
        check_environment()
        
        if not os.path.exists("backend/app.py"):
            print("Cannot start application: app.py not found!")
            sys.exit(1)
            
        print("Starting gunicorn server...")
        cmd = ["gunicorn", "--chdir", "backend", "app:app", "--bind", f"0.0.0.0:{os.environ.get('PORT', '5050')}", "--log-level", "debug"]
        print("Running command:", " ".join(cmd))
        subprocess.run(cmd)
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    start_app() 