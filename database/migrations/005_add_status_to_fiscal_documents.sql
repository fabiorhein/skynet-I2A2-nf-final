-- Migração 005: Adiciona coluna status à tabela fiscal_documents

-- Adiciona a coluna status se não existir
ALTER TABLE fiscal_documents 
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending';

-- Atualiza registros existentes para terem um valor padrão
UPDATE fiscal_documents 
SET status = 'processed' 
WHERE status IS NULL;

-- Comentário para documentação
COMMENT ON COLUMN fiscal_documents.status IS 'Status do documento (pending, processed, error, validated)';

-- Atualiza a versão do banco de dados (se você tiver uma tabela de versão)
-- INSERT INTO schema_migrations (version, applied_at) VALUES ('005', NOW());
