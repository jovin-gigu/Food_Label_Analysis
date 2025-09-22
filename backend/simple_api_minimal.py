"""
Simple Flask API Server for Food Scanner & Health Analysis Application
Minimal version to handle encoding issues
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000","https://food-label-analysis.vercel.app"])

# Global variables
food_db = None
model_loaded = False

def load_data_safely():
    """Load data with proper encoding handling"""
    global food_db, model_loaded
    
    try:
        logger.info("Loading data...")
        
        # Try to load food database with different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                food_db = pd.read_csv("data/food_database.csv", encoding=encoding)
                logger.info(f"Food database loaded with {len(food_db)} entries using {encoding} encoding")
                break
            except Exception as e:
                logger.warning(f"Failed to load with {encoding}: {e}")
                continue
        
        if food_db is None:
            logger.warning("Could not load food database")
        
        # Try to load models (optional)
        try:
            import pickle
            model = pickle.load(open("models/xgboost_model.pkl", "rb"))
            model_loaded = True
            logger.info("XGBoost model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
            model_loaded = False
        
        return True
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return False

# Initialize data
load_data_safely()

@app.route("/", methods=["GET"])
def home():
    """Home endpoint"""
    return jsonify({
        "message": "Food Scanner & Health Analysis API",
        "version": "1.0.0",
        "status": "running",
        "data_loaded": food_db is not None,
        "model_loaded": model_loaded,
        "endpoints": {
            "health": "/api/health",
            "food_search": "/api/food/search",
            "dashboard": "/api/dashboard/overview",
            "predict_disease": "/api/food/predict-disease",
            "analyze_nutrition": "/api/scanner/analyze-nutrition"
        }
    })

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_loaded": food_db is not None,
        "model_loaded": model_loaded
    })

@app.route("/api/food/search", methods=["GET"])
def search_food():
    """Search for food items in the database"""
    try:
        query = request.args.get("query", "").strip()
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
        
        if food_db is None:
            return jsonify({
                "query": query,
                "results": [],
                "total_found": 0,
                "message": "Food database not available"
            })
        
        # Search in food database
        query_lower = query.lower()
        matches = food_db[
            food_db['Food_Name'].str.lower().str.contains(query_lower, na=False)
        ]
        
        # Format results
        results = []
        for _, row in matches.head(20).iterrows():
            results.append({
                "id": int(row.name),
                "name": str(row['Food_Name']),
                "category": str(row.get('Food_Category', 'Unknown')),
                "calories_per_100g": float(row.get('Calories_per_100g', 0)) if pd.notnull(row.get('Calories_per_100g')) else 0
            })
        
        return jsonify({
            "query": query,
            "results": results,
            "total_found": len(results)
        })
    
    except Exception as e:
        logger.error(f"Error searching food: {e}")
        return jsonify({"error": "Failed to search food items"}), 500

@app.route("/api/dashboard/overview", methods=["GET"])
def get_dashboard_overview():
    """Get dashboard overview data"""
    try:
        overview_data = {
            "user_stats": {
                "total_scans": 127,
                "health_score": 85,
                "risk_assessments": 42,
                "improvement_streak": 7
            },
            "recent_analyses": [
                {"date": "2025-01-09", "food": "Quinoa Salad", "risk": "Low", "confidence": 92},
                {"date": "2025-01-08", "food": "Grilled Salmon", "risk": "Low", "confidence": 88},
                {"date": "2025-01-07", "food": "Processed Burger", "risk": "High", "confidence": 85},
                {"date": "2025-01-06", "food": "Greek Yogurt", "risk": "Low", "confidence": 94}
            ],
            "nutrition_summary": {
                "protein": {"value": 120, "target": 150, "unit": "g"},
                "carbs": {"value": 220, "target": 250, "unit": "g"},
                "fat": {"value": 65, "target": 75, "unit": "g"},
                "fiber": {"value": 28, "target": 35, "unit": "g"}
            },
            "risk_distribution": [
                {"name": "Low Risk", "value": 65, "color": "#10b981"},
                {"name": "Medium Risk", "value": 25, "color": "#f59e0b"},
                {"name": "High Risk", "value": 10, "color": "#ef4444"}
            ]
        }
        
        return jsonify(overview_data)
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        return jsonify({"error": "Failed to get dashboard data"}), 500

@app.route("/api/scanner/analyze-nutrition", methods=["POST"])
def analyze_nutrition_data():
    """Analyze nutritional data for health risks"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        nutritional_data = data.get("nutritional_data", {})
        food_name = data.get("food_name", "Unknown Food")
        
        if not nutritional_data:
            return jsonify({"error": "No nutritional data provided"}), 400
        
        # Calculate basic health score
        health_score = calculate_health_score(nutritional_data)
        recommendations = generate_recommendations(nutritional_data)
        
        result = {
            "food_name": food_name,
            "health_score": health_score,
            "recommendations": recommendations,
            "nutritional_analysis": nutritional_data,
            "confidence": 0.85
        }
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error analyzing nutrition data: {e}")
        return jsonify({"error": "Failed to analyze nutrition data"}), 500

