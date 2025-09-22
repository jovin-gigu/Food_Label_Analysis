'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, Utensils, Info, TrendingUp, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';

interface FoodItem {
  'Food Name': string;
  Category: string;
  'Processing Level': string;
  'Nutritional Density': string;
  Calories: number;
  Protein: number;
  Carbohydrates: number;
  Fat: number;
  Fiber: number;
  Sugar: number;
  Sodium: number;
  'Vitamin C': number;
  'Vitamin A': number;
  Calcium: number;
  Iron: number;
  Potassium: number;
  Magnesium: number;
  Zinc: number;
}

interface FoodCategories {
  categories: string[];
}

export default function FoodSearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<FoodItem[]>([]);
  const [selectedFood, setSelectedFood] = useState<FoodItem | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [healthyFoods, setHealthyFoods] = useState<FoodItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load categories and healthy foods on component mount
  useEffect(() => {
    loadCategories();
    loadHealthyFoods();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/food/categories');
      if (response.ok) {
        const data: FoodCategories = await response.json();
        setCategories(data.categories);
      }
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadHealthyFoods = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/food/healthy?limit=6');
      if (response.ok) {
        const data = await response.json();
        setHealthyFoods(data.healthy_foods || []);
      }
    } catch (error) {
      console.error('Error loading healthy foods:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast.error('Please enter a search query');
      return;
    }

    setIsLoading(true);
    try {
      let url = `http://127.0.0.1:5000/food/search?query=${encodeURIComponent(searchQuery)}`;
      if (selectedCategory !== 'all') {
        url += `&category=${encodeURIComponent(selectedCategory)}`;
      }

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSearchResults(data.results || []);
      
      if (data.results?.length === 0) {
        toast.info('No foods found matching your search criteria');
      } else {
        toast.success(`Found ${data.results?.length || 0} foods`);
      }
    } catch (error) {
      console.error('Search error:', error);
      toast.error('Failed to search foods. Make sure the backend server is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeFood = async (foodName: string) => {
    try {
      const response = await fetch('${process.env.NEXT_PUBLIC_BACKEND_URL}/food/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ food_name: foodName }),
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedFood(data.food_info);
        toast.success('Food analyzed successfully');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      toast.error('Failed to analyze food');
    }
  };

  const getProcessingLevelColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'unprocessed': return 'bg-green-500';
      case 'minimally processed': return 'bg-yellow-500';
      case 'processed': return 'bg-orange-500';
      case 'ultra-processed': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getNutritionalDensityColor = (density: string) => {
    switch (density?.toLowerCase()) {
      case 'high': return 'text-green-600 bg-green-50 dark:bg-green-950/20';
      case 'medium': return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950/20';
      case 'low': return 'text-red-600 bg-red-50 dark:bg-red-950/20';
      default: return 'text-gray-600 bg-gray-50 dark:bg-gray-950/20';
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center mb-4">
            <Search className="h-12 w-12 text-green-600 mr-4" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              Food Database Search
            </h1>
          </div>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Explore our comprehensive database of nutritional information
          </p>
        </motion.div>

        {/* Search Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mb-12"
        >
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Utensils className="h-5 w-5 mr-2 text-green-600" />
                Search Foods
              </CardTitle>
              <CardDescription>
                Search through our database of thousands of food items
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <Input
                    placeholder="Search for foods (e.g., apple, chicken breast, quinoa...)"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="text-base"
                  />
                </div>
                <div className="md:w-48">
                  <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                    <SelectTrigger>
                      <Filter className="h-4 w-4 mr-2" />
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Categories</SelectItem>
                      {categories.map((category) => (
                        <SelectItem key={category} value={category}>
                          {category}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button 
                  onClick={handleSearch} 
                  size="lg" 
                  disabled={isLoading}
                  className="md:px-8"
                >
                  {isLoading ? 'Searching...' : 'Search'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Search Results */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="lg:col-span-2"
          >
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>Search Results</CardTitle>
                <CardDescription>
                  {searchResults.length > 0 ? `Found ${searchResults.length} results` : 'Enter a search query to find foods'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {searchResults.length === 0 && !isLoading && (
                  <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                    <Search className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <p className="text-lg">No search results yet</p>
                    <p className="text-sm">Try searching for foods like "apple", "chicken", or "quinoa"</p>
                  </div>
                )}

                {isLoading && (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
                    <p className="text-lg text-gray-600 dark:text-gray-300">Searching foods...</p>
                  </div>
                )}

                <div className="space-y-4">
                  {searchResults.map((food, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                      className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => setSelectedFood(food)}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {food['Food Name']}
                        </h3>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            analyzeFood(food['Food Name']);
                          }}
                        >
                          <Info className="h-4 w-4 mr-1" />
                          Analyze
                        </Button>
                      </div>
                      
                      <div className="flex flex-wrap gap-2 mb-3">
                        <Badge variant="outline">{food.Category}</Badge>
                        <Badge className={getNutritionalDensityColor(food['Nutritional Density'])}>
                          {food['Nutritional Density']} Density
                        </Badge>
                        <Badge variant="outline" className="relative">
                          <div className={`w-2 h-2 rounded-full ${getProcessingLevelColor(food['Processing Level'])} mr-2`} />
                          {food['Processing Level']}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-gray-600 dark:text-gray-300">
                        <span>Calories: {food.Calories}</span>
                        <span>Protein: {food.Protein}g</span>
                        <span>Carbs: {food.Carbohydrates}g</span>
                        <span>Fat: {food.Fat}g</span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Detailed View & Recommendations */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="space-y-6"
          >
            {/* Food Detail */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>Food Details</CardTitle>
                <CardDescription>
                  Click on a food item to see detailed nutritional information
                </CardDescription>
              </CardHeader>
              <CardContent>
                {selectedFood ? (
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                        {selectedFood['Food Name']}
                      </h3>
                      <div className="flex flex-wrap gap-2 mb-4">
                        <Badge variant="outline">{selectedFood.Category}</Badge>
                        <Badge className={getNutritionalDensityColor(selectedFood['Nutritional Density'])}>
                          {selectedFood['Nutritional Density']} Density
                        </Badge>
                      </div>
                    </div>

                    {/* Macronutrients */}
                    <div>
                      <h4 className="font-semibold mb-3">Macronutrients (per 100g)</h4>
                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Calories</span>
                            <span>{selectedFood.Calories}</span>
                          </div>
                          <Progress value={(selectedFood.Calories / 600) * 100} className="h-2" />
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Protein</span>
                            <span>{selectedFood.Protein}g</span>
                          </div>
                          <Progress value={(selectedFood.Protein / 30) * 100} className="h-2" />
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Carbohydrates</span>
                            <span>{selectedFood.Carbohydrates}g</span>
                          </div>
                          <Progress value={(selectedFood.Carbohydrates / 50) * 100} className="h-2" />
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Fat</span>
                            <span>{selectedFood.Fat}g</span>
                          </div>
                          <Progress value={(selectedFood.Fat / 25) * 100} className="h-2" />
                        </div>
                      </div>
                    </div>

                    {/* Micronutrients */}
                    <div>
                      <h4 className="font-semibold mb-3">Key Nutrients</h4>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>Fiber: {selectedFood.Fiber}g</div>
                        <div>Sugar: {selectedFood.Sugar}g</div>
                        <div>Sodium: {selectedFood.Sodium}mg</div>
                        <div>Vitamin C: {selectedFood['Vitamin C']}mg</div>
                        <div>Calcium: {selectedFood.Calcium}mg</div>
                        <div>Iron: {selectedFood.Iron}mg</div>
                      </div>
                    </div>

                    {/* Processing Level Indicator */}
                    <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Processing Level</span>
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full ${getProcessingLevelColor(selectedFood['Processing Level'])} mr-2`} />
                          <span className="text-sm">{selectedFood['Processing Level']}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    <Info className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>Select a food item to see detailed information</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Healthy Recommendations */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
                  Healthy Picks
                </CardTitle>
                <CardDescription>
                  Nutritionally dense foods recommended by our AI
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {healthyFoods.map((food, index) => (
                    <div
                      key={index}
                      className="p-3 border rounded-lg hover:shadow-sm transition-shadow cursor-pointer"
                      onClick={() => setSelectedFood(food)}
                    >
                      <div className="font-medium text-sm">{food['Food Name']}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {food.Calories} cal • {food.Protein}g protein
                      </div>
                      <Badge className={`text-xs ${getNutritionalDensityColor(food['Nutritional Density'])}`} variant="outline">
                        {food['Nutritional Density']} Density
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
}