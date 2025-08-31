import pickle
import pandas as pd
from sklearn.preprocessing import LabelEncoder

def load_model_and_encoders():
    """Load the trained model and label encoders"""
    model = pickle.load(open("models/xgboost_model.pkl", "rb"))
    label_encoder_y = pickle.load(open("models/label_encoder_y.pkl", "rb"))
    return model, label_encoder_y

def encode_categorical_features(test_df, original_df):
    """Encode categorical features using the same encoding as training"""
    encoded_df = test_df.copy()
    categorical_cols = encoded_df.select_dtypes(include=["object"]).columns
    
    for col in categorical_cols:
        if col in original_df.columns:
            le = LabelEncoder()
            le.fit(original_df[col].astype(str))
            encoded_df[col] = le.transform(encoded_df[col].astype(str))
    
    return encoded_df

def test_single_prediction():
    """Test a single custom prediction (original functionality)"""
    print("🎯 Single Custom Prediction Test:")
    print("=" * 50)
    
    # Load model and encoders
    model, label_encoder_y = load_model_and_encoders()
    
    # Load dataset to get column names
    df = pd.read_csv("data/custom_nutrition_dataset.csv")
    feature_cols = [c for c in df.columns if c != "Disease"]

    # Prepare a sample row with defaults
    sample = pd.DataFrame([df[feature_cols].iloc[0].copy()])  # copy first row to keep types

    # Now override only the values you want
    sample["Ages"] = 25
    sample["Gender"] = df["Gender"].mode()[0]   # use the most common gender
    sample["Calories"] = 2000
    sample["Protein"] = 80

    # Ensure dtypes are same as training
    for col in sample.columns:
        sample[col] = sample[col].astype(df[col].dtype)

    # Encode categorical features
    encoded_sample = encode_categorical_features(sample, df)

    # Predict
    pred = model.predict(encoded_sample)
    probabilities = model.predict_proba(encoded_sample)[0]
    max_prob = max(probabilities)
    
    print(f"Input: 25yo {df['Gender'].mode()[0]}, 2000 cal, 80g protein")
    print(f"🎯 Predicted disease: {label_encoder_y.inverse_transform(pred)[0]}")
    print(f"📈 Confidence: {max_prob:.2%}")

