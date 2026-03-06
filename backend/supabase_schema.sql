-- ============================================
-- Supabase Schema for Multi-Agent Research Assistant
-- ============================================
-- 
-- HOW TO USE:
-- 1. Go to your Supabase dashboard (https://supabase.com)
-- 2. Open the SQL Editor (left sidebar → SQL Editor)
-- 3. Paste this entire file and click "Run"
--
-- WHY THIS TABLE STRUCTURE:
-- We store the ENTIRE research pipeline in one row:
-- - query: what the user asked
-- - sub_tasks: Planner Agent output (JSONB for flexibility)
-- - sources: Search Agent output (JSONB array of source objects)
-- - analysis: Analyzer Agent output (plain text)
-- - report: Writer Agent output (Markdown text)
-- - status: tracks pipeline progress (pending → in_progress → completed → failed)
--
-- WHY JSONB for sub_tasks and sources:
-- These fields contain structured data with variable shape.
-- JSONB lets us store complex nested objects without rigid schema,
-- and PostgreSQL can still query into them if needed.

CREATE TABLE IF NOT EXISTS research_tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Link the task to the authenticated user
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- The user's original research question
    query TEXT NOT NULL,
    
    -- Pipeline status: pending, in_progress, completed, failed
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    
    -- Planner Agent output: list of sub-tasks (JSONB for flexibility)
    sub_tasks JSONB,
    
    -- Search Agent output: list of sources with URLs and content
    sources JSONB,
    
    -- Analyzer Agent output: structured analysis text
    analysis TEXT,
    
    -- Writer Agent output: final Markdown research report
    report TEXT,
    
    -- Timestamps for tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- WHY this index:
-- The history sidebar queries by created_at DESC frequently.
-- An index makes this query fast even with many records.
CREATE INDEX IF NOT EXISTS idx_research_tasks_created_at 
    ON research_tasks (created_at DESC);

-- WHY this index:
-- The frontend filters by status (e.g., show only "completed" tasks).
CREATE INDEX IF NOT EXISTS idx_research_tasks_status 
    ON research_tasks (status);

-- Enable Row Level Security (Supabase best practice)
ALTER TABLE research_tasks ENABLE ROW LEVEL SECURITY;

-- Secure policies for authenticated users
CREATE POLICY "Users can view their own research" ON research_tasks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own research" ON research_tasks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own research" ON research_tasks
    FOR UPDATE USING (auth.uid() = user_id);

