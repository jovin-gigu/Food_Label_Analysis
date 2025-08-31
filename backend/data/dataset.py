import pandas as pd

# === Load your datasets ===
demographic = pd.read_csv("demographic.csv")
diet = pd.read_csv("diet.csv")
examination = pd.read_csv("examination.csv")
labs = pd.read_csv("labs.csv")
medications = pd.read_csv("medications.csv", encoding="latin1")

# Optional / reference datasets (can enrich later if needed)
food_macros = pd.read_csv("detailed_meals_macros_CLEANED.csv")
food_nutrition = pd.read_csv("Food_and_Nutrition__.csv")

# === 1. NHANES-style Master Dataset (union/merged) ===
# Common key is usually "SEQN" (participant ID). Adjust if different.
nhanes_master = demographic.merge(diet, on="SEQN", how="inner") \
                           .merge(examination, on="SEQN", how="inner") \
                           .merge(labs, on="SEQN", how="inner") \
                           .merge(medications, on="SEQN", how="left")

# Save NHANES-style dataset
nhanes_master.to_csv("nhanes_master_dataset.csv", index=False)
print("✅ NHANES-style master dataset saved as nhanes_master_dataset.csv")

# === 2. Custom Nutrition Dataset ===
# Combine cleaned macros + nutrition info
custom_nutrition = pd.concat([food_macros, food_nutrition], ignore_index=True)

# Save Custom Nutrition dataset
custom_nutrition.to_csv("custom_nutrition_dataset.csv", index=False)
print("✅ Custom nutrition dataset saved as custom_nutrition_dataset.csv")
