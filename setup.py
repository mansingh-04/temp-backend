from setuptools import setup, find_packages

setup(
    name="website-analyzer",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask==2.0.1",
        "werkzeug==2.0.2",
        "flask-cors==3.0.10",
        "requests==2.26.0",
        "beautifulsoup4==4.9.3",
        "python-dotenv==0.19.0",
        "google-generativeai==0.3.1",
        "pytesseract",
        "Pillow",
        "scikit-learn==1.3.2",
        "joblib==1.0.1",
        "numpy==1.24.3",
        "gunicorn==20.1.0"
    ],
) 