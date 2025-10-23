-- Solução radical SIMPLIFICADA para resolver problemas de permissão
-- Execute este script no SQL Editor do Supabase

-- 1. Conceder USAGE no esquema public para todos os usuários
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

-- 2. Conceder permissões TOTAL na tabela fiscal_documents
GRANT ALL PRIVILEGES ON TABLE public.fiscal_documents TO anon;
GRANT ALL PRIVILEGES ON TABLE public.fiscal_documents TO authenticated;
GRANT ALL PRIVILEGES ON TABLE public.fiscal_documents TO service_role;

-- 3. Conceder permissões em TODAS as tabelas do esquema public
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;

-- 4. Conceder permissões em TODAS as sequences do esquema public
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;

-- 5. Conceder permissões em TODAS as funções do esquema public
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated, service_role;

-- 6. Configurar permissões padrão para futuras tabelas
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO anon, authenticated, service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON FUNCTIONS TO anon, authenticated, service_role;

-- 7. DESABILITAR completamente o RLS na tabela fiscal_documents
ALTER TABLE public.fiscal_documents DISABLE ROW LEVEL SECURITY;

-- 8. Verificar permissões aplicadas (versão simplificada)
SELECT
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public'
AND grantee IN ('anon', 'authenticated', 'service_role')
ORDER BY grantee, table_name, privilege_type;

-- 9. Verificar usuário atual
SELECT
    current_user,
    session_user,
    current_setting('request.jwt.claim.sub', true) as user_id,
    current_setting('request.jwt.claims', true) as jwt_claims;
