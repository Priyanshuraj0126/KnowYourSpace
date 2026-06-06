"""
Supabase Configuration and Database Operations for KnowYourSpace
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

# Load environment variables
load_dotenv()

# Fixed UUID for the demo user (matches Supabase UUID schema)
DEMO_USER_ID = "00000000-0000-4000-a000-000000000001"

class SupabaseManager:
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not all([self.supabase_url, self.supabase_anon_key]):
            raise ValueError("Missing Supabase configuration. Please check your environment variables.")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_anon_key)
        
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile by ID"""
        try:
            response = self.client.table('user_profiles').select('*').eq('id', user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    def create_user_profile(self, user_id: str, username: str, email: str, location: str = None) -> bool:
        """Create a new user profile"""
        try:
            profile_data = {
                'id': user_id,
                'username': username,
                'email': email,
                'location': location or 'Unknown',
                'member_since': datetime.now().isoformat()
            }
            
            # Insert profile
            self.client.table('user_profiles').insert(profile_data).execute()
            
            # Create default preferences
            preferences_data = {
                'user_id': user_id,
                'theme': 'dark',
                'units': 'metric',
                'notifications': True,
                'language': 'en',
                'timezone': 'UTC'
            }
            self.client.table('user_preferences').insert(preferences_data).execute()
            
            # Create default stats
            stats_data = {
                'user_id': user_id,
                'space_objects_explored': 0,
                'events_tracked': 0,
                'ai_questions_asked': 0,
                'pages_visited': 0,
                'last_login': datetime.now().isoformat()
            }
            self.client.table('user_stats').insert(stats_data).execute()
            
            return True
        except Exception as e:
            print(f"Error creating user profile: {e}")
            return False
    
    def update_user_profile(self, user_id: str, updates: Dict) -> bool:
        """Update user profile"""
        try:
            if 'preferences' in updates and isinstance(updates['preferences'], dict):
                updates = {**updates, **updates.pop('preferences')}

            # Update profile
            if any(key in updates for key in ['username', 'email', 'location', 'bio']):
                profile_updates = {k: v for k, v in updates.items() if k in ['username', 'email', 'location', 'bio']}
                self.client.table('user_profiles').update(profile_updates).eq('id', user_id).execute()
            
            # Update preferences
            if any(key in updates for key in ['theme', 'units', 'notifications', 'language', 'timezone']):
                pref_updates = {k: v for k, v in updates.items() if k in ['theme', 'units', 'notifications', 'language', 'timezone']}
                self.client.table('user_preferences').update(pref_updates).eq('user_id', user_id).execute()
            
            return True
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Optional[Dict]:
        """Get user statistics"""
        try:
            response = self.client.table('user_stats').select('*').eq('user_id', user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return None
    
    def update_user_stats(self, user_id: str, updates: Dict) -> bool:
        """Update user statistics"""
        try:
            self.client.table('user_stats').update(updates).eq('user_id', user_id).execute()
            return True
        except Exception as e:
            print(f"Error updating user stats: {e}")
            return False
    
    def increment_stat(self, user_id: str, stat_name: str, increment: int = 1) -> bool:
        """Increment a specific statistic"""
        try:
            current_stats = self.get_user_stats(user_id)
            if current_stats:
                current_value = current_stats.get(stat_name, 0)
                new_value = current_value + increment
                self.update_user_stats(user_id, {stat_name: new_value})
                return True
            return False
        except Exception as e:
            print(f"Error incrementing stat {stat_name}: {e}")
            return False
    
    def get_user_favorites(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user favorites"""
        try:
            response = self.client.table('user_favorites').select('*').eq('user_id', user_id).order('added_at', desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            print(f"Error getting user favorites: {e}")
            return []
    
    def add_favorite(self, user_id: str, title: str, favorite_type: str, description: str = None, external_id: str = None, external_url: str = None, metadata: Dict = None) -> bool:
        """Add a new favorite"""
        try:
            favorite_data = {
                'user_id': user_id,
                'title': title,
                'type': favorite_type,
                'description': description,
                'external_id': external_id,
                'external_url': external_url,
                'metadata': metadata or {},
                'added_at': datetime.now().isoformat()
            }
            
            self.client.table('user_favorites').insert(favorite_data).execute()
            return True
        except Exception as e:
            print(f"Error adding favorite: {e}")
            return False
    
    def remove_favorite(self, user_id: str, favorite_id: str) -> bool:
        """Remove a favorite"""
        try:
            self.client.table('user_favorites').delete().eq('id', favorite_id).eq('user_id', user_id).execute()
            return True
        except Exception as e:
            print(f"Error removing favorite: {e}")
            return False
    
    def get_user_activities(self, user_id: str, limit: int = 50, activity_type: str = None) -> List[Dict]:
        """Get user activities"""
        try:
            query = self.client.table('user_activities').select('*').eq('user_id', user_id)
            
            if activity_type and activity_type != 'all':
                query = query.eq('type', activity_type)
            
            response = query.order('timestamp', desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            print(f"Error getting user activities: {e}")
            return []
    
    def log_activity(self, user_id: str, activity_type: str, details: Dict = None) -> bool:
        """Log a new user activity"""
        try:
            activity_data = {
                'user_id': user_id,
                'type': activity_type,
                'details': details or {},
                'timestamp': datetime.now().isoformat()
            }
            
            self.client.table('user_activities').insert(activity_data).execute()
            
            # Update relevant stats based on activity type
            if activity_type == 'page_visit':
                self.increment_stat(user_id, 'pages_visited')
            elif activity_type == 'ai_search':
                self.increment_stat(user_id, 'ai_questions_asked')
            elif activity_type == 'event_view':
                self.increment_stat(user_id, 'events_tracked')
            elif activity_type == 'object_explore':
                self.increment_stat(user_id, 'space_objects_explored')
            
            return True
        except Exception as e:
            print(f"Error logging activity: {e}")
            return False
    
    def get_user_search_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user search history"""
        try:
            response = self.client.table('user_search_history').select('*').eq('user_id', user_id).order('timestamp', desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            print(f"Error getting search history: {e}")
            return []
    
    def add_search_history(self, user_id: str, query: str, search_type: str = 'general') -> bool:
        """Add search to history"""
        try:
            search_data = {
                'user_id': user_id,
                'query': query,
                'search_type': search_type,
                'timestamp': datetime.now().isoformat()
            }
            
            self.client.table('user_search_history').insert(search_data).execute()
            return True
        except Exception as e:
            print(f"Error adding search history: {e}")
            return False
    
    def clear_search_history(self, user_id: str) -> bool:
        """Clear user search history"""
        try:
            self.client.table('user_search_history').delete().eq('user_id', user_id).execute()
            return True
        except Exception as e:
            print(f"Error clearing search history: {e}")
            return False
    
    def get_user_achievements(self, user_id: str) -> List[Dict]:
        """Get user achievements"""
        try:
            response = self.client.table('user_achievements').select('*').eq('user_id', user_id).execute()
            return response.data or []
        except Exception as e:
            print(f"Error getting user achievements: {e}")
            return []
    
    def check_and_award_achievements(self, user_id: str) -> List[Dict]:
        """Check if user qualifies for new achievements and award them"""
        try:
            # Get current user stats
            stats = self.get_user_stats(user_id)
            if not stats:
                return []
            
            # Get achievement definitions
            response = self.client.table('achievement_definitions').select('*').execute()
            achievement_defs = response.data or []
            
            # Get existing achievements
            existing_achievements = {ach['achievement_id'] for ach in self.get_user_achievements(user_id)}
            
            new_achievements = []
            
            for achievement in achievement_defs:
                achievement_id = achievement['id']
                
                # Skip if already awarded
                if achievement_id in existing_achievements:
                    continue
                
                # Check if requirements are met
                requirements = achievement['requirements']
                qualifies = True
                
                for req_key, req_value in requirements.items():
                    if stats.get(req_key, 0) < req_value:
                        qualifies = False
                        break
                
                if qualifies:
                    # Award achievement
                    achievement_data = {
                        'user_id': user_id,
                        'achievement_id': achievement_id,
                        'name': achievement['name'],
                        'description': achievement['description'],
                        'icon': achievement['icon'],
                        'unlocked_at': datetime.now().isoformat()
                    }
                    
                    self.client.table('user_achievements').insert(achievement_data).execute()
                    new_achievements.append(achievement_data)
            
            return new_achievements
        except Exception as e:
            print(f"Error checking achievements: {e}")
            return []
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict]:
        """Get user preferences"""
        try:
            response = self.client.table('user_preferences').select('*').eq('user_id', user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting user preferences: {e}")
            return None
    
    def update_user_preferences(self, user_id: str, updates: Dict) -> bool:
        """Update user preferences"""
        try:
            self.client.table('user_preferences').update(updates).eq('user_id', user_id).execute()
            return True
        except Exception as e:
            print(f"Error updating user preferences: {e}")
            return False
    
    def get_demo_user_data(self) -> Dict:
        """Get demo user data for development/testing"""
        demo_user_id = DEMO_USER_ID
        
        # Check if demo user exists, if not create it
        profile = self.get_user_profile(demo_user_id)
        if not profile:
            self.create_user_profile(
                demo_user_id, 
                "SpaceExplorer2025", 
                "demo@knowyourspace.com", 
                "New York, USA"
            )
        
        # Get all demo user data
        profile = self.get_user_profile(demo_user_id)
        stats = self.get_user_stats(demo_user_id)
        preferences = self.get_user_preferences(demo_user_id)
        favorites = self.get_user_favorites(demo_user_id)
        activities = self.get_user_activities(demo_user_id)
        achievements = self.get_user_achievements(demo_user_id)
        search_history = self.get_user_search_history(demo_user_id)
        
        return {
            'profile': profile,
            'stats': stats,
            'preferences': preferences,
            'favorites': favorites,
            'activities': activities,
            'achievements': achievements,
            'search_history': search_history
        }

# Global instance
supabase_manager = None

def get_supabase_manager() -> SupabaseManager:
    """Get or create Supabase manager instance"""
    global supabase_manager
    if supabase_manager is None:
        try:
            supabase_manager = SupabaseManager()
        except Exception as e:
            print(f"Failed to initialize Supabase: {e}")
            return None
    return supabase_manager

def is_supabase_available() -> bool:
    """Check if Supabase is available"""
    try:
        manager = get_supabase_manager()
        return manager is not None
    except:
        return False
