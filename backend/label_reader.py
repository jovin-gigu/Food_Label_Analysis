import cv2
import pytesseract
import numpy as np
from PIL import Image
import re
import json

class FoodLabelReader:
    """OCR-based food label reader for extracting nutritional information"""
    
    def __init__(self):
        """Initialize the label reader"""
        # Configure tesseract path (you may need to adjust this)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def preprocess_image(self, image_path):
        """Preprocess image for better OCR results"""
        # Read image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply noise reduction
        denoised = cv2.medianBlur(gray, 3)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def extract_text_from_image(self, image_path):
        """Extract all text from food label image"""
        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path)
            
            # Use tesseract to extract text
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(processed_img, config=custom_config)
            
            return text.strip()
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
    
    def parse_nutritional_info(self, text):
        """Parse nutritional information from extracted text"""
        nutritional_data = {}
        
        # Common nutritional patterns
        patterns = {
            'calories': r'calories?\s*:?\s*(\d+)',
            'protein': r'protein\s*:?\s*(\d+(?:\.\d+)?)\s*g',
            'carbohydrates': r'carbohydrates?\s*:?\s*(\d+(?:\.\d+)?)\s*g',
            'carbs': r'carbs?\s*:?\s*(\d+(?:\.\d+)?)\s*g',
            'fat': r'total\s*fat\s*:?\s*(\d+(?:\.\d+)?)\s*g',
            'saturated_fat': r'saturated\s*fat\s*:?\s*(\d+(?:\.\d+)?)\s*g',
            'sugar': r'sugars?\s*:?\s*(\d+(?:\.\d+)?)\s*g',
            'sodium': r'sodium\s*:?\s*(\d+(?:\.\d+)?)\s*mg',
            'fiber': r'dietary\s*fiber\s*:?\s*(\d+(?:\.\d+)?)\s*g',
            'serving_size': r'serving\s*size\s*:?\s*([^\n]+)',
            'servings_per_container': r'servings?\s*per\s*container\s*:?\s*(\d+(?:\.\d+)?)'
        }
        
        text_lower = text.lower()
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                if key in ['serving_size']:
                    nutritional_data[key] = match.group(1).strip()
                else:
                    nutritional_data[key] = float(match.group(1))
        
        return nutritional_data
    
    def detect_food_category(self, text):
        """Detect food category based on text content"""
        text_lower = text.lower()
        
        categories = {
            'Whole Food': ['organic', 'natural', 'fresh', 'whole grain', 'unprocessed'],
            'Whole Grain': ['whole wheat', 'brown rice', 'quinoa', 'oats', 'whole grain'],
            'Lean Protein': ['chicken breast', 'fish', 'salmon', 'turkey', 'lean beef'],
            'Dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream'],
            'Fast Food': ['fried', 'burger', 'pizza', 'fries', 'fast food'],
            'Prepared Meal': ['frozen', 'microwave', 'ready to eat', 'prepared'],
            'Mixed': []  # Default category
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'Mixed'
    
    def estimate_processing_level(self, text):
        """Estimate processing level based on ingredients and text"""
        text_lower = text.lower()
        
        # High processing indicators
        high_processing = ['artificial', 'preservatives', 'additives', 'hydrogenated', 
                          'high fructose', 'corn syrup', 'modified', 'processed']
        
        # Low processing indicators
        low_processing = ['organic', 'natural', 'fresh', 'whole', 'unprocessed']
        
        high_score = sum(1 for indicator in high_processing if indicator in text_lower)
        low_score = sum(1 for indicator in low_processing if indicator in text_lower)
        
        # Calculate processing level (1-10, 1=least processed, 10=most processed)
        if low_score > high_score:
            return max(1, 10 - low_score)
        else:
            return min(10, 5 + high_score)
    
    def estimate_nutritional_density(self, nutritional_data):
        """Estimate nutritional density based on nutritional content"""
        if not nutritional_data:
            return 5  # Default middle value
        
        score = 10  # Start with perfect score
        
        # Penalize high sugar
        if 'sugar' in nutritional_data and nutritional_data['sugar'] > 15:
            score -= 3
        elif 'sugar' in nutritional_data and nutritional_data['sugar'] > 10:
            score -= 1
        
        # Penalize high sodium
        if 'sodium' in nutritional_data and nutritional_data['sodium'] > 400:
            score -= 2
        elif 'sodium' in nutritional_data and nutritional_data['sodium'] > 200:
            score -= 1
        
        # Reward high protein
        if 'protein' in nutritional_data and nutritional_data['protein'] > 20:
            score += 1
        
        # Reward high fiber
        if 'fiber' in nutritional_data and nutritional_data['fiber'] > 5:
            score += 1
        
        return max(1, min(10, score))
    
    def read_food_label(self, image_path):
        """Main method to read and analyze food label"""
        try:
            # Extract text from image
            text = self.extract_text_from_image(image_path)
            
            if not text:
                return {"error": "No text found in image"}
            
            # Parse nutritional information
            nutritional_data = self.parse_nutritional_info(text)
            
            # Detect food category
            category = self.detect_food_category(text)
            
            # Estimate processing level
            processing_level = self.estimate_processing_level(text)
            
            # Estimate nutritional density
            nutritional_density = self.estimate_nutritional_density(nutritional_data)
            
            # Calculate per 100g values if serving size is available
            per_100g_data = self.calculate_per_100g(nutritional_data)
            
            return {
                "extracted_text": text,
                "nutritional_data": nutritional_data,
                "per_100g_data": per_100g_data,
                "food_category": category,
                "processing_level": processing_level,
                "nutritional_density": nutritional_density,
                "analysis_complete": True
            }
            
        except Exception as e:
            return {"error": f"Error reading label: {str(e)}"}
    
    def calculate_per_100g(self, nutritional_data):
        """Calculate nutritional values per 100g"""
        per_100g = {}
        
        # This is a simplified calculation
        # In reality, you'd need to parse serving size and convert accordingly
        
        for key, value in nutritional_data.items():
            if key not in ['serving_size', 'servings_per_container'] and isinstance(value, (int, float)):
                # Assume standard serving size for calculation
                # You might want to make this more sophisticated
                per_100g[key] = value * 2  # Rough estimate
        
        return per_100g

def main():
    """Test the label reader"""
    reader = FoodLabelReader()
    
    # Test with a sample image (you'll need to provide an actual image)
    # result = reader.read_food_label("sample_food_label.jpg")
    # print(json.dumps(result, indent=2))
    
    print("Food Label Reader initialized successfully!")
    print("Ready to read food labels and extract nutritional information.")

if __name__ == "__main__":
    main()
