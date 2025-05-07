import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from bs4 import BeautifulSoup

MODEL_PATH = "components/score_model.pkl"

def train_dummy_model():
    """Create a realistic dummy model with sensible weightings"""
    np.random.seed(42)
    X = np.zeros((100, 5))
    for i in range(100):
        X[i, 0] = np.random.randint(0, 6)   
        X[i, 1] = np.random.randint(0, 15)  
        X[i, 2] = np.random.randint(1, 20)  
        X[i, 3] = np.random.randint(0, 4)    
        X[i, 4] = np.random.randint(0, 2)    

    weights = [8, 7, 5, 5, 10]
    base_score = 40  
    
    weighted_sum = X.dot(weights)
    max_possible = np.array(weights).dot([5, 15, 20, 3, 1])  
    y = base_score + (weighted_sum / max_possible) * 60  
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    
    return model

def load_model():
    if not os.path.exists(MODEL_PATH):
        return train_dummy_model()
    return joblib.load(MODEL_PATH)

def extract_features_from_html(html):
    """Extract website features from HTML content"""
    soup = BeautifulSoup(html, 'html.parser')
    
    ctas = soup.find_all(['button', 'a'])
    cta_count = len(ctas)
    
    h1_count = len(soup.find_all('h1'))
    h2_count = len(soup.find_all('h2'))
    h3_count = len(soup.find_all('h3'))
    hierarchy_score = h1_count * 3 + h2_count * 2 + h3_count
    
    paragraphs = soup.find_all('p')
    p_count = len(paragraphs)
    
    lists = len(soup.find_all(['ul', 'ol']))
    
    testimonials = 1 if soup.find(string=lambda text: text and ('testimonial' in text.lower() or 'review' in text.lower())) else 0

    features = [cta_count, hierarchy_score, p_count, lists, testimonials]
    
    return features

def predict_score(features=None, html=None):
    """
    Predict landing page score using either pre-extracted features or raw HTML
    
    Args:
        features: Optional pre-extracted feature list
        html: Optional HTML string to extract features from
        
    Returns:
        score: Float score from 0-100
    """
    if html and not features:
        features = extract_features_from_html(html)
    
    if not features:
        raise ValueError("Either features or HTML must be provided")
        
    model = load_model()
    X = np.array(features).reshape(1, -1)
    
    if X.shape[1] != 5:
        if X.shape[1] < 5:
            X = np.pad(X, ((0, 0), (0, 5 - X.shape[1])), 'constant')
        else:
            X = X[:, :5]
    
    score = float(model.predict(X)[0])
    
    return max(0, min(100, score))

def train_from_user_data(html, user_score, user_feedback=None):
    """
    Train the model with user-provided data and feedback
    
    Args:
        html: HTML content of the analyzed website
        user_score: User-provided score (0-100)
        user_feedback: Optional dictionary with additional feedback
        
    Returns:
        dict: Results including old and new scores
    """
    features = extract_features_from_html(html)
    
    old_score = predict_score(features=features)
    
    user_data = []
    
    entry = {
        "features": features,
        "user_score": user_score
    }
    
    user_data.append(entry)
    
    model_updated = False
    new_score = old_score
    
    if len(user_data) >= 1:
        X = np.array([entry["features"] for entry in user_data])
        y = np.array([entry["user_score"] for entry in user_data])
        
        model = load_model()

        model.fit(X, y)
        
        joblib.dump(model, MODEL_PATH)
        model_updated = True
        
        new_score = float(model.predict(np.array(features).reshape(1, -1))[0])
        new_score = max(0, min(100, new_score))
    
    return {
        "old_score": old_score,
        "new_score": new_score,
        "model_updated": model_updated,
        "features": features
    }
