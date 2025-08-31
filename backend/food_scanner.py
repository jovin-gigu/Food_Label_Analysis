import pandas as pd
import pickle
from sklearn.preprocessing import LabelEncoder

class FoodScanner:
    """Interactive Food Scanner for disease risk analysis"""

    def __init__(self):
        """Initialize the food scanner with trained models and database"""
        self.model = None
        self.label_encoder_y = None
        self.food_db = None
        self.encoders = {}
        self.load_models()
        self.load_food_database()

    def load_models(self):
        """Load the trained food analysis model and encoders"""
        try:
            self.model = pickle.load(open("models/xgboost_model.pkl", "rb"))
            self.label_encoder_y = pickle.load(open("models/label_encoder_y.pkl", "rb"))
            # Optionally load feature encoders if needed
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            self.model = None
            self.label_encoder_y = None

    def load_food_database(self):
        """Load the food database"""
        try:
            self.food_db = pd.read_csv("data/food_database.csv")
        except Exception as e:
            print(f"❌ Error loading food database: {e}")
            self.food_db = None

    def search_food(self, query):
        """Search for food items in the database"""
        if self.food_db is None:
            return pd.DataFrame()
        query = query.lower()
        matches = self.food_db[
            self.food_db['Food_Name'].str.lower().str.contains(query, na=False)
        ]
        return matches[['Food_Name', 'Food_Category', 'Calories_per_100g', 'Processing_Level', 'Nutritional_Density']].head(10)

    def analyze_food_item(self, food_name=None, nutritional_data=None):
        """Analyze a food item for disease risk"""
        if self.model is None or self.label_encoder_y is None:
            return {"error": "Model not loaded"}

        # If food_name provided, get from database
        if food_name and self.food_db is not None:
            row = self.food_db[self.food_db['Food_Name'].str.lower() == food_name.lower()]
            if not row.empty:
                nutritional_data = row.iloc[0].to_dict()

        # If nutritional_data is still None, return error
        if nutritional_data is None:
            return {"error": "No nutritional data provided"}

        # Prepare DataFrame
        df = pd.DataFrame([nutritional_data])

        # Encode categorical features if needed
        for col in df.select_dtypes(include=["object"]).columns:
            if col in self.food_db.columns:
                le = LabelEncoder()
                le.fit(self.food_db[col].astype(str))
                df[col] = le.transform(df[col].astype(str))

        # Make prediction
        try:
            pred = self.model.predict(df)
            probabilities = self.model.predict_proba(df)[0]
            max_prob = max(probabilities)
            predicted_disease = self.label_encoder_y.inverse_transform(pred)[0]
            all_probs = dict(zip(self.label_encoder_y.classes_, probabilities))
            analysis = self.get_nutritional_analysis(nutritional_data)
            return {
                "food_name": food_name or nutritional_data.get("Food_Name", "Unknown"),
                "predicted_disease": predicted_disease,
                "confidence": max_prob,
                "all_probabilities": all_probs,
                "nutritional_analysis": analysis
            }
        except Exception as e:
            return {"error": f"Prediction error: {e}"}

    def get_nutritional_analysis(self, nutritional_data):
        """Provide nutritional analysis and recommendations"""
        analysis = {
            "health_score": 0,
            "concerns": [],
            "recommendations": []
        }
        score = 100

        # Processing level impact
        if nutritional_data.get('Processing_Level', 0) > 7:
            score -= 25
            analysis["concerns"].append("Highly processed food")
        elif nutritional_data.get('Processing_Level', 0) > 5:
            score -= 10
            analysis["concerns"].append("Moderately processed food")

        # Nutritional density impact
        if nutritional_data.get('Nutritional_Density', 10) < 5:
            score -= 15
            analysis["concerns"].append("Low nutritional density")

        # Sugar content
        if nutritional_data.get('Sugar_per_100g', 0) > 15:
            score -= 15
            analysis["concerns"].append("High sugar content")
        elif nutritional_data.get('Sugar_per_100g', 0) > 10:
            score -= 7
            analysis["concerns"].append("Moderate sugar content")

        # Sodium content
        if nutritional_data.get('Sodium_per_100g', 0) > 400:
            score -= 15
            analysis["concerns"].append("Very high sodium content")
        elif nutritional_data.get('Sodium_per_100g', 0) > 200:
            score -= 7
            analysis["concerns"].append("Moderate sodium content")

        # Fat content
        if nutritional_data.get('Fat_per_100g', 0) > 20:
            score -= 10
            analysis["concerns"].append("High fat content")

        # Fiber content
        if nutritional_data.get('Fiber_per_100g', 10) < 3:
            score -= 10
            analysis["concerns"].append("Low fiber content")

        # Additives
        if nutritional_data.get('Additives_Count', 0) > 5:
            score -= 10
            analysis["concerns"].append("Contains many additives")

        analysis["health_score"] = max(0, score)

        # Generate recommendations
        if score < 50:
            analysis["recommendations"].append("Consider healthier alternatives with less processing and additives.")
        if nutritional_data.get('Processing_Level', 0) > 5:
            analysis["recommendations"].append("Choose less processed foods.")
        if nutritional_data.get('Sugar_per_100g', 0) > 10:
            analysis["recommendations"].append("Reduce sugar intake.")
        if nutritional_data.get('Sodium_per_100g', 0) > 200:
            analysis["recommendations"].append("Reduce sodium intake.")

        return analysis

    def get_food_categories(self):
        """Get all available food categories"""
        if self.food_db is None:
            return []
        return self.food_db['Food_Category'].unique().tolist()

    def get_top_healthy_foods(self, category=None, limit=10):
        """Get top healthy foods from database"""
        if self.food_db is None:
            return pd.DataFrame()
        df = self.food_db.copy()
        if category:
            df = df[df['Food_Category'] == category]
        df = df.sort_values(['Nutritional_Density', 'Processing_Level'], ascending=[False, True])
        return df[['Food_Name', 'Food_Category', 'Nutritional_Density', 'Processing_Level']].head(limit)

