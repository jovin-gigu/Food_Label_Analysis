from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd

app = Flask(__name__)
CORS(app)

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

# Load model and encoders
model = pickle.load(open("models/food_analysis_model.pkl", "rb"))
label_encoder_y = pickle.load(open("models/food_label_encoder_y.pkl", "rb"))
label_encoders = pickle.load(open("models/food_feature_encoders.pkl", "rb"))
feature_cols = pickle.load(open("models/food_feature_names.pkl", "rb"))
food_db = pd.read_csv("data/food_database_fixed.csv")

@app.route("/api/search_food", methods=["GET"])
def search_food():
    query = request.args.get("query", "")
    matches = food_db[food_db['Food_Name'].str.lower().str.contains(query.lower(), na=False)]
    return matches[['Food_Name', 'Food_Category', 'Calories_per_100g']].head(10).to_json(orient="records")

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

@app.route("/")
def home():
    return "Food Scanner API is running!"

if __name__ == "__main__":
    print("🚀 Starting Food Scanner API...")
    app.run(debug=True)