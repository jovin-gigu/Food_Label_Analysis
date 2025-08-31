import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os

def train_user_model():
    print("🔵 Training user nutrition model...")
    df = pd.read_csv("data/custom_nutrition_dataset.csv")
    target_col = "Disease"
    X = df.drop(columns=[target_col])
    y = df[target_col]
    for col in X.select_dtypes(include=["object"]).columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
    label_encoder_y = LabelEncoder()
    y = label_encoder_y.fit_transform(y.astype(str))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = XGBClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        use_label_encoder=False,
        eval_metric="mlogloss"
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print("\n✅ Accuracy:", accuracy_score(y_test, y_pred))
    print("\n📊 Classification Report:\n", classification_report(y_test, y_pred))
    os.makedirs("models", exist_ok=True)
    pickle.dump(model, open("models/xgboost_model.pkl", "wb"))
    pickle.dump(label_encoder_y, open("models/label_encoder_y.pkl", "wb"))
    print("\n💾 User model saved to models/xgboost_model.pkl")
    print("💾 User target label encoder saved to models/label_encoder_y.pkl")

def train_food_model():
    print("🍎 Training food label model...")
    df = pd.read_csv("data/food_database_fixed.csv")
    target_col = "Disease_Risk"
    feature_cols = [col for col in df.columns if col not in [target_col, 'Food_Name']]
    X = df[feature_cols]
    y = df[target_col]
    categorical_cols = X.select_dtypes(include=["object"]).columns
    label_encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        label_encoders[col] = le
    label_encoder_y = LabelEncoder()
    y = label_encoder_y.fit_transform(y.astype(str))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = XGBClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        use_label_encoder=False,
        eval_metric="mlogloss"
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print(f"\n✅ Model Accuracy: {accuracy_score(y_test, y_pred):.3f}")
    print(f"\n📊 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=label_encoder_y.classes_))
    os.makedirs("models", exist_ok=True)
    pickle.dump(model, open("models/food_analysis_model.pkl", "wb"))
    pickle.dump(label_encoder_y, open("models/food_label_encoder_y.pkl", "wb"))
    pickle.dump(label_encoders, open("models/food_feature_encoders.pkl", "wb"))
    pickle.dump(feature_cols, open("models/food_feature_names.pkl", "wb"))
    print(f"\n💾 Food model saved to models/food_analysis_model.pkl")
    print(f"💾 Food target encoder saved to models/food_label_encoder_y.pkl")
    print(f"💾 Food feature encoders saved to models/food_feature_encoders.pkl")
    print(f"💾 Food feature names saved to models/food_feature_names.pkl")

if __name__ == "__main__":
    print("Select model to train:")
    print("1. User nutrition model")
    print("2. Food label model")
    choice = input("Enter 1 or 2: ").strip()
    if choice == "1":
        train_user_model()
    elif choice == "2":
        train_food_model()
    else:
        print("Invalid choice.")