"""
Comprehensive Flask API Server for Food Scanner & Health Analysis Application
Connects backend machine learning models with frontend Next.js application
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import os
import logging
from datetime import datetime
import traceback
import base64
from PIL import Image
import io
import json

# Import custom modules
from food_scanner import FoodScanner
from label_reader import FoodLabelReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000","https://food-label-analysis.vercel.app"])  # Allow Next.js frontend

# Global variables for models and data
model = None
label_encoder_y = None
food_db = None
food_scanner = None
label_reader = None

def load_models_and_data():
    """Load all required models and datasets"""
    global model, label_encoder_y, food_db, food_scanner, label_reader
    
    try:
        logger.info("Loading models and data...")
        
        # Load main ML model
        model = pickle.load(open("models/xgboost_model.pkl", "rb"))
        label_encoder_y = pickle.load(open("models/label_encoder_y.pkl", "rb"))
        logger.info("✅ XGBoost model loaded successfully")
        
        # Load food database
        food_db = pd.read_csv("data/food_database.csv", encoding='utf-8', errors='ignore')
        logger.info(f"✅ Food database loaded with {len(food_db)} entries")
        
        # Initialize food scanner
        food_scanner = FoodScanner()
        logger.info("✅ Food scanner initialized")
        
        # Initialize label reader
        label_reader = FoodLabelReader()
        logger.info("✅ Label reader initialized")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error loading models: {e}")
        return False

def encode_categorical_features(test_df, original_df):
    """Encode categorical features using the same encoding as training"""
    encoded_df = test_df.copy()
    categorical_cols = encoded_df.select_dtypes(include=["object"]).columns
    
    for col in categorical_cols:
        if col in original_df.columns:
            le = LabelEncoder()
            le.fit(original_df[col].astype(str))
            try:
                encoded_df[col] = le.transform(encoded_df[col].astype(str))
            except ValueError:
                # Handle unknown categories by using the most frequent category
                encoded_df[col] = le.transform([original_df[col].mode()[0]] * len(encoded_df))
    
    return encoded_df

# Initialize models on startup
def initialize():
    """Initialize the application"""
    if not load_models_and_data():
        logger.error("Failed to initialize application")

# Initialize models immediately when the module is loaded
initialize()

# ==================== HEALTH ENDPOINTS ====================

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": model is not None,
        "food_db_loaded": food_db is not None
    })

# ==================== DASHBOARD ENDPOINTS ====================

@app.route("/api/dashboard/overview", methods=["GET"])
def get_dashboard_overview():
    """Get dashboard overview data"""
    try:
        # Mock data for dashboard - in real app, this would come from user database
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

# ==================== FOOD SEARCH ENDPOINTS ====================

@app.route("/api/food/search", methods=["GET"])
def search_food():
    """Search for food items in the database"""
    try:
        query = request.args.get("query", "").strip()
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
        
        if food_db is None:
            return jsonify({"error": "Food database not loaded"}), 500
        
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
                "name": row['Food_Name'],
                "category": row.get('Food_Category', 'Unknown'),
                "calories_per_100g": row.get('Calories_per_100g', 0),
                "processing_level": row.get('Processing_Level', 'Unknown'),
                "nutritional_density": row.get('Nutritional_Density', 'Unknown')
            })
        
        return jsonify({
            "query": query,
            "results": results,
            "total_found": len(results)
        })
    
    except Exception as e:
        logger.error(f"Error searching food: {e}")
        return jsonify({"error": "Failed to search food items"}), 500

@app.route("/api/food/details/<int:food_id>", methods=["GET"])
def get_food_details(food_id):
    """Get detailed information about a specific food item"""
    try:
        if food_db is None:
            return jsonify({"error": "Food database not loaded"}), 500
        
        food_item = food_db.iloc[food_id]
        
        details = {
            "id": food_id,
            "name": food_item['Food_Name'],
            "category": food_item.get('Food_Category', 'Unknown'),
            "nutritional_info": {
                "calories_per_100g": food_item.get('Calories_per_100g', 0),
                "protein": food_item.get('Protein_per_100g', 0),
                "carbohydrates": food_item.get('Carbohydrates_per_100g', 0),
                "fat": food_item.get('Fat_per_100g', 0),
                "fiber": food_item.get('Fiber_per_100g', 0),
                "sugar": food_item.get('Sugar_per_100g', 0),
                "sodium": food_item.get('Sodium_per_100mg', 0)
            },
            "processing_level": food_item.get('Processing_Level', 'Unknown'),
            "nutritional_density": food_item.get('Nutritional_Density', 'Unknown')
        }
        
        return jsonify(details)
    
    except Exception as e:
        logger.error(f"Error getting food details: {e}")
        return jsonify({"error": "Food item not found"}), 404

# ==================== FOOD SCANNER ENDPOINTS ====================

@app.route("/api/scanner/analyze-image", methods=["POST"])
def analyze_food_image():
    """Analyze food image using OCR and ML models"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"error": "No image selected"}), 400
        
        # Save uploaded image temporarily
        temp_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        image_file.save(temp_path)
        
        try:
            # Extract text from image using OCR
            if label_reader:
                extracted_text = label_reader.extract_text_from_image(temp_path)
                nutritional_info = label_reader.parse_nutritional_info(extracted_text)
                food_category = label_reader.detect_food_category(extracted_text)
            else:
                # Fallback mock data if OCR not available
                nutritional_info = {
                    "calories": 250,
                    "protein": 12.0,
                    "carbohydrates": 45.0,
                    "fat": 8.0,
                    "fiber": 3.0,
                    "sugar": 15.0,
                    "sodium": 400.0
                }
                food_category = "Processed Food"
            
            # Analyze using food scanner
            analysis_result = {
                "extracted_text": extracted_text if 'extracted_text' in locals() else "",
                "nutritional_info": nutritional_info,
                "food_category": food_category,
                "health_score": calculate_health_score(nutritional_info),
                "recommendations": generate_recommendations(nutritional_info),
                "processing_level": determine_processing_level(nutritional_info),
                "confidence": 0.87  # Mock confidence score
            }
            
            return jsonify(analysis_result)
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        logger.error(f"Error analyzing food image: {e}")
        return jsonify({"error": "Failed to analyze image"}), 500

