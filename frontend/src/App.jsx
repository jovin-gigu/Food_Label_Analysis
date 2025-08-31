import FoodScanner from "./FoodScanner";

function App() {

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">
            🍎 Food Health Scanner
          </h1>
          
          <FoodScanner />
        </div>
      </div>
    </div>
  );
}

export default App;
