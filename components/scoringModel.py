import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from bs4 import BeautifulSoup
import warnings

# Check if we're in Vercel environment
is_vercel = os.environ.get('VERCEL') == '1'
MODEL_PATH = "components/score_model.pkl"

def train_dummy_model():
    """Create a realistic dummy model with sensible weightings"""
    if is_vercel:
        print("Skipping model training in Vercel environment")
        return create_simple_model()
        
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
    
    try:
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(model, MODEL_PATH)
    except Exception as e:
        print(f"Warning: Could not save model: {str(e)}")
    
    return model

def create_simple_model():
    """Create a very simple model for serverless environments"""
    class SimpleModel:
        def predict(self, X):
            # Simple scoring logic based on features
            # [cta_count, hierarchy_score, p_count, lists, testimonials]
            scores = []
            for features in X:
                base_score = 50
                if len(features) >= 5:
                    cta_bonus = min(features[0] * 2, 10)  # Max 10 points for CTAs
                    hierarchy_bonus = min(features[1] * 0.5, 15)  # Max 15 points for hierarchy
                    content_bonus = min(features[2] * 0.25, 10)  # Max 10 points for paragraphs
                    list_bonus = min(features[3] * 2, 5)  # Max 5 points for lists
                    trust_bonus = 10 if features[4] > 0 else 0  # 10 points for testimonials
                    
                    score = base_score + cta_bonus + hierarchy_bonus + content_bonus + list_bonus + trust_bonus
                    scores.append(min(100, max(0, score)))
                else:
                    scores.append(50)  # Default score
            return scores
    
    return SimpleModel()

def load_model():
    """Load the model or create a simple one if necessary"""
    if is_vercel:
        return create_simple_model()
        
    if not os.path.exists(MODEL_PATH):
        return train_dummy_model()
        
    try:
        return joblib.load(MODEL_PATH)
    except Exception as e:
        print(f"Error loading model: {str(e)}, creating simple one")
        return create_simple_model() 