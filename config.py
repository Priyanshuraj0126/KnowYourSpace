import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for KnowYourSpace application"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY') or os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    NASA_API_KEY = os.getenv('NASA_API_KEY', 'DEMO_KEY')
    MARS_VISTA_API_KEY = os.getenv('MARS_VISTA_API_KEY')
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    
    # API Endpoints
    NASA_BASE_URL = "https://api.nasa.gov"
    MARS_VISTA_BASE_URL = "https://api.marsvista.dev"
    OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1"
    NASA_APOD_TIMEOUT = 20
    
    # Application Settings
    ITEMS_PER_PAGE = 20
    MAX_FAVORITES_PER_USER = 100
    
    # Weather API Settings
    DEFAULT_LATITUDE = 40.7128  # New York
    DEFAULT_LONGITUDE = -74.0060
    
    # Astronomical Events
    EVENTS_LOOKUP_DAYS = 30  # How many days ahead to look for events
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        missing_configs = []
        
        if not cls.GEMINI_API_KEY:
            missing_configs.append("GEMINI_API_KEY")
        
        if not cls.SUPABASE_URL:
            missing_configs.append("SUPABASE_URL")
        
        if not cls.SUPABASE_ANON_KEY:
            missing_configs.append("SUPABASE_ANON_KEY")
        
        if missing_configs:
            print(f"Warning: Missing configuration for: {', '.join(missing_configs)}")
            print("Some features may not work properly.")
            return False
        
        return True
    
    @classmethod
    def get_nasa_api_url(cls, endpoint):
        """Generate NASA API URL with endpoint"""
        return f"{cls.NASA_BASE_URL}/{endpoint}"
    
    @classmethod
    def get_weather_api_url(cls, endpoint):
        """Generate Open Meteo API URL with endpoint"""
        return f"{cls.OPEN_METEO_BASE_URL}/{endpoint}"
    
    @classmethod
    def is_production(cls):
        """Check if running in production mode"""
        return cls.FLASK_ENV == 'production'
    
    @classmethod
    def is_development(cls):
        """Check if running in development mode"""
        return cls.FLASK_ENV == 'development'

# Create global config instance
config = Config()

# Validate configuration on import
if __name__ == '__main__':
    config.validate_config()
