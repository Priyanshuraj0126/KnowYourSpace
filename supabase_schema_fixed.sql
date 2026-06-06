-- Supabase Database Schema for KnowYourSpace Profile System (Fixed Version)

-- Create custom types
CREATE TYPE activity_type AS ENUM (
    'page_visit',
    'ai_search', 
    'event_view',
    'object_explore',
    'favorite_added',
    'achievement_unlocked'
);

CREATE TYPE favorite_type AS ENUM (
    'space_object',
    'event',
    'discovery',
    'mission'
);

CREATE TYPE search_type AS ENUM (
    'general',
    'planets',
    'stars',
    'cosmology',
    'space-exploration',
    'astronomy'
);

CREATE TYPE theme_preference AS ENUM (
    'dark',
    'light',
    'auto'
);

CREATE TYPE unit_system AS ENUM (
    'metric',
    'imperial'
);

-- Users table (extends Supabase auth.users)
CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    location VARCHAR(120),
    member_since TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    avatar_url TEXT,
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User preferences table
CREATE TABLE public.user_preferences (
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE PRIMARY KEY,
    theme theme_preference DEFAULT 'dark',
    units unit_system DEFAULT 'metric',
    notifications BOOLEAN DEFAULT true,
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User statistics table
CREATE TABLE public.user_stats (
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE PRIMARY KEY,
    space_objects_explored INTEGER DEFAULT 0,
    events_tracked INTEGER DEFAULT 0,
    ai_questions_asked INTEGER DEFAULT 0,
    pages_visited INTEGER DEFAULT 0,
    last_login TIMESTAMP WITH TIME ZONE,
    total_favorites INTEGER DEFAULT 0,
    total_searches INTEGER DEFAULT 0,
    total_activities INTEGER DEFAULT 0,
    member_days INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User favorites table
CREATE TABLE public.user_favorites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(255) NOT NULL,
    type favorite_type NOT NULL,
    description TEXT,
    external_id VARCHAR(255),
    external_url TEXT,
    metadata JSONB,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User activity log table
CREATE TABLE public.user_activities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    type activity_type NOT NULL,
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User search history table
CREATE TABLE public.user_search_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    query TEXT NOT NULL,
    search_type search_type DEFAULT 'general',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User achievements table
CREATE TABLE public.user_achievements (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    achievement_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(100) NOT NULL,
    unlocked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

-- Achievement definitions table
CREATE TABLE public.achievement_definitions (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(100) NOT NULL,
    requirements JSONB NOT NULL,
    points INTEGER DEFAULT 0,
    category VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default achievement definitions
INSERT INTO public.achievement_definitions (id, name, description, icon, requirements, points, category) VALUES
('explorer_bronze', 'Bronze Explorer', 'Explored 10+ space objects', 'fas fa-rocket', '{"space_objects_explored": 10}', 10, 'exploration'),
('explorer_silver', 'Silver Explorer', 'Explored 50+ space objects', 'fas fa-rocket', '{"space_objects_explored": 50}', 25, 'exploration'),
('explorer_gold', 'Gold Explorer', 'Explored 100+ space objects', 'fas fa-rocket', '{"space_objects_explored": 100}', 50, 'exploration'),
('curious_mind', 'Curious Mind', 'Asked 25+ AI questions', 'fas fa-brain', '{"ai_questions_asked": 25}', 15, 'learning'),
('knowledge_seeker', 'Knowledge Seeker', 'Asked 100+ AI questions', 'fas fa-brain', '{"ai_questions_asked": 100}', 50, 'learning'),
('event_tracker', 'Event Tracker', 'Tracked 15+ astronomical events', 'fas fa-calendar-star', '{"events_tracked": 15}', 20, 'events'),
('event_master', 'Event Master', 'Tracked 50+ astronomical events', 'fas fa-calendar-star', '{"events_tracked": 50}', 75, 'events'),
('collector', 'Space Collector', 'Saved 20+ favorite items', 'fas fa-heart', '{"total_favorites": 20}', 25, 'collection'),
('super_collector', 'Super Collector', 'Saved 100+ favorite items', 'fas fa-heart', '{"total_favorites": 100}', 100, 'collection'),
('dedicated_learner', 'Dedicated Learner', 'Visited 100+ pages', 'fas fa-eye', '{"pages_visited": 100}', 30, 'engagement'),
('veteran_explorer', 'Veteran Explorer', 'Member for 365+ days', 'fas fa-trophy', '{"member_days": 365}', 100, 'loyalty');

-- Create indexes for better performance
CREATE INDEX idx_user_favorites_user_id ON public.user_favorites(user_id);
CREATE INDEX idx_user_favorites_type ON public.user_favorites(type);
CREATE INDEX idx_user_activities_user_id ON public.user_activities(user_id);
CREATE INDEX idx_user_activities_type ON public.user_activities(type);
CREATE INDEX idx_user_activities_timestamp ON public.user_activities(timestamp);
CREATE INDEX idx_user_search_history_user_id ON public.user_search_history(user_id);
CREATE INDEX idx_user_search_history_timestamp ON public.user_search_history(timestamp);
CREATE INDEX idx_user_achievements_user_id ON public.user_achievements(user_id);

-- Enable Row Level Security (RLS)
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_achievements ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_profiles
CREATE POLICY "Users can view their own profile" ON public.user_profiles
    FOR SELECT USING (true);

CREATE POLICY "Users can update their own profile" ON public.user_profiles
    FOR UPDATE USING (true);

CREATE POLICY "Users can insert their own profile" ON public.user_profiles
    FOR INSERT WITH CHECK (true);

-- RLS Policies for user_preferences
CREATE POLICY "Users can view their own preferences" ON public.user_preferences
    FOR SELECT USING (true);

CREATE POLICY "Users can update their own preferences" ON public.user_preferences
    FOR UPDATE USING (true);

CREATE POLICY "Users can insert their own preferences" ON public.user_preferences
    FOR INSERT WITH CHECK (true);

-- RLS Policies for user_stats
CREATE POLICY "Users can view their own stats" ON public.user_stats
    FOR SELECT USING (true);

CREATE POLICY "Users can update their own stats" ON public.user_stats
    FOR UPDATE USING (true);

CREATE POLICY "Users can insert their own stats" ON public.user_stats
    FOR INSERT WITH CHECK (true);

-- RLS Policies for user_favorites
CREATE POLICY "Users can view their own favorites" ON public.user_favorites
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own favorites" ON public.user_favorites
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update their own favorites" ON public.user_favorites
    FOR UPDATE USING (true);

CREATE POLICY "Users can delete their own favorites" ON public.user_favorites
    FOR DELETE USING (true);

-- RLS Policies for user_activities
CREATE POLICY "Users can view their own activities" ON public.user_activities
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own activities" ON public.user_activities
    FOR INSERT WITH CHECK (true);

-- RLS Policies for user_search_history
CREATE POLICY "Users can view their own search history" ON public.user_search_history
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own search history" ON public.user_search_history
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can delete their own search history" ON public.user_search_history
    FOR DELETE USING (true);

-- RLS Policies for user_achievements
CREATE POLICY "Users can view their own achievements" ON public.user_achievements
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own achievements" ON public.user_achievements
    FOR INSERT WITH CHECK (true);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_stats_updated_at BEFORE UPDATE ON public.user_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate member days
CREATE OR REPLACE FUNCTION calculate_member_days()
RETURNS TRIGGER AS $$
BEGIN
    NEW.member_days = EXTRACT(EPOCH FROM (NOW() - NEW.member_since)) / 86400;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for member_days calculation
CREATE TRIGGER calculate_member_days_trigger BEFORE INSERT OR UPDATE ON public.user_stats
    FOR EACH ROW EXECUTE FUNCTION calculate_member_days();

-- Function to update total counts
CREATE OR REPLACE FUNCTION update_total_counts()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- Update total_favorites
        UPDATE public.user_stats 
        SET total_favorites = (
            SELECT COUNT(*) FROM public.user_favorites WHERE user_id = NEW.user_id
        )
        WHERE user_id = NEW.user_id;
        
        -- Update total_activities
        UPDATE public.user_stats 
        SET total_activities = (
            SELECT COUNT(*) FROM public.user_activities WHERE user_id = NEW.user_id
        )
        WHERE user_id = NEW.user_id;
        
        -- Update total_searches
        UPDATE public.user_stats 
        SET total_searches = (
            SELECT COUNT(*) FROM public.user_search_history WHERE user_id = NEW.user_id
        )
        WHERE user_id = NEW.user_id;
    END IF;
    
    IF TG_OP = 'DELETE' THEN
        -- Update total_favorites
        UPDATE public.user_stats 
        SET total_favorites = (
            SELECT COUNT(*) FROM public.user_favorites WHERE user_id = OLD.user_id
        )
        WHERE user_id = OLD.user_id;
        
        -- Update total_activities
        UPDATE public.user_stats 
        SET total_activities = (
            SELECT COUNT(*) FROM public.user_activities WHERE user_id = OLD.user_id
        )
        WHERE user_id = OLD.user_id;
        
        -- Update total_searches
        UPDATE public.user_stats 
        SET total_searches = (
            SELECT COUNT(*) FROM public.user_search_history WHERE user_id = OLD.user_id
        )
        WHERE user_id = OLD.user_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

-- Create triggers for total counts
CREATE TRIGGER update_favorites_count AFTER INSERT OR UPDATE OR DELETE ON public.user_favorites
    FOR EACH ROW EXECUTE FUNCTION update_total_counts();

CREATE TRIGGER update_activities_count AFTER INSERT OR UPDATE OR DELETE ON public.user_activities
    FOR EACH ROW EXECUTE FUNCTION update_total_counts();

CREATE TRIGGER update_search_count AFTER INSERT OR UPDATE OR DELETE ON public.user_search_history
    FOR EACH ROW EXECUTE FUNCTION update_total_counts();