@app.route("/food/predict-disease", methods=["POST", "OPTIONS"])
@app.route("/api/food/predict-disease", methods=["POST", "OPTIONS"])
def predict_disease():
    """Predict disease risk based on user data"""
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Mock prediction result (replace with actual model prediction when fully integrated)
        predicted_disease = "Low Risk"
        confidence = 0.85
        
        # If model is loaded, try to use it
        if model_loaded:
            try:
                import pickle
                model = pickle.load(open("models/xgboost_model.pkl", "rb"))
                # Add actual prediction logic here when data format is confirmed
                predicted_disease = "Diabetes"  # Mock result
                confidence = 0.78
            except Exception as e:
                logger.warning(f"Model prediction failed: {e}")
        
        result = {
            "predicted_disease": predicted_disease,
            "confidence": confidence,
            "risk_level": "Medium" if confidence > 0.7 else "Low",
            "recommendations": [
                "Maintain a balanced diet",
                "Exercise regularly",
                "Monitor your health metrics"
            ]
        }
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error predicting disease: {e}")
        return jsonify({"error": "Failed to predict disease"}), 500

def calculate_health_score(nutritional_info):
    """Calculate health score based on nutritional information"""
    score = 100
    
    # Penalize high sodium
    sodium = nutritional_info.get('sodium', 0)
    if sodium > 2000:
        score -= 20
    elif sodium > 1500:
        score -= 10
    
    # Penalize high sugar
    sugar = nutritional_info.get('sugar', 0)
    if sugar > 25:
        score -= 15
    elif sugar > 15:
        score -= 8
    
    # Reward high fiber
    fiber = nutritional_info.get('fiber', 0)
    if fiber > 5:
        score += 10
    elif fiber > 3:
        score += 5
    
    # Reward good protein content
    protein = nutritional_info.get('protein', 0)
    if protein > 15:
        score += 5
    
    return max(0, min(100, score))

def generate_recommendations(nutritional_info):
    """Generate health recommendations based on nutritional info"""
    recommendations = []
    
    if nutritional_info.get('sodium', 0) > 1500:
        recommendations.append("Consider reducing sodium intake for better heart health")
    
    if nutritional_info.get('sugar', 0) > 20:
        recommendations.append("High sugar content - consider moderation")
    
    if nutritional_info.get('fiber', 0) < 3:
        recommendations.append("Add more fiber-rich foods to your diet")
    
    if nutritional_info.get('protein', 0) < 10:
        recommendations.append("Consider adding more protein sources")
    
    if not recommendations:
        recommendations.append("Good nutritional balance - keep it up!")
    
    return recommendations

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    print("Starting Food Scanner & Health Analysis API Server...")
    print("Frontend should connect to: http://127.0.0.1:5000")
    print("Available endpoints:")
    print("  • Health Check: GET /api/health")
    print("  • Dashboard: GET /api/dashboard/overview")
    print("  • Food Search: GET /api/food/search?query=<food_name>")
    print("  • Nutrition Analysis: POST /api/scanner/analyze-nutrition")
    
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        threaded=True
    )