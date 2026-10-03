-- ====================================================================
-- Blood Report Analyzer - Supabase Database Schema & RLS Initialization
-- ====================================================================

-- 1. Enable required extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Create users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create chat_sessions table
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create chat_messages table
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    content TEXT,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. Add indexes to optimize queries
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON public.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON public.chat_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON public.chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON public.chat_messages(created_at ASC);

-- 6. Insert Default Guest User (satisfies foreign key constraints for guest / unauthenticated sessions)
INSERT INTO public.users (id, email, name)
VALUES ('00000000-0000-0000-0000-000000000001', 'guest@bloodanalysis.local', 'Guest User')
ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email;

-- 7. Grant Permissions to Supabase API roles (anon, authenticated, service_role)
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.users TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.chat_sessions TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.chat_messages TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;

-- 8. Auto-Confirm Users in GoTrue (fixes "Email not confirmed" on self-hosted Supabase)
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'auth' AND tablename = 'users') THEN
        UPDATE auth.users 
        SET email_confirmed_at = COALESCE(email_confirmed_at, NOW())
        WHERE email_confirmed_at IS NULL;
    END IF;
END $$;

-- Trigger to auto-confirm any new auth.users signup
CREATE OR REPLACE FUNCTION public.handle_auto_confirm_user()
RETURNS TRIGGER AS $$
BEGIN
    NEW.email_confirmed_at = COALESCE(NEW.email_confirmed_at, NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'auth' AND tablename = 'users') THEN
        DROP TRIGGER IF EXISTS tr_auto_confirm_user ON auth.users;
        CREATE TRIGGER tr_auto_confirm_user
            BEFORE INSERT ON auth.users
            FOR EACH ROW
            EXECUTE FUNCTION public.handle_auto_confirm_user();
    END IF;
END $$;

-- ====================================================================
-- 9. Row Level Security (RLS) Configuration
-- ====================================================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Clean existing policies if any
DROP POLICY IF EXISTS "Allow select users" ON public.users;
DROP POLICY IF EXISTS "Allow insert users" ON public.users;
DROP POLICY IF EXISTS "Allow update users" ON public.users;

DROP POLICY IF EXISTS "Allow select chat_sessions" ON public.chat_sessions;
DROP POLICY IF EXISTS "Allow insert chat_sessions" ON public.chat_sessions;
DROP POLICY IF EXISTS "Allow update chat_sessions" ON public.chat_sessions;
DROP POLICY IF EXISTS "Allow delete chat_sessions" ON public.chat_sessions;

DROP POLICY IF EXISTS "Allow select chat_messages" ON public.chat_messages;
DROP POLICY IF EXISTS "Allow insert chat_messages" ON public.chat_messages;
DROP POLICY IF EXISTS "Allow delete chat_messages" ON public.chat_messages;

-- --- Policies for public.users ---
CREATE POLICY "Allow select users" ON public.users
    FOR SELECT TO anon, authenticated, service_role
    USING (true);

CREATE POLICY "Allow insert users" ON public.users
    FOR INSERT TO anon, authenticated, service_role
    WITH CHECK (true);

CREATE POLICY "Allow update users" ON public.users
    FOR UPDATE TO anon, authenticated, service_role
    USING (auth.uid() = id OR auth.uid() IS NULL);

-- --- Policies for public.chat_sessions ---
CREATE POLICY "Allow select chat_sessions" ON public.chat_sessions
    FOR SELECT TO anon, authenticated, service_role
    USING (
        auth.uid() = user_id 
        OR user_id = '00000000-0000-0000-0000-000000000001'
        OR auth.uid() IS NULL
    );

CREATE POLICY "Allow insert chat_sessions" ON public.chat_sessions
    FOR INSERT TO anon, authenticated, service_role
    WITH CHECK (
        auth.uid() = user_id 
        OR user_id = '00000000-0000-0000-0000-000000000001'
        OR auth.uid() IS NULL
    );

CREATE POLICY "Allow update chat_sessions" ON public.chat_sessions
    FOR UPDATE TO anon, authenticated, service_role
    USING (
        auth.uid() = user_id 
        OR user_id = '00000000-0000-0000-0000-000000000001'
        OR auth.uid() IS NULL
    );

CREATE POLICY "Allow delete chat_sessions" ON public.chat_sessions
    FOR DELETE TO anon, authenticated, service_role
    USING (
        auth.uid() = user_id 
        OR user_id = '00000000-0000-0000-0000-000000000001'
        OR auth.uid() IS NULL
    );

-- --- Policies for public.chat_messages ---
CREATE POLICY "Allow select chat_messages" ON public.chat_messages
    FOR SELECT TO anon, authenticated, service_role
    USING (
        auth.uid() IS NULL
        OR EXISTS (
            SELECT 1 FROM public.chat_sessions s
            WHERE s.id = chat_messages.session_id
            AND (s.user_id = auth.uid() OR s.user_id = '00000000-0000-0000-0000-000000000001')
        )
    );

CREATE POLICY "Allow insert chat_messages" ON public.chat_messages
    FOR INSERT TO anon, authenticated, service_role
    WITH CHECK (
        auth.uid() IS NULL
        OR EXISTS (
            SELECT 1 FROM public.chat_sessions s
            WHERE s.id = chat_messages.session_id
            AND (s.user_id = auth.uid() OR s.user_id = '00000000-0000-0000-0000-000000000001')
        )
    );

CREATE POLICY "Allow delete chat_messages" ON public.chat_messages
    FOR DELETE TO anon, authenticated, service_role
    USING (
        auth.uid() IS NULL
        OR EXISTS (
            SELECT 1 FROM public.chat_sessions s
            WHERE s.id = chat_messages.session_id
            AND (s.user_id = auth.uid() OR s.user_id = '00000000-0000-0000-0000-000000000001')
        )
    );

-- 10. Refresh PostgREST schema cache immediately
NOTIFY pgrst, 'reload schema';