@app.route("/api/scanner/analyze-nutrition", methods=["POST"])
def analyze_nutrition_data():
    """Analyze nutritional data for health risks"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract nutritional information
        nutritional_data = data.get("nutritional_data", {})
        food_name = data.get("food_name", "Unknown Food")
        
        if not nutritional_data:
            return jsonify({"error": "No nutritional data provided"}), 400
        
        # Use food scanner for analysis
        if food_scanner:
            result = food_scanner.analyze_food_item(food_name, nutritional_data)
        else:
            # Fallback analysis
            result = perform_basic_nutrition_analysis(nutritional_data, food_name)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error analyzing nutrition data: {e}")
        return jsonify({"error": "Failed to analyze nutrition data"}), 500

# ==================== HEALTH ANALYSIS ENDPOINTS ====================

@app.route("/api/health/predict-disease", methods=["POST"])
def predict_disease_risk():
    """Predict disease risk based on user profile and nutrition data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Load original dataset for encoding reference
        original_df = pd.read_csv("data/custom_nutrition_dataset.csv", encoding='utf-8', errors='ignore')
        feature_cols = [c for c in original_df.columns if c != "Disease"]
        
        # Prepare user data
        user_data = {}
        for col in feature_cols:
            if col in data:
                user_data[col] = data[col]
            else:
                # Use default values from dataset
                user_data[col] = original_df[col].mode()[0] if original_df[col].dtype == 'object' else original_df[col].mean()
        
        # Create DataFrame
        user_df = pd.DataFrame([user_data])
        
        # Encode categorical features
        encoded_df = encode_categorical_features(user_df, original_df)
        
        # Make prediction
        if model and label_encoder_y:
            prediction = model.predict(encoded_df)
            probabilities = model.predict_proba(encoded_df)[0]
            max_prob = max(probabilities)
            predicted_disease = label_encoder_y.inverse_transform(prediction)[0]
            
            # Get all disease probabilities
            all_probabilities = {}
            for i, disease in enumerate(label_encoder_y.classes_):
                all_probabilities[disease] = float(probabilities[i])
            
            result = {
                "predicted_disease": predicted_disease,
                "confidence": float(max_prob),
                "all_probabilities": all_probabilities,
                "risk_level": get_risk_level(max_prob),
                "recommendations": get_disease_recommendations(predicted_disease),
                "user_profile": user_data
            }
            
            return jsonify(result)
        else:
            return jsonify({"error": "Prediction model not available"}), 500
    
    except Exception as e:
        logger.error(f"Error predicting disease risk: {e}")
        return jsonify({"error": "Failed to predict disease risk"}), 500

