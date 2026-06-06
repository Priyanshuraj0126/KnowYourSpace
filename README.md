# KnowYourSpace 🌌 - Space Exploration & Learning Platform

A stunning, modern space exploration and learning platform featuring a cosmic design with real-time astronomical data, interactive celestial maps, and comprehensive information about planets, stars, and galaxies.

## ✨ Features

### 🎨 **Cosmic Design & UI/UX**
- **Dark Space Theme**: Beautiful nebula-like background with animated stars
- **Gradient Text Effects**: "KnowYour" in purple-to-pink, "Space" in yellow-to-orange
- **Glassmorphism Cards**: Modern, semi-transparent card design with subtle borders
- **Responsive Layout**: Optimized for all devices with smooth animations
- **Interactive Elements**: Hover effects, smooth transitions, and micro-interactions

### 🚀 **Core Functionality**
- **Real-time Space Data**: Integration with NASA APIs for live astronomical information
- **Celestial Object Explorer**: Detailed information about planets, stars, galaxies, and nebulae
- **Live Sky Events**: Track upcoming astronomical events and ISS flyovers
- **AI-Powered Q&A**: Ask questions about space using Gemini Pro AI
- **Weather & Visibility**: Check stargazing conditions with Open Meteo API

### 🌟 **Navigation & Structure**
- **Modern Navigation**: Clean navigation with telescope icon and "KnowSpace" branding
- **Search Functionality**: Search bar for finding celestial objects and information
- **Quick Access Links**: Easy navigation to planets, stars, and live events
- **Consistent Design**: Unified design language across all pages

## 🛠️ Technology Stack

### **Frontend**
- **HTML5**: Semantic markup with modern structure
- **CSS3**: Advanced styling with CSS variables, gradients, and animations
- **JavaScript**: Interactive functionality and dynamic content loading
- **Font Awesome**: Comprehensive icon library for space-themed elements
- **Google Fonts**: Orbitron (display) and Roboto (body) typography

### **Backend**
- **Python Flask**: Lightweight web framework for API endpoints
- **NASA Open APIs**: Astronomy Picture of the Day, Near Earth Objects, Mars Rover Photos
- **Open Meteo API**: Weather and visibility data for stargazing
- **Google Gemini Pro**: AI-powered space Q&A system
- **Supabase**: User authentication and data storage (configured but temporarily disabled)

### **Design System**
- **Color Palette**: Dark cosmic theme with purple, blue, and orange accents
- **Typography**: Futuristic Orbitron for headings, clean Roboto for body text
- **Animations**: Smooth transitions, hover effects, and background animations
- **Layout**: Card-based grid system with glassmorphism effects

## 🚀 Getting Started

### **Prerequisites**
- Python 3.8+
- pip package manager
- Modern web browser

### **Installation**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd KnowyourSpace
   ```

2. **Set up environment variables**
   ```bash
   # Copy the example environment file
   copy env.example .env
   
   # Edit .env with your API keys
   NASA_API_KEY=your_nasa_api_key
   GEMINI_API_KEY=your_gemini_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_supabase_key
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and navigate to `http://localhost:5000`
   - Experience the cosmic design and explore space!

### **Windows Quick Start**
```bash
# Run the start.bat file for automatic setup
start.bat
```

## 🌌 **Design Philosophy**

The new design embodies the wonder and mystery of space exploration:

- **Cosmic Aesthetics**: Dark backgrounds with nebula-like effects and animated stars
- **Modern UI/UX**: Clean, intuitive interface with smooth animations
- **Space-Themed Elements**: Telescope icons, gradient text effects, and celestial imagery
- **Responsive Design**: Optimized for all screen sizes and devices
- **Interactive Experience**: Engaging hover effects and smooth transitions

## 📱 **Pages & Features**

### **Main Dashboard** (`/`)
- Hero section with gradient "KnowYourSpace" title
- Search functionality for celestial objects
- Featured celestial bodies cards (Mars, Andromeda Galaxy, Jupiter)
- Quick access links to planets, stars, and live events

### **Explore Page** (`/explore`)
- Celestial object exploration with detailed cards
- Information about planets, stars, galaxies, and nebulae
- Interactive elements and smooth animations

### **Events Page** (`/events`)
- Live sky events tracking
- ISS flyovers, planetary events, and meteor showers
- Real-time astronomical event information

### **AI Chat** (`/ai-chat`)
- AI-powered space Q&A using Gemini Pro
- Expert astronomical knowledge and explanations
- Interactive chat interface

## 🔧 **API Integration**

### **NASA APIs**
- **APOD**: Astronomy Picture of the Day
- **NeoWs**: Near Earth Objects data
- **Mars Rover Photos**: Images from Mars exploration

### **Weather & Visibility**
- **Open Meteo**: Real-time weather data and visibility conditions
- **Location-based**: Default coordinates with customizable location support

### **AI Assistant**
- **Gemini Pro**: Advanced AI model for space-related questions
- **Context-aware**: Space-focused responses with educational content

## 🎨 **Customization**

### **CSS Variables**
The design system uses CSS variables for easy customization:
```css
:root {
    --primary-color: #6366f1;
    --secondary-color: #8b5cf6;
    --accent-color: #f59e0b;
    --gradient-primary: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    --gradient-text: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);
}
```

### **Adding New Pages**
1. Create HTML template in `templates/` directory
2. Add route in `app.py`
3. Include the main CSS and enhancement files
4. Follow the established design patterns

## 🚀 **Future Enhancements**

- **3D Visualizations**: Interactive 3D models of celestial objects
- **Real-time Tracking**: Live tracking of satellites and space missions
- **Community Features**: User-generated content and sharing
- **Mobile App**: Native mobile application development
- **Advanced Analytics**: Detailed astronomical data analysis

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 **Contributing**

Contributions are welcome! Please feel free to submit a Pull Request.

## 🌟 **Acknowledgments**

- **NASA**: For providing comprehensive space data APIs
- **Google**: For Gemini Pro AI capabilities
- **Open Meteo**: For weather and visibility data
- **Font Awesome**: For the comprehensive icon library
- **Space Enthusiasts**: For inspiration and feedback

---

**Built with ❤️ for space exploration and cosmic discovery** 🚀✨
