-- Script completo para resolver problemas de permissão no Supabase

-- 1. Conceder permissões no esquema public
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;

-- 2. Conceder permissões para futuras tabelas
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO anon, authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO anon, authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON FUNCTIONS TO anon, authenticated;

-- 3. Verificar e corrigir as políticas RLS da tabela fiscal_documents
-- Primeiro, remover TODAS as políticas existentes (sem IF EXISTS para forçar)
DO $$
DECLARE
    pol record;
BEGIN
    FOR pol IN (
        SELECT policyname
        FROM pg_policies
        WHERE tablename = 'fiscal_documents'
    ) LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.fiscal_documents', pol.policyname);
    END LOOP;
END $$;

-- 4. Desabilitar temporariamente o RLS para permitir inserções
ALTER TABLE "public"."fiscal_documents" DISABLE ROW LEVEL SECURITY;

-- 5. Política de leitura para todos (incluindo anon)
CREATE POLICY "Permitir leitura de documentos"
ON "public"."fiscal_documents"
FOR SELECT
USING (true);

-- 6. Política de inserção para todos (incluindo anon)
CREATE POLICY "Permitir inserção de documentos"
ON "public"."fiscal_documents"
FOR INSERT
WITH CHECK (true);

-- 7. Política de update para todos (incluindo anon)
CREATE POLICY "Permitir atualização de documentos"
ON "public"."fiscal_documents"
FOR UPDATE
USING (true)
WITH CHECK (true);

-- 8. Política de delete para todos (incluindo anon)
CREATE POLICY "Permitir exclusão de documentos"
ON "public"."fiscal_documents"
FOR DELETE
USING (true);

-- 9. Reativar o RLS (agora com políticas permissivas)
ALTER TABLE "public"."fiscal_documents" ENABLE ROW LEVEL SECURITY;

-- 10. Verificar permissões aplicadas
SELECT
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public'
AND grantee IN ('anon', 'authenticated')
ORDER BY grantee, table_name, privilege_type;

-- 11. Verificar configurações do RLS
SELECT
    n.nspname as schema,
    c.relname as table,
    c.relrowsecurity as has_row_security,
    c.relforcerowsecurity as force_row_security,
    array_agg(p.polname) as policies
FROM pg_class c
LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_policy p ON p.polrelid = c.oid
WHERE c.relname = 'fiscal_documents'
GROUP BY 1, 2, 3, 4;

-- 12. Testar uma inserção simples (substitua pelos valores corretos da sua tabela)
-- INSERT INTO fiscal_documents (
--     id,
--     user_id,
--     file_name,
--     file_path,
--     document_type,
--     validation_status,
--     status,
--     created_at,
--     updated_at
-- ) VALUES (
--     gen_random_uuid(),
--     gen_random_uuid(),
--     'teste.pdf',
--     'uploads/teste.pdf',
--     'PDF'::document_type,
--     'pending'::validation_status_type,
--     'pending'::process_status_type,
--     NOW(),
--     NOW()
-- );

-- 13. Verificar o usuário atual
SELECT
    current_user,
    session_user,
    current_setting('request.jwt.claim.sub', true) as user_id,
    current_setting('request.jwt.claims', true) as jwt_claims;