def test_comprehensive_cases():
    """Test multiple comprehensive test cases"""
    print("\n🔬 Comprehensive Test Cases:")
    print("=" * 60)
    
    # Load model and encoders
    model, label_encoder_y = load_model_and_encoders()
    df = pd.read_csv("data/custom_nutrition_dataset.csv")
    feature_cols = [c for c in df.columns if c != "Disease"]
    
    # Test cases covering different scenarios
    test_cases = [
        {
            "name": "Young Active Male (High Risk)",
            "data": {
                "Ages": 25, "Gender": "Male", "Height": 180, "Weight": 90,
                "Activity Level": "Very Active", "Dietary Preference": "Omnivore",
                "Daily Calorie Target": 3000, "Protein": 150, "Sugar": 200.0, "Sodium": 35.0,
                "Calories": 3200, "Carbohydrates": 400, "Fiber": 45.0, "Fat": 100,
                "Breakfast Suggestion": "Oatmeal with protein powder and fruit", "Breakfast Calories": 400.0,
                "Breakfast Protein": 30.0, "Breakfast Carbohydrates": 50.0, "Breakfast Fats": 15.0,
                "Lunch Suggestion": "Chicken breast with brown rice and vegetables", "Lunch Calories": 600.0,
                "Lunch Protein": 50.0, "Lunch Carbohydrates": 60.0,
                "Dinner Suggestion": "Steak with roasted vegetables", "Dinner Calories": 800.0,
                "Dinner Protein.1": 60.0, "Dinner Carbohydrates.1": 40.0, "Dinner Fats": 35.0,
                "Snack Suggestion": "Protein shake", "Snacks Calories": 200.0,
                "Snacks Protein": 25.0, "Snacks Carbohydrates": 15.0, "Snacks Fats": 5.0,
                "Lunch Fats": 20.0
            }
        },
        {
            "name": "Middle-aged Sedentary Female (Multiple Risk)",
            "data": {
                "Ages": 55, "Gender": "Female", "Height": 160, "Weight": 80,
                "Activity Level": "Sedentary", "Dietary Preference": "Omnivore",
                "Daily Calorie Target": 1500, "Protein": 60, "Sugar": 150.0, "Sodium": 30.0,
                "Calories": 1800, "Carbohydrates": 250, "Fiber": 20.0, "Fat": 70,
                "Breakfast Suggestion": "Scrambled eggs with whole wheat toast and avocado", "Breakfast Calories": 300.0,
                "Breakfast Protein": 8.0, "Breakfast Carbohydrates": 45.0, "Breakfast Fats": 12.0,
                "Lunch Suggestion": "Turkey sandwich on whole wheat bread with vegetables", "Lunch Calories": 500.0,
                "Lunch Protein": 20.0, "Lunch Carbohydrates": 60.0,
                "Dinner Suggestion": "Vegetarian chili with cornbread", "Dinner Calories": 600.0,
                "Dinner Protein.1": 25.0, "Dinner Carbohydrates.1": 80.0, "Dinner Fats": 25.0,
                "Snack Suggestion": "Greek yogurt with fruit", "Snacks Calories": 200.0,
                "Snacks Protein": 3.0, "Snacks Carbohydrates": 30.0, "Snacks Fats": 8.0,
                "Lunch Fats": 15.0
            }
        },
        {
            "name": "Young Vegan Female (Healthy Lifestyle)",
            "data": {
                "Ages": 28, "Gender": "Female", "Height": 165, "Weight": 55,
                "Activity Level": "Moderately Active", "Dietary Preference": "Vegan",
                "Daily Calorie Target": 2000, "Protein": 80, "Sugar": 100.0, "Sodium": 20.0,
                "Calories": 1900, "Carbohydrates": 250, "Fiber": 35.0, "Fat": 60,
                "Breakfast Suggestion": "Overnight oats with fruit and chia seeds", "Breakfast Calories": 350.0,
                "Breakfast Protein": 12.0, "Breakfast Carbohydrates": 55.0, "Breakfast Fats": 8.0,
                "Lunch Suggestion": "Quinoa salad with chickpeas and vegetables", "Lunch Calories": 400.0,
                "Lunch Protein": 15.0, "Lunch Carbohydrates": 60.0,
                "Dinner Suggestion": "Lentil and vegetable curry", "Dinner Calories": 500.0,
                "Dinner Protein.1": 25.0, "Dinner Carbohydrates.1": 80.0, "Dinner Fats": 15.0,
                "Snack Suggestion": "Apple with almond butter", "Snacks Calories": 200.0,
                "Snacks Protein": 6.0, "Snacks Carbohydrates": 25.0, "Snacks Fats": 10.0,
                "Lunch Fats": 12.0
            }
        },
        {
            "name": "Elderly Male (High Sodium Risk)",
            "data": {
                "Ages": 70, "Gender": "Male", "Height": 170, "Weight": 75,
                "Activity Level": "Lightly Active", "Dietary Preference": "Omnivore",
                "Daily Calorie Target": 1800, "Protein": 70, "Sugar": 120.0, "Sodium": 40.0,
                "Calories": 2000, "Carbohydrates": 220, "Fiber": 25.0, "Fat": 65,
                "Breakfast Suggestion": "Scrambled eggs with whole wheat toast and avocado", "Breakfast Calories": 400.0,
                "Breakfast Protein": 20.0, "Breakfast Carbohydrates": 10.0, "Breakfast Fats": 30.0,
                "Lunch Suggestion": "Turkey sandwich on whole wheat bread with vegetables", "Lunch Calories": 500.0,
                "Lunch Protein": 25.0, "Lunch Carbohydrates": 50.0,
                "Dinner Suggestion": "Chicken and vegetable stir-fry", "Dinner Calories": 700.0,
                "Dinner Protein.1": 35.0, "Dinner Carbohydrates.1": 60.0, "Dinner Fats": 30.0,
                "Snack Suggestion": "Trail mix", "Snacks Calories": 200.0,
                "Snacks Protein": 8.0, "Snacks Carbohydrates": 10.0, "Snacks Fats": 15.0,
                "Lunch Fats": 20.0
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test_case['name']}")
        
        # Create DataFrame for this test case
        test_df = pd.DataFrame([test_case['data']])
        
        # Ensure all columns are present and in correct order
        for col in feature_cols:
            if col not in test_df.columns:
                test_df[col] = df[col].mode()[0]
        
        test_df = test_df[feature_cols]
        
        # Encode categorical features
        encoded_test_df = encode_categorical_features(test_df, df)
        
        # Make prediction
        try:
            prediction = model.predict(encoded_test_df)
            predicted_disease = label_encoder_y.inverse_transform(prediction)[0]
            probabilities = model.predict_proba(encoded_test_df)[0]
            max_prob = max(probabilities)
            
            print(f"   Demographics: {test_case['data']['Ages']}yo {test_case['data']['Gender']}, {test_case['data']['Height']}cm, {test_case['data']['Weight']}kg")
            print(f"   Lifestyle: {test_case['data']['Activity Level']}, {test_case['data']['Dietary Preference']}")
            print(f"   Nutrition: {test_case['data']['Calories']} cal, {test_case['data']['Protein']}g protein, {test_case['data']['Sodium']}g sodium")
            print(f"   🎯 Predicted Disease: {predicted_disease}")
            print(f"   📈 Confidence: {max_prob:.2%}")
            
        except Exception as e:
            print(f"   ❌ Error in prediction: {str(e)}")
        
        print("-" * 50)

def test_from_csv():
    """Test predictions from the test_data_samples.csv file"""
    print("\n📁 Testing from CSV file:")
    print("=" * 40)
    
    try:
        # Load model and encoders
        model, label_encoder_y = load_model_and_encoders()
        original_df = pd.read_csv("data/custom_nutrition_dataset.csv")
        feature_cols = [c for c in original_df.columns if c != "Disease"]
        
        # Load test data
        test_df = pd.read_csv("data/test_data_samples.csv")
        
        print(f"Testing {len(test_df)} samples from CSV...")
        
        for i, row in test_df.iterrows():
            # Remove the Disease column if it exists (it's the target)
            if 'Disease' in row:
                row = row.drop('Disease')
            
            # Create DataFrame for this row
            sample_df = pd.DataFrame([row])
            sample_df = sample_df[feature_cols]
            
            # Encode categorical features
            encoded_sample = encode_categorical_features(sample_df, original_df)
            
            # Make prediction
            prediction = model.predict(encoded_sample)
            predicted_disease = label_encoder_y.inverse_transform(prediction)[0]
            probabilities = model.predict_proba(encoded_sample)[0]
            max_prob = max(probabilities)
            
            print(f"Sample {i+1}: {row['Ages']}yo {row['Gender']}, {row['Activity Level']} → {predicted_disease} ({max_prob:.1%})")
            
    except FileNotFoundError:
        print("❌ data/test_data_samples.csv not found. The test data file should be in the data folder.")
    except Exception as e:
        print(f"❌ Error testing from CSV: {str(e)}")

if __name__ == "__main__":
    try:
        # Run all tests
        test_single_prediction()
        test_comprehensive_cases()
        test_from_csv()
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Error running tests: {str(e)}")
        print("Make sure the model files exist in the models/ directory")

