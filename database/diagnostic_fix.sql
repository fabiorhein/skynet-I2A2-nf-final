-- Script de diagnóstico e correção completo
-- Execute este script no SQL Editor do Supabase

-- 1. Verificar usuário atual e suas permissões
SELECT
    current_user,
    session_user,
    current_setting('request.jwt.claim.sub', true) as user_id,
    current_setting('request.jwt.claims', true) as jwt_claims;

-- 2. Verificar permissões no esquema public
SELECT
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public'
AND grantee IN ('anon', 'authenticated', 'service_role', 'postgres')
ORDER BY grantee, table_name, privilege_type;

-- 3. Verificar configurações do RLS na tabela fiscal_documents
SELECT
    t.schemaname,
    t.tablename,
    t.rowsecurity,
    t.rowsecurityforce,
    array_agg(p.polname) as policies
FROM pg_tables t
LEFT JOIN pg_policies p ON p.tablename = t.tablename
WHERE t.tablename = 'fiscal_documents'
GROUP BY 1, 2, 3, 4;

-- 4. Listar todas as políticas RLS
SELECT * FROM pg_policies WHERE tablename = 'fiscal_documents';

-- 5. DESABILITAR RLS completamente (solução temporária)
ALTER TABLE public.fiscal_documents DISABLE ROW LEVEL SECURITY;

-- 6. Conceder permissões TOTAL para todos os usuários
GRANT ALL PRIVILEGES ON TABLE public.fiscal_documents TO anon;
GRANT ALL PRIVILEGES ON TABLE public.fiscal_documents TO authenticated;
GRANT ALL PRIVILEGES ON TABLE public.fiscal_documents TO service_role;

-- 7. Conceder USAGE no esquema public
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

-- 8. Verificar se funcionou
SELECT
    t.schemaname,
    t.tablename,
    t.rowsecurity
FROM pg_tables t
WHERE t.tablename = 'fiscal_documents';

-- 9. Testar uma inserção simples (descomente para testar)
-- INSERT INTO fiscal_documents (
--     id,
--     user_id,
--     file_name,
--     document_type,
--     validation_status,
--     status,
--     created_at,
--     updated_at
-- ) VALUES (
--     gen_random_uuid(),
--     gen_random_uuid(),
--     'teste_diagnostico.pdf',
--     'PDF',
--     'pending',
--     'pending',
--     NOW(),
--     NOW()
-- );
