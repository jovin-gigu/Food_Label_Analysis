import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
from werkzeug.utils import secure_filename
from label_reader import FoodLabelReader
from ai_service import initialize_ai_service, get_ai_service
from dotenv import load_dotenv
import time
import tempfile
from pathlib import Path

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS for production
if os.getenv('FLASK_ENV') == 'production':
    # In production, only allow your frontend domain
    CORS(app, origins=[
        "https://food-label-analysis.vercel.app"
    ])
else:
    # In development, allow all origins
    CORS(app)

@app.route("/food/analyze", methods=["POST"])
def analyze_food():
    data = request.get_json()
    food_name = data.get("name")
    # your analysis logic here
    result = {"message": f"Analyzed {food_name} successfully!"}
    return jsonify(result)

port = int(os.environ.get("PORT", 5000))  # 5000 fallback for local dev

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)

if os.getenv('FLASK_ENV') == 'production':
    CORS(app, origins=["https://food-label-analysis.vercel.app"])
else:
    CORS(app)  # local dev


# Configure upload settings
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def safe_file_cleanup(filepath, max_retries=3, delay=0.1):
    """
    Safely remove a file with retry logic for Windows file locking issues.
    
    Args:
        filepath (str): Path to the file to remove
        max_retries (int): Maximum number of retry attempts
        delay (float): Delay between retry attempts in seconds
    """
    if not os.path.exists(filepath):
        return True
        
    for attempt in range(max_retries):
        try:
            os.remove(filepath)
            return True
        except PermissionError as e:
            if "[WinError 32]" in str(e) or "being used by another process" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    print(f"⚠️ Warning: Could not delete file {filepath} after {max_retries} attempts: {e}")
                    return False
            else:
                print(f"❌ Error deleting file {filepath}: {e}")
                return False
        except Exception as e:
            print(f"❌ Unexpected error deleting file {filepath}: {e}")
            return False
    
    return False

def create_secure_temp_file(file, upload_folder):
    """
    Create a secure temporary file with unique name to avoid conflicts.
    
    Args:
        file: Uploaded file object
        upload_folder (str): Directory to save the file
        
    Returns:
        str: Path to the saved file
    """
    # Generate a unique filename with timestamp
    timestamp = str(int(time.time() * 1000))
    original_filename = secure_filename(file.filename)
    name, ext = os.path.splitext(original_filename)
    unique_filename = f"{name}_{timestamp}{ext}"
    
    filepath = os.path.join(upload_folder, unique_filename)
    file.save(filepath)
    return filepath

def safe_parse_nutrition_value(value, default=0, is_int=False):
    """
    Safely parse nutrition values that might contain strings like '<1', '~2', 'trace', etc.
    
    Args:
        value: The value to parse (can be string, int, float)
        default: Default value if parsing fails
        is_int: Whether to return an integer (True) or float (False)
        
    Returns:
        Parsed numeric value or default
    """
    if value is None:
        return default
    
    # If already a number, return it
    if isinstance(value, (int, float)):
        return int(value) if is_int else float(value)
    
    # Convert to string and clean it
    str_value = str(value).strip().lower()
    
    # Handle empty strings
    if not str_value:
        return default
    
    # Handle special cases
    if str_value in ['trace', 'negligible', 'n/a', 'na', '-']:
        return default
    
    # Handle '<' notation (less than)
    if str_value.startswith('<'):
        try:
            num = float(str_value[1:])
            # Return half the value for '<X' cases
            result = num / 2
            return int(result) if is_int else result
        except ValueError:
            return default
    
    # Handle '~' notation (approximately)
    if str_value.startswith('~'):
        try:
            num = float(str_value[1:])
            return int(num) if is_int else num
        except ValueError:
            return default
    
    # Handle ranges like '2-3'
    if '-' in str_value and not str_value.startswith('-'):
        try:
            parts = str_value.split('-')
            if len(parts) == 2:
                low = float(parts[0])
                high = float(parts[1])
                avg = (low + high) / 2
                return int(avg) if is_int else avg
        except ValueError:
            pass
    
    # Try direct conversion
    try:
        num = float(str_value)
        return int(num) if is_int else num
    except ValueError:
        return default

# Initialize the OCR label reader
label_reader = FoodLabelReader()

# Initialize AI model service
ai_api_key = os.getenv('AI_API_KEY')
if ai_api_key:
    try:
        print("🤖 Initializing AI model service...")
        initialize_ai_service(ai_api_key)
        print("✅ AI model service initialized successfully.")
    except Exception as e:
        print(f"❌ Error initializing AI model service: {e}")
else:
    print("⚠️ AI_API_KEY not found in environment variables")