@app.route("/api/health/comprehensive-analysis", methods=["POST"])
def comprehensive_health_analysis():
    """Perform comprehensive health analysis"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Run multiple analyses
        analyses = {}
        
        # Disease risk prediction
        try:
            disease_prediction = predict_disease_risk()
            if disease_prediction.status_code == 200:
                analyses["disease_risk"] = disease_prediction.get_json()
        except:
            analyses["disease_risk"] = {"error": "Disease prediction unavailable"}
        
        # Nutritional analysis
        nutritional_data = data.get("nutritional_data", {})
        if nutritional_data:
            analyses["nutrition"] = analyze_nutritional_balance(nutritional_data)
        
        # Lifestyle recommendations
        analyses["lifestyle_recommendations"] = generate_lifestyle_recommendations(data)
        
        # Health score calculation
        analyses["overall_health_score"] = calculate_overall_health_score(data)
        
        return jsonify(analyses)
    
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        return jsonify({"error": "Failed to perform comprehensive analysis"}), 500

# ==================== USER PROFILE ENDPOINTS ====================

@app.route("/api/profile/health-metrics", methods=["GET", "POST"])
def handle_health_metrics():
    """Get or update user health metrics"""
    if request.method == "GET":
        # Mock health metrics - in real app, fetch from user database
        metrics = {
            "bmi": {"value": 23.5, "status": "normal", "target": "18.5-24.9"},
            "daily_steps": {"value": 8500, "status": "good", "target": "10,000"},
            "water_intake": {"value": 2.1, "status": "good", "target": "2.5L"},
            "sleep_hours": {"value": 7.2, "status": "good", "target": "7-9h"},
            "heart_rate": {"value": 72, "status": "normal", "target": "60-100 bpm"},
            "blood_pressure": {"value": "120/80", "status": "normal", "target": "<120/80"}
        }
        return jsonify(metrics)
    
    elif request.method == "POST":
        # Update health metrics
        data = request.get_json()
        # In real app, save to database
        return jsonify({"message": "Health metrics updated successfully", "data": data})

# ==================== UTILITY FUNCTIONS ====================

def calculate_health_score(nutritional_info):
    """Calculate health score based on nutritional information"""
    score = 100
    
    # Penalize high sodium
    if nutritional_info.get('sodium', 0) > 2000:
        score -= 20
    elif nutritional_info.get('sodium', 0) > 1500:
        score -= 10
    
    # Penalize high sugar
    if nutritional_info.get('sugar', 0) > 25:
        score -= 15
    elif nutritional_info.get('sugar', 0) > 15:
        score -= 8
    
    # Reward high fiber
    if nutritional_info.get('fiber', 0) > 5:
        score += 10
    elif nutritional_info.get('fiber', 0) > 3:
        score += 5
    
    # Reward good protein content
    if nutritional_info.get('protein', 0) > 15:
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

def determine_processing_level(nutritional_info):
    """Determine food processing level based on nutritional info"""
    sodium = nutritional_info.get('sodium', 0)
    sugar = nutritional_info.get('sugar', 0)
    
    if sodium > 2000 or sugar > 30:
        return "Highly Processed"
    elif sodium > 1000 or sugar > 15:
        return "Moderately Processed"
    else:
        return "Minimally Processed"

def perform_basic_nutrition_analysis(nutritional_data, food_name):
    """Perform basic nutrition analysis without ML models"""
    health_score = calculate_health_score(nutritional_data)
    recommendations = generate_recommendations(nutritional_data)
    
    return {
        "food_name": food_name,
        "health_score": health_score,
        "recommendations": recommendations,
        "nutritional_analysis": nutritional_data,
        "processing_level": determine_processing_level(nutritional_data),
        "confidence": 0.75
    }

def get_risk_level(confidence):
    """Determine risk level based on confidence score"""
    if confidence > 0.8:
        return "High"
    elif confidence > 0.6:
        return "Medium"
    else:
        return "Low"

def generate_lifestyle_recommendations(user_data):
    """Generate lifestyle recommendations based on user data"""
    recommendations = []
    
    age = user_data.get('Ages', 30)
    activity_level = user_data.get('Activity Level', 'Sedentary')
    
    if age > 50:
        recommendations.append("Regular health checkups are important at your age")
        recommendations.append("Consider calcium-rich foods for bone health")
    
    if activity_level == 'Sedentary':
        recommendations.append("Try to incorporate more physical activity into your routine")
        recommendations.append("Even 30 minutes of walking daily can make a difference")
    
    return recommendations

def get_disease_recommendations(predicted_disease):
    """Get recommendations based on predicted disease"""
    recommendations_map = {
        "Diabetes": [
            "Monitor blood sugar levels regularly",
            "Focus on complex carbohydrates",
            "Include regular physical activity",
            "Limit processed foods and sugary drinks"
        ],
        "Heart Disease": [
            "Reduce sodium intake",
            "Include omega-3 rich foods",
            "Maintain healthy weight",
            "Manage stress levels"
        ],
        "Hypertension": [
            "Follow DASH diet principles",
            "Limit sodium to less than 2300mg daily",
            "Include potassium-rich foods",
            "Maintain regular exercise routine"
        ],
        "Obesity": [
            "Create caloric deficit through diet and exercise",
            "Focus on whole, unprocessed foods",
            "Include strength training exercises",
            "Stay hydrated and get adequate sleep"
        ]
    }
    
    return recommendations_map.get(predicted_disease, [
        "Maintain a balanced diet",
        "Exercise regularly",
        "Get adequate sleep",
        "Manage stress levels"
    ])

def analyze_nutritional_balance(nutritional_data):
    """Analyze nutritional balance"""
    analysis = {
        "macronutrient_balance": {},
        "micronutrient_status": {},
        "overall_rating": "Good"
    }
    
    total_calories = nutritional_data.get('calories', 2000)
    protein_cals = nutritional_data.get('protein', 0) * 4
    carb_cals = nutritional_data.get('carbohydrates', 0) * 4
    fat_cals = nutritional_data.get('fat', 0) * 9
    
    if total_calories > 0:
        analysis["macronutrient_balance"] = {
            "protein_percent": (protein_cals / total_calories) * 100,
            "carb_percent": (carb_cals / total_calories) * 100,
            "fat_percent": (fat_cals / total_calories) * 100
        }
    
    return analysis

def calculate_overall_health_score(user_data):
    """Calculate overall health score"""
    score = 100
    
    # Age factor
    age = user_data.get('Ages', 30)
    if age > 65:
        score -= 10
    elif age > 50:
        score -= 5
    
    # Activity level
    activity = user_data.get('Activity Level', 'Sedentary')
    if activity == 'Sedentary':
        score -= 15
    elif activity == 'Lightly Active':
        score -= 5
    elif activity == 'Very Active':
        score += 10
    
    # BMI (if available)
    weight = user_data.get('Weight', 70)
    height = user_data.get('Height', 170) / 100  # Convert to meters
    bmi = weight / (height * height) if height > 0 else 25
    
    if bmi > 30:
        score -= 20
    elif bmi > 25:
        score -= 10
    elif bmi < 18.5:
        score -= 5
    
    return max(0, min(100, score))

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    logger.error(traceback.format_exc())
    return jsonify({"error": "An unexpected error occurred"}), 500

# ==================== MAIN ENTRY POINT ====================

@app.route("/")
def home():
    """Home endpoint"""
    return jsonify({
        "message": "Food Scanner & Health Analysis API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "dashboard": "/api/dashboard/overview",
            "food_search": "/api/food/search",
            "food_scanner": "/api/scanner/analyze-image",
            "health_analysis": "/api/health/predict-disease",
            "profile": "/api/profile/health-metrics"
        }
    })

if __name__ == "__main__":
    print("🚀 Starting Food Scanner & Health Analysis API Server...")
    print("📍 Frontend should connect to: http://127.0.0.1:5000")
    print("🔍 Available endpoints:")
    print("   • Health Check: GET /api/health")
    print("   • Dashboard: GET /api/dashboard/overview")
    print("   • Food Search: GET /api/food/search?query=<food_name>")
    print("   • Image Analysis: POST /api/scanner/analyze-image")
    print("   • Disease Prediction: POST /api/health/predict-disease")
    print("   • Health Metrics: GET/POST /api/profile/health-metrics")
    
    # Initialize models
    if not load_models_and_data():
        print("⚠️  Warning: Some models failed to load. API will run with limited functionality.")
    
    # Start the server
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        threaded=True
    )