def main():
    """Interactive command-line interface for food scanning"""
    scanner = FoodScanner()
    
    if scanner.model is None:
        print("❌ Cannot start scanner - models not loaded")
        return
    
    print("\n🍎 Food Label Analysis Tool")
    print("=" * 50)
    
    while True:
        print("\n📋 Options:")
        print("1. Search food in database")
        print("2. Analyze food by name")
        print("3. Manual nutritional input")
        print("4. View food categories")
        print("5. Get healthy food recommendations")
        print("6. Exit")
        
        choice = input("\n🎯 Choose an option (1-6): ").strip()
        
        if choice == "1":
            query = input("🔍 Enter food name to search: ").strip()
            results = scanner.search_food(query)
            if len(results) > 0:
                print(f"\n📊 Found {len(results)} results:")
                print(results.to_string(index=False))
            else:
                print("❌ No results found")
        
        elif choice == "2":
            food_name = input("🍎 Enter exact food name: ").strip()
            result = scanner.analyze_food_item(food_name=food_name)
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                print_analysis_result(result)
        
        elif choice == "3":
            print("\n📝 Enter nutritional information (per 100g):")
            nutritional_data = {}
            
            nutritional_data['Food_Category'] = input("Food Category (Whole Food/Whole Grain/Lean Protein/Dairy/Fast Food/Prepared Meal/Mixed): ").strip()
            nutritional_data['Calories_per_100g'] = float(input("Calories: ") or 0)
            nutritional_data['Protein_per_100g'] = float(input("Protein (g): ") or 0)
            nutritional_data['Carbs_per_100g'] = float(input("Carbohydrates (g): ") or 0)
            nutritional_data['Fat_per_100g'] = float(input("Fat (g): ") or 0)
            nutritional_data['Fiber_per_100g'] = float(input("Fiber (g): ") or 0)
            nutritional_data['Sugar_per_100g'] = float(input("Sugar (g): ") or 0)
            nutritional_data['Sodium_per_100g'] = float(input("Sodium (mg): ") or 0)
            nutritional_data['Processing_Level'] = int(input("Processing Level (1-10, 1=whole food, 10=highly processed): ") or 5)
            nutritional_data['Nutritional_Density'] = int(input("Nutritional Density (1-10, 10=most nutritious): ") or 5)
            nutritional_data['Glycemic_Index'] = int(input("Glycemic Index (0-100): ") or 50)
            nutritional_data['Additives_Count'] = int(input("Number of additives: ") or 0)
            
            result = scanner.analyze_food_item(nutritional_data=nutritional_data)
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                print_analysis_result(result)
        
        elif choice == "4":
            categories = scanner.get_food_categories()
            print(f"\n📂 Available categories: {', '.join(categories)}")
        
        elif choice == "5":
            category = input("📂 Enter category (or press Enter for all): ").strip() or None
            healthy_foods = scanner.get_top_healthy_foods(category=category)
            print(f"\n🥗 Top healthy foods:")
            print(healthy_foods.to_string(index=False))
        
        elif choice == "6":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")

def print_analysis_result(result):
    """Print the analysis result in a formatted way"""
    print(f"\n🍎 Analysis for: {result['food_name']}")
    print("=" * 50)
    print(f"🎯 Predicted Disease Risk: {result['predicted_disease']}")
    print(f"📈 Confidence: {result['confidence']:.1%}")
    
    print(f"\n📊 All Risk Probabilities:")
    for disease, prob in result['all_probabilities'].items():
        print(f"   {disease}: {prob:.1%}")
    
    analysis = result['nutritional_analysis']
    print(f"\n🏥 Health Score: {analysis['health_score']}/100")
    
    if analysis['concerns']:
        print(f"\n⚠️  Concerns:")
        for concern in analysis['concerns']:
            print(f"   • {concern}")
    
    if analysis['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"   • {rec}")

if __name__ == "__main__":
    main()