try:
    print("Loading model and encoders...")
    model = pickle.load(open("models/food_analysis_model.pkl", "rb"))
    label_encoder_y = pickle.load(open("models/food_label_encoder_y.pkl", "rb"))
    label_encoders = pickle.load(open("models/food_feature_encoders.pkl", "rb"))
    feature_cols = pickle.load(open("models/food_feature_names.pkl", "rb"))
    food_db = pd.read_csv("data/food_database_fixed.csv")
    print("✅ Model and encoders loaded successfully.")
except Exception as e:
    print(f"❌ Error loading model or data: {e}")

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_health_score(nutritional_data):
    """Calculate a health score based on nutritional information"""
    score = 50  # Base score
    
    # Positive factors
    if 'protein' in nutritional_data and nutritional_data['protein'] > 10:
        score += 10
    if 'fiber' in nutritional_data and nutritional_data['fiber'] > 3:
        score += 15
    
    # Negative factors
    if 'sugar' in nutritional_data:
        if nutritional_data['sugar'] > 20:
            score -= 20
        elif nutritional_data['sugar'] > 10:
            score -= 10
    
    if 'sodium' in nutritional_data:
        if nutritional_data['sodium'] > 500:
            score -= 15
        elif nutritional_data['sodium'] > 300:
            score -= 10
    
    return max(0, min(100, score))

def get_processing_level_text(level):
    """Convert processing level number to text"""
    if level <= 3:
        return "Unprocessed"
    elif level <= 5:
        return "Minimally Processed"
    elif level <= 7:
        return "Processed"
    else:
        return "Ultra-processed"

def generate_recommendations(nutritional_data, category, processing_level):
    """Generate health recommendations based on analysis"""
    recommendations = []
    
    if 'sugar' in nutritional_data and nutritional_data['sugar'] > 15:
        recommendations.append("High sugar content - consider consuming in moderation")
    
    if 'sodium' in nutritional_data and nutritional_data['sodium'] > 400:
        recommendations.append("High sodium content - be mindful of daily intake")
    
    if 'fiber' in nutritional_data and nutritional_data['fiber'] > 3:
        recommendations.append("Good source of dietary fiber")
    
    if 'protein' in nutritional_data and nutritional_data['protein'] > 10:
        recommendations.append("Good protein content")
    
    if processing_level <= 3:
        recommendations.append("Minimally processed food - a healthy choice")
    elif processing_level > 7:
        recommendations.append("Highly processed - consider whole food alternatives")
    
    if not recommendations:
        recommendations.append("Moderate nutritional profile - part of a balanced diet")
    
    return recommendations

