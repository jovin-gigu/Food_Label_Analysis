import { useState, useEffect } from "react";
import axios from "axios";

function FoodScanner() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [selectedFood, setSelectedFood] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState([]);
  const [healthyFoods, setHealthyFoods] = useState([]);
  const [labelAnalysis, setLabelAnalysis] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [activeTab, setActiveTab] = useState("search");

  useEffect(() => {
    fetchCategories();
    fetchHealthyFoods();
  }, []);

  const fetchCategories = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:5000/food/categories");
      setCategories(res.data.categories);
    } catch (err) {
      console.error("Error fetching categories:", err);
    }
  };

  const fetchHealthyFoods = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:5000/food/healthy?limit=5");
      setHealthyFoods(res.data.healthy_foods);
    } catch (err) {
      console.error("Error fetching healthy foods:", err);
    }
  };

  const searchFood = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const res = await axios.get(`http://127.0.0.1:5000/food/search?query=${encodeURIComponent(searchQuery)}`);
      setSearchResults(res.data.results);
    } catch (err) {
      console.error("Search error:", err);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const analyzeFood = async (foodName) => {
    setLoading(true);
    try {
      const res = await axios.post("http://127.0.0.1:5000/food/analyze", {
        food_name: foodName
      });
      setAnalysis(res.data);
      setSelectedFood(foodName);
    } catch (err) {
      console.error("Analysis error:", err);
      setAnalysis({ error: "Failed to analyze food item" });
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedImage(file);
      setLabelAnalysis(null);
    }
  };

  const analyzeLabel = async () => {
    if (!uploadedImage) return;
    
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadedImage);
      
      const res = await axios.post("http://127.0.0.1:5000/food/analyze-from-label", formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setLabelAnalysis(res.data);
    } catch (err) {
      console.error("Label analysis error:", err);
      setLabelAnalysis({ error: "Failed to analyze food label" });
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (risk) => {
    switch (risk?.toLowerCase()) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'moderate': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">🍎 Food Scanner</h2>
      
      {/* Tab Navigation */}
      <div className="flex justify-center mb-6">
        <div className="bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab("search")}
            className={`px-6 py-2 rounded-md font-semibold transition-colors ${
              activeTab === "search"
                ? "bg-white text-blue-600 shadow-sm"
                : "text-gray-600 hover:text-gray-800"
            }`}
          >
            🔍 Search Database
          </button>
          <button
            onClick={() => setActiveTab("scan")}
            className={`px-6 py-2 rounded-md font-semibold transition-colors ${
              activeTab === "scan"
                ? "bg-white text-blue-600 shadow-sm"
                : "text-gray-600 hover:text-gray-800"
            }`}
          >
            📷 Scan Label
          </button>
        </div>
      </div>

      {/* Search Tab */}
      {activeTab === "search" && (
        <>
      {/* Search Section */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h3 className="text-lg font-semibold mb-4">Search Food Items</h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter food name (e.g., 'apple', 'chicken', 'pizza')"
            className="flex-1 p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyPress={(e) => e.key === 'Enter' && searchFood()}
          />
          <button
            onClick={searchFood}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-3 rounded-md font-semibold"
          >
            {loading ? "🔍" : "Search"}
          </button>
        </div>
      </div>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-4">Search Results</h3>
          <div className="grid gap-3">
            {searchResults.map((food, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-md">
                <div>
                  <h4 className="font-semibold">{food.Food_Name}</h4>
                  <p className="text-sm text-gray-600">
                    {food.Food_Category} • {food.Calories_per_100g} cal/100g
                  </p>
                  <p className="text-xs text-gray-500">
                    Processing: {food.Processing_Level} • Density: {food.Nutritional_Density}
                  </p>
                </div>
                <button
                  onClick={() => analyzeFood(food.Food_Name)}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-semibold"
                >
                  Analyze
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-4">
            Analysis Results for: {selectedFood}
          </h3>
          
          {analysis.error ? (
            <div className="text-red-600">
              <p>❌ {analysis.error}</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded-md">
                  <h4 className="font-semibold text-gray-700">Health Risk</h4>
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getRiskColor(analysis.health_risk)}`}>
                    {analysis.health_risk}
                  </span>
                </div>
                
                <div className="text-center p-4 bg-gray-50 rounded-md">
                  <h4 className="font-semibold text-gray-700">Processing Level</h4>
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getRiskColor(analysis.processing_level)}`}>
                    {analysis.processing_level}
                  </span>
                </div>
                
                <div className="text-center p-4 bg-gray-50 rounded-md">
                  <h4 className="font-semibold text-gray-700">Nutritional Density</h4>
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getRiskColor(analysis.nutritional_density)}`}>
                    {analysis.nutritional_density}
                  </span>
                </div>
              </div>

              {analysis.recommendations && analysis.recommendations.length > 0 && (
                <div>
                  <h4 className="font-semibold text-gray-700 mb-2">Recommendations:</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {analysis.recommendations.map((rec, index) => (
                      <li key={index} className="text-gray-600">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Healthy Food Recommendations */}
      {healthyFoods.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-4">🥗 Healthy Food Recommendations</h3>
          <div className="grid gap-3">
            {healthyFoods.map((food, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-green-50 rounded-md">
                <div>
                  <h4 className="font-semibold text-green-800">{food.Food_Name}</h4>
                  <p className="text-sm text-green-600">
                    {food.Food_Category} • Density: {food.Nutritional_Density}
                  </p>
                </div>
                <span className="text-xs bg-green-200 text-green-800 px-2 py-1 rounded-full">
                  {food.Processing_Level}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
        </>
      )}

      {/* Label Scanning Tab */}
      {activeTab === "scan" && (
        <>
          {/* Image Upload Section */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold mb-4">📷 Upload Food Label Image</h3>
            <div className="space-y-4">
              <div>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-sm text-gray-500 mt-2">
                  Upload a clear photo of a food label or nutrition facts table
                </p>
              </div>
              
              {uploadedImage && (
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <p className="text-sm text-gray-600">
                      Selected: <span className="font-semibold">{uploadedImage.name}</span>
                    </p>
                  </div>
                  <button
                    onClick={analyzeLabel}
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-2 rounded-md font-semibold"
                  >
                    {loading ? "🔍 Analyzing..." : "📊 Analyze Label"}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Label Analysis Results */}
          {labelAnalysis && (
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold mb-4">📊 Label Analysis Results</h3>
              
              {labelAnalysis.error ? (
                <div className="text-red-600">
                  <p>❌ {labelAnalysis.error}</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Extracted Text */}
                  {labelAnalysis.label_reading?.extracted_text && (
                    <div>
                      <h4 className="font-semibold text-gray-700 mb-2">📝 Extracted Text:</h4>
                      <div className="bg-gray-50 p-3 rounded-md text-sm">
                        <pre className="whitespace-pre-wrap">{labelAnalysis.label_reading.extracted_text}</pre>
                      </div>
                    </div>
                  )}

                  {/* Nutritional Information */}
                  {labelAnalysis.label_reading?.nutritional_data && (
                    <div>
                      <h4 className="font-semibold text-gray-700 mb-2">🥗 Nutritional Information:</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {Object.entries(labelAnalysis.label_reading.nutritional_data).map(([key, value]) => (
                          <div key={key} className="bg-gray-50 p-3 rounded-md text-center">
                            <p className="text-sm text-gray-600 capitalize">{key.replace('_', ' ')}</p>
                            <p className="font-semibold">{value}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Health Analysis */}
                  {labelAnalysis.health_analysis && (
                    <div>
                      <h4 className="font-semibold text-gray-700 mb-2">🏥 Health Analysis:</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-gray-50 rounded-md">
                          <h5 className="font-semibold text-gray-700">Disease Risk</h5>
                          <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getRiskColor(labelAnalysis.health_analysis.predicted_disease)}`}>
                            {labelAnalysis.health_analysis.predicted_disease}
                          </span>
                        </div>
                        
                        <div className="text-center p-4 bg-gray-50 rounded-md">
                          <h5 className="font-semibold text-gray-700">Confidence</h5>
                          <p className="text-lg font-semibold text-blue-600">
                            {(labelAnalysis.health_analysis.confidence * 100).toFixed(1)}%
                          </p>
                        </div>
                        
                        <div className="text-center p-4 bg-gray-50 rounded-md">
                          <h5 className="font-semibold text-gray-700">Health Score</h5>
                          <p className="text-lg font-semibold text-green-600">
                            {labelAnalysis.health_analysis.nutritional_analysis?.health_score || 'N/A'}/100
                          </p>
                        </div>
                      </div>

                      {/* Recommendations */}
                      {labelAnalysis.health_analysis.nutritional_analysis?.recommendations && (
                        <div className="mt-4">
                          <h5 className="font-semibold text-gray-700 mb-2">💡 Recommendations:</h5>
                          <ul className="list-disc list-inside space-y-1">
                            {labelAnalysis.health_analysis.nutritional_analysis.recommendations.map((rec, index) => (
                              <li key={index} className="text-gray-600">{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default FoodScanner;

