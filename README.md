# NutriScope - Advanced Food Analysis & Health Prediction Platform

A comprehensive Next.js application that integrates with a Python ML backend to provide AI-powered food analysis, health risk prediction, and personalized nutritional insights.

## 🚀 Features

### Frontend (Next.js)
- **Modern UI/UX**: Beautiful, responsive design with dark mode support
- **Health Analysis**: Comprehensive form for personal health assessment
- **Food Search**: Advanced food database search with filtering
- **Dashboard**: Interactive health metrics and progress tracking
- **Food Scanner**: AI-powered food label scanning (simulation)
- **Profile Management**: Complete user profile and preferences
- **Data Visualization**: Charts and progress indicators using Recharts

### Backend Integration
- **Disease Risk Prediction**: ML-powered health risk analysis
- **Food Database**: Nutritional information for thousands of foods
- **Real-time API**: RESTful endpoints for seamless data exchange

## 📁 Project Structure

```
project-root/
├── backend/                    # Your Python ML backend
│   ├── simple_api.py          # Main API server
│   ├── test.py               # ML testing & validation
│   ├── models/               # XGBoost models and encoders
│   ├── data/                 # Training and food databases
│   └── ...
├── (Next.js app files)       # Frontend application
├── app/                      # Next.js app directory
├── components/               # Reusable UI components
├── lib/                      # Utility functions
└── package.json              # Dependencies and scripts
```

## 🛠️ Setup & Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+ with pip
- Backend dependencies from your `requirements.txt`

### 1. Frontend Setup
```bash
# Install frontend dependencies
npm install

# Start development server
npm run dev
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start the API server
py simple_api_minimal.py
```

### 3. Run Both Simultaneously (Recommended)
```bash
# Run both frontend and backend together
npm run dev:full
```

This command uses `concurrently` to run both the Next.js dev server and Python API server at the same time.

## 🔧 Configuration

### API Endpoints
The frontend connects to these backend endpoints:
- `POST /food/predict-disease` - Health risk prediction
- `GET /food/search` - Food database search
- `POST /food/analyze` - Food analysis
- `GET /food/categories` - Food categories
- `GET /food/healthy` - Healthy food recommendations

### Environment Variables
Create a `.env.local` file in the frontend root:
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:5000
```

## 📊 Key Features Breakdown

### 1. Health Analysis Page
- Comprehensive health form with demographics, lifestyle, and nutrition inputs
- Real-time ML prediction using your XGBoost model
- Confidence scores and risk level categorization
- Personalized health recommendations

### 2. Food Search & Analysis
- Search through extensive food database
- Nutritional information visualization
- Processing level indicators
- Health score calculations

### 3. Interactive Dashboard
- Health metrics tracking
- Weekly progress charts
- Risk distribution visualization
- Recent analysis history

### 4. Food Label Scanner
- Image upload and processing simulation
- OCR-like nutritional extraction
- AI-powered health scoring
- Processing level analysis

### 5. Profile Management
- Personal information management
- Health preferences configuration
- Notification settings
- Data privacy controls

## 🎨 Design Features

- **Modern Gradient Design**: Beautiful gradients and color schemes
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Dark Mode Support**: Complete dark/light theme system
- **Smooth Animations**: Framer Motion animations throughout
- **Interactive Charts**: Recharts integration for data visualization
- **Micro-interactions**: Hover effects and transitions

## 🚀 Running in Production

### Development
```bash
# Run both services in development
npm run dev:full
```

### Production Build
```bash
# Build the frontend
npm run build

# Start production server
npm start

# Backend should be deployed separately
cd backend && py simple_api_minimal.py
```

## 🔌 Backend Integration

The app integrates seamlessly with your Python backend:

1. **Health Predictions**: Uses your `test.py` logic via the `/food/predict-disease` endpoint
2. **Food Database**: Accesses your `food_database_fixed.csv` data
3. **ML Models**: Utilizes your trained XGBoost models
4. **Real-time Analysis**: Provides instant health insights

## 📱 Mobile Responsiveness

The application is fully responsive with:
- Mobile-first design approach
- Touch-friendly interfaces
- Optimized layouts for all screen sizes
- Progressive Web App capabilities

## 🔒 Security & Privacy

- CORS configuration for API security
- Input validation and sanitization
- Privacy-focused data handling
- No sensitive data storage in frontend

## 🎯 User Experience

- Intuitive navigation with clear visual hierarchy
- Loading states and error handling
- Toast notifications for user feedback
- Accessibility considerations
- Performance optimizations

## 📈 Performance

- Next.js 13+ App Router for optimal performance
- Code splitting and lazy loading
- Optimized images and assets
- Efficient API calls and caching

This application demonstrates professional-grade development with modern technologies, providing users with a comprehensive health analysis platform powered by your sophisticated ML backend.
