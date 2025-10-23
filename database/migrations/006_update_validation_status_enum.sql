-- Migração 006: Atualiza o tipo validation_status_type para incluir valores faltantes

-- 1. Remover a view que depende da coluna
DROP VIEW IF EXISTS analytics_consolidated CASCADE;

-- 2. Remover o valor padrão atual da coluna
ALTER TABLE fiscal_documents 
    ALTER COLUMN validation_status DROP DEFAULT;

-- 3. Criar um novo tipo com os valores atualizados
CREATE TYPE validation_status_type_new AS ENUM (
    'success', 'warning', 'error', 'pending', 'processed', 'extracted'
);

-- 4. Converter os valores existentes para texto
ALTER TABLE fiscal_documents 
    ALTER COLUMN validation_status 
    DROP DEFAULT,
    ALTER COLUMN validation_status 
    TYPE TEXT USING validation_status::TEXT;

-- 5. Converter para o novo tipo com tratamento de valores
ALTER TABLE fiscal_documents 
    ALTER COLUMN validation_status 
    TYPE validation_status_type_new 
    USING (
        CASE validation_status
            WHEN 'success' THEN 'success'::validation_status_type_new
            WHEN 'warning' THEN 'warning'::validation_status_type_new
            WHEN 'error' THEN 'error'::validation_status_type_new
            WHEN 'pending' THEN 'pending'::validation_status_type_new
            WHEN 'processed' THEN 'processed'::validation_status_type_new
            WHEN 'extracted' THEN 'extracted'::validation_status_type_new
            ELSE 'pending'::validation_status_type_new  -- valor padrão para valores desconhecidos
        END
    );

-- 6. Remover o tipo antigo
DROP TYPE validation_status_type;

-- 7. Renomear o novo tipo para o nome original
ALTER TYPE validation_status_type_new RENAME TO validation_status_type;

-- 8. Adicionar valor padrão 'pending' à coluna
ALTER TABLE fiscal_documents 
    ALTER COLUMN validation_status 
    SET DEFAULT 'pending'::validation_status_type;

-- 9. Atualizar os valores existentes (opcional, se necessário)
-- UPDATE fiscal_documents 
-- SET validation_status = 'processed'::validation_status_type 
-- WHERE validation_status = 'success';

-- 10. Recriar a view (se necessário)
-- Exemplo genérico - ajuste conforme a definição original da sua view
CREATE OR REPLACE VIEW analytics_consolidated AS
SELECT 
    fd.*,
    -- Inclua aqui as outras colunas e lógicas da view original
    CASE 
        WHEN fd.validation_status = 'success' THEN 'Válido'
        WHEN fd.validation_status = 'processed' THEN 'Processado'
        WHEN fd.validation_status = 'extracted' THEN 'Extraído'
        WHEN fd.validation_status = 'warning' THEN 'Aviso'
        WHEN fd.validation_status = 'error' THEN 'Erro'
        ELSE 'Pendente'
    END as status_formatado
FROM fiscal_documents fd;

-- 11. Comentário para documentação
COMMENT ON TYPE validation_status_type IS 'Status de validação do documento (success, warning, error, pending, processed, extracted)';

-- 12. Atualizar a versão do banco de dados (se aplicável)
-- INSERT INTO schema_migrations (version, applied_at) VALUES ('006', NOW());
