-- Script ultra-simples para resolver problemas de permissão
-- Execute este script no SQL Editor do Supabase

-- Desabilitar RLS completamente na tabela fiscal_documents
ALTER TABLE public.fiscal_documents DISABLE ROW LEVEL SECURITY;

-- Verificar se foi desabilitado
SELECT
    tablename,
    rowsecurity
FROM pg_tables
WHERE tablename = 'fiscal_documents';