@app.route("/api/scan_label", methods=["POST"])
def scan_label():
    """OCR endpoint to scan food labels and extract nutritional information"""
    try:
        # Check if file is in request
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed. Please upload PNG, JPG, JPEG, GIF, or BMP files"}), 400
        
        # Save the uploaded file with unique name
        filepath = create_secure_temp_file(file, app.config['UPLOAD_FOLDER'])
        
        try:
            # Use the label reader to process the image
            result = label_reader.read_food_label(filepath)
            
            # Clean up the uploaded file safely
            safe_file_cleanup(filepath)
            
            if "error" in result:
                return jsonify(result), 400
            
            # Extract nutritional information
            nutritional_data = result.get('nutritional_data', {})
            processing_level = result.get('processing_level', 5)
            category = result.get('food_category', 'Mixed')
            
            # Calculate health score
            health_score = calculate_health_score(nutritional_data)
            
            # Get processing level text
            processing_text = get_processing_level_text(processing_level)
            
            # Generate recommendations
            recommendations = generate_recommendations(nutritional_data, category, processing_level)
            
            # Format response to match frontend expectations
            response = {
                "name": f"Scanned Food Product ({category})",
                "confidence": 85,  # OCR confidence could be calculated based on text quality
                "nutritional_info": {
                    "calories": int(nutritional_data.get('calories', 0)),
                    "protein": float(nutritional_data.get('protein', 0)),
                    "carbohydrates": float(nutritional_data.get('carbohydrates', nutritional_data.get('carbs', 0))),
                    "fat": float(nutritional_data.get('fat', 0)),
                    "fiber": float(nutritional_data.get('fiber', 0)),
                    "sugar": float(nutritional_data.get('sugar', 0)),
                    "sodium": float(nutritional_data.get('sodium', 0))
                },
                "health_score": health_score,
                "processing_level": processing_text,
                "recommendations": recommendations,
                "raw_data": result  # Include raw OCR results for debugging
            }
            
            return jsonify(response)
            
        except Exception as e:
            # Clean up file in case of error
            safe_file_cleanup(filepath)
            return jsonify({"error": f"Error processing image: {str(e)}"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/search_food", methods=["GET"])
def search_food():
    query = request.args.get("query", "")
    matches = food_db[food_db['Food_Name'].str.lower().str.contains(query.lower(), na=False)]
    return matches[['Food_Name', 'Food_Category', 'Calories_per_100g']].head(10).to_json(orient="records")

@app.route("/food/categories", methods=["GET"])
def get_food_categories():
    """Get available food categories"""
    try:
        categories = [
            "Fruits",
            "Vegetables", 
            "Grains & Cereals",
            "Proteins & Meat",
            "Dairy & Eggs",
            "Nuts & Seeds",
            "Beverages",
            "Snacks & Sweets",
            "Oils & Fats",
            "Herbs & Spices",
            "Seafood",
            "Legumes & Beans"
        ]
        
        return jsonify({
            "success": True,
            "categories": categories
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to get categories: {str(e)}"}), 500

@app.route("/food/search", methods=["GET"])
def food_search_ai():
    """AI-powered food search using Gemini"""
    try:
        query = request.args.get("query", "").strip()
        category = request.args.get("category", "").strip()
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
        
        # Get AI service
        ai_model = get_ai_service()
        if not ai_model:
            # Fallback to database search
            matches = food_db[food_db['Food_Name'].str.lower().str.contains(query.lower(), na=False)]
            if category and category != 'all':
                matches = matches[matches['Food_Category'].str.lower().str.contains(category.lower(), na=False)]
            
            results = []
            for _, row in matches.head(10).iterrows():
                results.append({
                    'Food Name': row.get('Food_Name', ''),
                    'Category': row.get('Food_Category', ''),
                    'Processing Level': 'Processed',
                    'Nutritional Density': 'Medium',
                    'Calories': int(row.get('Calories_per_100g', 0)),
                    'Protein': int(row.get('Protein_per_100g', 0)),
                    'Carbohydrates': int(row.get('Carbs_per_100g', 0)),
                    'Fat': int(row.get('Fat_per_100g', 0)),
                    'Fiber': int(row.get('Fiber_per_100g', 0)),
                    'Sugar': int(row.get('Sugar_per_100g', 0)),
                    'Sodium': int(row.get('Sodium_per_100g', 0)),
                    'Vitamin C': 0,
                    'Vitamin A': 0,
                    'Calcium': 0,
                    'Iron': 0,
                    'Potassium': 0,
                    'Magnesium': 0,
                    'Zinc': 0
                })
            
            return jsonify({
                "success": True,
                "query": query,
                "results": results,
                "source": "database",
                "count": len(results)
            })
        
        # Create AI search prompt
        category_filter = f" in the {category} category" if category and category != 'all' else ""
        search_prompt = f"""
        Search for foods related to: "{query}"{category_filter}
        
        Please provide comprehensive information about foods matching this query. 
        Return exactly 8-10 relevant food items as a JSON array with this structure:
        [
            {{
                "Food Name": "Complete food name",
                "Category": "Food category (e.g., Fruits, Vegetables, Grains, Proteins, Dairy, Snacks)",
                "Processing Level": "Fresh/Minimally Processed/Processed/Ultra-processed",
                "Nutritional Density": "High/Medium/Low",
                "Calories": calories_per_100g_as_number,
                "Protein": protein_grams_per_100g_as_number,
                "Carbohydrates": carbs_grams_per_100g_as_number,
                "Fat": fat_grams_per_100g_as_number,
                "Fiber": fiber_grams_per_100g_as_number,
                "Sugar": sugar_grams_per_100g_as_number,
                "Sodium": sodium_mg_per_100g_as_number,
                "Vitamin C": vitamin_c_mg_per_100g_as_number,
                "Vitamin A": vitamin_a_ug_per_100g_as_number,
                "Calcium": calcium_mg_per_100g_as_number,
                "Iron": iron_mg_per_100g_as_number,
                "Potassium": potassium_mg_per_100g_as_number,
                "Magnesium": magnesium_mg_per_100g_as_number,
                "Zinc": zinc_mg_per_100g_as_number
            }}
        ]
        
        Base nutritional values on standard food composition databases. Ensure all numeric values are realistic.
        """
        
        try:
            # Get AI analysis
            analysis_result = ai_model.analyze_text(search_prompt)
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', analysis_result, re.DOTALL)
            if json_match:
                foods_data = json.loads(json_match.group())
                
                return jsonify({
                    "success": True,
                    "query": query,
                    "category": category,
                    "results": foods_data,
                    "source": "ai",
                    "count": len(foods_data)
                })
            else:
                # Fallback to database if AI parsing fails
                raise ValueError("Could not parse AI response")
                
        except Exception as ai_error:
            print(f"AI search error: {ai_error}")
            # Fallback to database search
            matches = food_db[food_db['Food_Name'].str.lower().str.contains(query.lower(), na=False)]
            if category and category != 'all':
                matches = matches[matches['Food_Category'].str.lower().str.contains(category.lower(), na=False)]
            
            results = []
            for _, row in matches.head(8).iterrows():
                results.append({
                    'Food Name': row.get('Food_Name', ''),
                    'Category': row.get('Food_Category', ''),
                    'Processing Level': 'Processed',
                    'Nutritional Density': 'Medium',
                    'Calories': int(row.get('Calories_per_100g', 0)),
                    'Protein': int(row.get('Protein_per_100g', 0)),
                    'Carbohydrates': int(row.get('Carbs_per_100g', 0)),
                    'Fat': int(row.get('Fat_per_100g', 0)),
                    'Fiber': int(row.get('Fiber_per_100g', 0)),
                    'Sugar': int(row.get('Sugar_per_100g', 0)),
                    'Sodium': int(row.get('Sodium_per_100g', 0)),
                    'Vitamin C': 0,
                    'Vitamin A': 0,
                    'Calcium': 0,
                    'Iron': 0,
                    'Potassium': 0,
                    'Magnesium': 0,
                    'Zinc': 0
                })
            
            return jsonify({
                "success": True,
                "query": query,
                "results": results,
                "source": "database_fallback",
                "count": len(results)
            })
            
    except Exception as e:
        print(f"Food search error: {e}")
        return jsonify({"error": f"Food search failed: {str(e)}"}), 500

@app.route("/food/healthy", methods=["GET"])
def get_healthy_foods():
    """Get recommended healthy foods using AI"""
    try:
        limit = int(request.args.get("limit", 6))
        
        # Get AI service
        ai_model = get_ai_service()
        if not ai_model:
            # Fallback healthy foods from database
            healthy_foods = [
                {"Food Name": "Spinach", "Category": "Vegetables", "Calories": 23, "Protein": 2.9, "Nutritional Density": "High"},
                {"Food Name": "Blueberries", "Category": "Fruits", "Calories": 57, "Protein": 0.7, "Nutritional Density": "High"},
                {"Food Name": "Salmon", "Category": "Proteins", "Calories": 208, "Protein": 20.4, "Nutritional Density": "High"},
                {"Food Name": "Greek Yogurt", "Category": "Dairy", "Calories": 59, "Protein": 10.2, "Nutritional Density": "High"},
                {"Food Name": "Quinoa", "Category": "Grains", "Calories": 120, "Protein": 4.4, "Nutritional Density": "High"},
                {"Food Name": "Avocado", "Category": "Fruits", "Calories": 160, "Protein": 2.0, "Nutritional Density": "High"}
            ][:limit]
            
            return jsonify({
                "success": True,
                "results": healthy_foods,
                "source": "database",
                "count": len(healthy_foods)
            })
        
        # Create AI prompt for healthy foods
        healthy_prompt = f"""
        Recommend {limit} of the healthiest, most nutrient-dense foods available.
        Focus on foods with high nutritional value, minimal processing, and proven health benefits.
        
        Return as a JSON array with this structure:
        [
            {{
                "Food Name": "Complete food name",
                "Category": "Food category",
                "Processing Level": "Fresh/Minimally Processed",
                "Nutritional Density": "High",
                "Calories": calories_per_100g_as_number,
                "Protein": protein_grams_per_100g_as_number,
                "Carbohydrates": carbs_grams_per_100g_as_number,
                "Fat": fat_grams_per_100g_as_number,
                "Fiber": fiber_grams_per_100g_as_number,
                "Sugar": sugar_grams_per_100g_as_number,
                "Sodium": sodium_mg_per_100g_as_number,
                "Vitamin C": vitamin_c_mg_per_100g_as_number,
                "Vitamin A": vitamin_a_ug_per_100g_as_number,
                "Calcium": calcium_mg_per_100g_as_number,
                "Iron": iron_mg_per_100g_as_number,
                "Potassium": potassium_mg_per_100g_as_number,
                "Magnesium": magnesium_mg_per_100g_as_number,
                "Zinc": zinc_mg_per_100g_as_number
            }}
        ]
        
        Include a variety from different food groups: vegetables, fruits, proteins, whole grains, healthy fats.
        """
        
        try:
            # Get AI analysis
            analysis_result = ai_model.analyze_text(healthy_prompt)
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', analysis_result, re.DOTALL)
            if json_match:
                healthy_foods = json.loads(json_match.group())
                
                return jsonify({
                    "success": True,
                    "results": healthy_foods,
                    "source": "ai",
                    "count": len(healthy_foods)
                })
            else:
                raise ValueError("Could not parse AI response")
                
        except Exception as ai_error:
            print(f"AI healthy foods error: {ai_error}")
            # Fallback to predefined healthy foods
            healthy_foods = [
                {"Food Name": "Kale", "Category": "Vegetables", "Calories": 35, "Protein": 3.3, "Nutritional Density": "High"},
                {"Food Name": "Wild Blueberries", "Category": "Fruits", "Calories": 57, "Protein": 0.7, "Nutritional Density": "High"},
                {"Food Name": "Wild Salmon", "Category": "Seafood", "Calories": 208, "Protein": 20.4, "Nutritional Density": "High"},
                {"Food Name": "Greek Yogurt", "Category": "Dairy", "Calories": 59, "Protein": 10.2, "Nutritional Density": "High"},
                {"Food Name": "Quinoa", "Category": "Grains", "Calories": 120, "Protein": 4.4, "Nutritional Density": "High"},
                {"Food Name": "Avocado", "Category": "Fruits", "Calories": 160, "Protein": 2.0, "Nutritional Density": "High"}
            ][:limit]
            
            return jsonify({
                "success": True,
                "results": healthy_foods,
                "source": "fallback",
                "count": len(healthy_foods)
            })
            
    except Exception as e:
        print(f"Healthy foods error: {e}")
        return jsonify({"error": f"Failed to get healthy foods: {str(e)}"}), 500

@app.route("/food/analyze", methods=["POST"])
def analyze_food_ai():
    """AI-powered food analysis using Gemini"""
    try:
        data = request.get_json()
        food_name = data.get("food_name", "").strip()
        
        if not food_name:
            return jsonify({"error": "Food name is required"}), 400
        
        # Get AI service
        ai_model = get_ai_service()
        if not ai_model:
            return jsonify({"error": "AI service not available"}), 503
        
        # Create analysis prompt 
        analysis_prompt = f"""
        Provide a comprehensive nutritional and health analysis of: "{food_name}"
        
        Include the following information in JSON format:
        {{
            "food_name": "Standardized food name",
            "category": "Food category",
            "nutritional_profile": {{
                "calories_per_100g": number,
                "protein": number,
                "carbohydrates": number,
                "fat": number,
                "fiber": number,
                "sugar": number,
                "sodium": number
            }},
            "health_benefits": [
                "Benefit 1",
                "Benefit 2",
                "Benefit 3"
            ],
            "health_concerns": [
                "Concern 1 (if any)",
                "Concern 2 (if any)"
            ],
            "processing_level": "Fresh/Minimally Processed/Processed/Ultra-processed",
            "nutritional_density": "High/Medium/Low",
            "recommended_serving": "Standard serving size and frequency",
            "preparation_tips": [
                "Tip 1",
                "Tip 2"
            ],
            "health_score": score_out_of_100,
            "summary": "Brief 2-3 sentence summary of the food's nutritional value and health impact"
        }}
        
        Base your analysis on established nutritional databases and scientific research.
        """
        
        try:
            # Get AI analysis
            analysis_result = ai_model.analyze_text(analysis_prompt)
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', analysis_result, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
                
                return jsonify({
                    "success": True,
                    "food_name": food_name,
                    "analysis": analysis_data,
                    "source": "ai"
                })
            else:
                raise ValueError("Could not parse AI response")
                
        except Exception as ai_error:
            print(f"AI analysis error: {ai_error}")
            # Fallback analysis
            return jsonify({
                "success": True,
                "food_name": food_name,
                "analysis": {
                    "food_name": food_name,
                    "category": "General",
                    "nutritional_profile": {
                        "calories_per_100g": 150,
                        "protein": 5.0,
                        "carbohydrates": 20.0,
                        "fat": 5.0,
                        "fiber": 3.0,
                        "sugar": 8.0,
                        "sodium": 200
                    },
                    "health_benefits": [
                        "Provides essential nutrients",
                        "May support overall health"
                    ],
                    "health_concerns": [
                        "Consider portion size",
                        "Check for allergens"
                    ],
                    "processing_level": "Processed",
                    "nutritional_density": "Medium",
                    "recommended_serving": "Follow standard dietary guidelines",
                    "preparation_tips": [
                        "Follow package instructions",
                        "Store properly"
                    ],
                    "health_score": 60,
                    "summary": f"{food_name} is a food item that can be part of a balanced diet when consumed in moderation."
                },
                "source": "fallback"
            })
            
    except Exception as e:
        print(f"Food analysis error: {e}")
        return jsonify({"error": f"Food analysis failed: {str(e)}"}), 500

@app.route("/api/analyze_food", methods=["POST"])
def analyze_food():
    data = request.json
    food_name = data.get("food_name")
    nutritional_data = data.get("nutritional_data")

    # If food_name is given, get its data from DB
    if food_name:
        row = food_db[food_db['Food_Name'].str.lower() == food_name.lower()]
        if not row.empty:
            nutritional_data = row.iloc[0][feature_cols].to_dict()

    if nutritional_data is None:
        return jsonify({"error": "No nutritional data provided"}), 400

    # Prepare DataFrame
    df = pd.DataFrame([nutritional_data])
    # Encode categorical features
    for col in df.select_dtypes(include=["object"]).columns:
        if col in label_encoders:
            le = label_encoders[col]
            df[col] = le.transform(df[col].astype(str))

    # Predict
    pred = model.predict(df[feature_cols])
    probabilities = model.predict_proba(df[feature_cols])[0]
    max_prob = max(probabilities)
    predicted_disease = label_encoder_y.inverse_transform(pred)[0]
    all_probs = dict(zip(label_encoder_y.classes_, probabilities))

    return jsonify({
        "food_name": food_name or nutritional_data.get("Food_Name", "Unknown"),
        "predicted_disease": predicted_disease,
        "confidence": max_prob,
        "all_probabilities": all_probs
    })

@app.route("/api/ai_analyze", methods=["POST"])
def ai_analyze():
    """Analyze food image using AI model"""
    try:
        ai_model = get_ai_service()
        if not ai_model:
            return jsonify({"error": "AI model service not available. Please check API key configuration."}), 503
        
        # Check if file is in request
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed. Please upload PNG, JPG, JPEG, GIF, or BMP files"}), 400
        
        # Save the uploaded file with unique name
        filepath = create_secure_temp_file(file, app.config['UPLOAD_FOLDER'])
        
        try:
            # Analyze image with AI model
            analysis_result = ai_model.analyze_food_image(filepath)
            
            # Clean up the uploaded file safely
            safe_file_cleanup(filepath)
            
            if not analysis_result['success']:
                return jsonify({"error": analysis_result.get('error', 'Failed to analyze image')}), 400
            
            data = analysis_result['data']
            
            # Extract nutritional information
            nutritional_info = data.get('nutritional_info', {})
            
            # Calculate health score (use AI model's confidence or calculate our own)
            health_score = safe_parse_nutrition_value(data.get('health_score', data.get('confidence', 50)), 50, is_int=True)
            
            # Format response to match frontend expectations
            response = {
                "name": data.get('food_name', 'Unknown Food Product'),
                "confidence": safe_parse_nutrition_value(data.get('confidence', 0), 0, is_int=True),
                "nutritional_info": {
                    "calories": safe_parse_nutrition_value(nutritional_info.get('calories', 0), 0, is_int=True),
                    "protein": safe_parse_nutrition_value(nutritional_info.get('protein', 0), 0.0),
                    "carbohydrates": safe_parse_nutrition_value(nutritional_info.get('carbohydrates', 0), 0.0),
                    "fat": safe_parse_nutrition_value(nutritional_info.get('fat', 0), 0.0),
                    "fiber": safe_parse_nutrition_value(nutritional_info.get('fiber', 0), 0.0),
                    "sugar": safe_parse_nutrition_value(nutritional_info.get('sugar', 0), 0.0),
                    "sodium": safe_parse_nutrition_value(nutritional_info.get('sodium', 0), 0.0)
                },
                "health_score": health_score,
                "processing_level": f"Level {data.get('processing_level', 5)} Processing",
                "recommendations": data.get('recommendations', []),
                "food_category": data.get('food_category', 'Unknown'),
                "ingredients": data.get('ingredients', []),
                "allergens": data.get('allergens', []),
                "health_analysis": data.get('health_analysis', ''),
                "ai_powered": True,
                "raw_ai_data": data
            }
            
            return jsonify(response)
            
        except Exception as e:
            # Clean up file in case of error
            safe_file_cleanup(filepath)
            return jsonify({"error": f"Error analyzing image with AI model: {str(e)}"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/nutrition_scan", methods=["POST"])
def nutrition_scan():
    """Extract nutrition facts from food label using AI model"""
    try:
        ai_model = get_ai_service()
        if not ai_model:
            return jsonify({"error": "AI model service not available"}), 503
        
        # Check if file is in request
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400
        
        # Save the uploaded file with unique name
        filepath = create_secure_temp_file(file, app.config['UPLOAD_FOLDER'])
        
        try:
            # Extract nutrition label with AI model
            result = ai_model.extract_nutrition_label(filepath)
            
            # Clean up the uploaded file safely
            safe_file_cleanup(filepath)
            
            if not result['success']:
                return jsonify({"error": result.get('error', 'Failed to extract nutrition label')}), 400
            
            data = result['data']
            nutrition_facts = data.get('nutrition_facts', {})
            
            # Format response
            response = {
                "name": data.get('product_name', 'Nutrition Label'),
                "brand": data.get('brand', ''),
                "confidence": safe_parse_nutrition_value(data.get('confidence', 0), 0, is_int=True),
                "nutritional_info": {
                    "calories": safe_parse_nutrition_value(nutrition_facts.get('calories', 0), 0, is_int=True),
                    "protein": safe_parse_nutrition_value(nutrition_facts.get('protein', 0), 0.0),
                    "carbohydrates": safe_parse_nutrition_value(nutrition_facts.get('total_carbs', 0), 0.0),
                    "fat": safe_parse_nutrition_value(nutrition_facts.get('total_fat', 0), 0.0),
                    "fiber": safe_parse_nutrition_value(nutrition_facts.get('dietary_fiber', 0), 0.0),
                    "sugar": safe_parse_nutrition_value(nutrition_facts.get('total_sugars', 0), 0.0),
                    "sodium": safe_parse_nutrition_value(nutrition_facts.get('sodium', 0), 0.0)
                },
                "detailed_nutrition": nutrition_facts,
                "ingredients": data.get('ingredients', ''),
                "allergens": data.get('allergens', []),
                "serving_size": nutrition_facts.get('serving_size', ''),
                "ai_powered": True,
                "raw_data": data
            }
            
            return jsonify(response)
            
        except Exception as e:
            # Clean up file in case of error
            safe_file_cleanup(filepath)
            return jsonify({"error": f"Error extracting nutrition label: {str(e)}"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/food/predict-disease", methods=["POST"])
def predict_disease():
    """AI-powered health analysis and disease prediction endpoint"""
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["Ages", "Gender", "Height", "Weight", "Activity Level", 
                          "Dietary Preference", "Daily Calorie Target", "Protein", 
                          "Sugar", "Sodium", "Calories", "Carbohydrates", "Fiber", "Fat"]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {missing_fields}"}), 400
        
        # Get AI service
        ai_model = get_ai_service()
        if not ai_model:
            return jsonify({"error": "AI model service not available"}), 503
        
        # Create comprehensive health analysis prompt
        prompt = f"""
        Analyze the following health and nutritional data to provide a comprehensive health assessment:

        PERSONAL INFORMATION:
        - Age: {data['Ages']} years
        - Gender: {data['Gender']}
        - Height: {data['Height']} cm
        - Weight: {data['Weight']} kg
        - Activity Level: {data['Activity Level']}
        - Dietary Preference: {data['Dietary Preference']}

        DAILY NUTRITIONAL INTAKE:
        - Daily Calorie Target: {data['Daily Calorie Target']} kcal
        - Actual Calories: {data['Calories']} kcal
        - Protein: {data['Protein']} g
        - Carbohydrates: {data['Carbohydrates']} g
        - Fat: {data['Fat']} g
        - Fiber: {data['Fiber']} g
        - Sugar: {data['Sugar']} g
        - Sodium: {data['Sodium']} g

        Please provide a comprehensive health analysis in the following JSON format:
        {{
            "predicted_disease": "Primary health concern or 'Healthy' if no major risks",
            "confidence": confidence_percentage_as_number,
            "risk_level": "Low/Medium/High",
            "all_probabilities": {{
                "Diabetes": probability_percentage,
                "Heart Disease": probability_percentage,
                "Obesity": probability_percentage,
                "Hypertension": probability_percentage,
                "Malnutrition": probability_percentage,
                "Healthy": probability_percentage
            }},
            "recommendations": [
                "Specific dietary recommendation 1",
                "Specific exercise recommendation 2",
                "Specific lifestyle recommendation 3",
                "Specific monitoring recommendation 4",
                "Specific preventive measure 5"
            ],
            "bmi_analysis": "BMI calculation and interpretation",
            "calorie_balance": "Analysis of caloric intake vs needs",
            "nutrient_balance": "Analysis of macronutrient balance",
            "health_score": overall_health_score_out_of_100
        }}

        Base your analysis on established medical and nutritional guidelines. Consider BMI, caloric balance, nutrient ratios, activity level, and age-specific health risks.
        """
        
        try:
            # Get AI analysis
            analysis_result = ai_model.analyze_text(prompt)
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', analysis_result, re.DOTALL)
            if json_match:
                analysis_json = json.loads(json_match.group())
                
                # Ensure required fields exist and format properly for frontend
                raw_probabilities = analysis_json.get("all_probabilities", {})
                
                # Convert probabilities to decimal format (0-1) expected by frontend
                formatted_probabilities = {}
                for condition, prob in raw_probabilities.items():
                    # Convert to decimal if it's a percentage (>1), otherwise keep as is
                    prob_value = float(prob)
                    converted_prob = prob_value / 100.0 if prob_value > 1 else prob_value
                    formatted_probabilities[condition] = converted_prob
                
                # Handle confidence conversion
                raw_confidence = analysis_json.get("confidence", 75)
                confidence_value = float(raw_confidence)
                formatted_confidence = confidence_value / 100.0 if confidence_value > 1 else confidence_value
                
                result = {
                    "predicted_disease": analysis_json.get("predicted_disease", "Unknown"),
                    "confidence": formatted_confidence,
                    "risk_level": analysis_json.get("risk_level", "Medium"),
                    "all_probabilities": formatted_probabilities,
                    "recommendations": analysis_json.get("recommendations", [
                        "Maintain a balanced diet with adequate fruits and vegetables",
                        "Engage in regular physical activity as per your activity level",
                        "Monitor your weight and BMI regularly",
                        "Stay hydrated and limit processed foods",
                        "Consult healthcare providers for regular check-ups"
                    ]),
                    "bmi_analysis": analysis_json.get("bmi_analysis", "BMI analysis not available"),
                    "calorie_balance": analysis_json.get("calorie_balance", "Calorie balance analysis not available"),
                    "nutrient_balance": analysis_json.get("nutrient_balance", "Nutrient balance analysis not available"),
                    "health_score": int(analysis_json.get("health_score", 75))
                }
                
                return jsonify(result)
            else:
                # Fallback if JSON parsing fails
                return jsonify({
                    "predicted_disease": "Analysis Completed",
                    "confidence": 0.75,  # Decimal format for frontend
                    "risk_level": "Medium",
                    "all_probabilities": {
                        "Diabetes": 0.15,  # Convert to decimal format
                        "Heart Disease": 0.10,
                        "Obesity": 0.20,
                        "Hypertension": 0.12,
                        "Malnutrition": 0.08,
                        "Healthy": 0.35
                    },
                    "recommendations": [
                        "Maintain a balanced diet with adequate nutrients",
                        "Regular physical activity is recommended",
                        "Monitor your health metrics regularly",
                        "Consult healthcare providers for personalized advice",
                        "Stay consistent with healthy lifestyle choices"
                    ],
                    "bmi_analysis": f"BMI calculation based on height {data['Height']}cm and weight {data['Weight']}kg",
                    "calorie_balance": f"Daily intake: {data['Calories']} vs target: {data['Daily Calorie Target']}",
                    "nutrient_balance": "Balanced intake of proteins, carbs, and fats recommended",
                    "health_score": 75
                })
                
        except Exception as ai_error:
            print(f"AI analysis error: {ai_error}")
            # Return basic analysis if AI fails
            bmi = data['Weight'] / ((data['Height'] / 100) ** 2)
            
            if bmi < 18.5:
                primary_concern = "Underweight"
                risk_level = "Medium"
            elif bmi > 30:
                primary_concern = "Obesity"
                risk_level = "High"
            elif bmi > 25:
                primary_concern = "Overweight"
                risk_level = "Medium"
            else:
                primary_concern = "Healthy Weight"
                risk_level = "Low"
            
            return jsonify({
                "predicted_disease": primary_concern,
                "confidence": 0.70,  # Decimal format for frontend
                "risk_level": risk_level,
                "all_probabilities": {
                    "Diabetes": 0.12,  # Convert to decimal format
                    "Heart Disease": 0.08,
                    "Obesity": 0.25 if bmi > 25 else 0.05,
                    "Hypertension": 0.15,
                    "Malnutrition": 0.10 if bmi < 18.5 else 0.03,
                    "Healthy": 0.40 if 18.5 <= bmi <= 25 else 0.20
                },
                "recommendations": [
                    "Maintain a balanced diet with proper portion control",
                    "Engage in regular physical exercise",
                    "Monitor your BMI and weight regularly",
                    "Ensure adequate hydration",
                    "Consult with healthcare professionals for personalized advice"
                ],
                "bmi_analysis": f"Your BMI is {bmi:.1f}, classified as {primary_concern}",
                "calorie_balance": f"Daily intake: {data['Calories']} kcal vs target: {data['Daily Calorie Target']} kcal",
                "nutrient_balance": "Balanced macronutrient distribution recommended",
                "health_score": 85 if 18.5 <= bmi <= 25 else 65
            })
            
    except Exception as e:
        print(f"Health analysis error: {e}")
        return jsonify({"error": f"Health analysis failed: {str(e)}"}), 500

@app.route("/")
def home():
    return "Food Scanner API is running!"

@app.route("/health")
def health_check():
    ai_model = get_ai_service()
    return jsonify({
        "status": "healthy", 
        "message": "Food Scanner API is running",
        "ai_model_available": ai_model is not None,
        "endpoints": [
            "/api/ai_analyze - AI model food analysis",
            "/api/nutrition_scan - AI model nutrition label extraction",
            "/api/scan_label - Traditional OCR scanning",
            "/api/analyze_food - ML model analysis",
            "/food/predict-disease - AI health analysis and disease prediction"
        ]
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    
    print(f"🚀 Starting Food Scanner API on port {port}...")
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)