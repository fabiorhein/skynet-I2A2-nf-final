-- Script simplificado para resolver problemas de permissão

-- 1. Conceder permissões no esquema public
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;

-- 2. Desabilitar RLS completamente (solução temporária)
ALTER TABLE "public"."fiscal_documents" DISABLE ROW LEVEL SECURITY;

-- 3. Conceder permissões diretamente na tabela
GRANT ALL PRIVILEGES ON TABLE public.fiscal_documents TO anon;
GRANT ALL PRIVILEGES ON TABLE public.fiscal_documents TO authenticated;

-- 4. Verificar status atual
SELECT
    current_user,
    session_user,
    current_setting('request.jwt.claim.sub', true) as user_id;

-- 5. Testar inserção (descomente para testar)
-- INSERT INTO fiscal_documents (
--     file_name,
--     document_type,
--     validation_status,
--     status,
--     created_at,
--     updated_at
-- ) VALUES (
--     'teste.pdf',
--     'PDF',
--     'pending',
--     'pending',
--     NOW(),
--     NOW()
-- );
