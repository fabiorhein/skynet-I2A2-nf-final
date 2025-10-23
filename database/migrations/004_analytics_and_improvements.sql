-- SkyNET-I2A2 - Tabelas para Sistema de Dados Reais
-- Migração 004: Analytics e melhorias para dados dinâmicos

-- 1. Tabela para dados analíticos processados
-- (usada pelo DataManager para analytics em tempo real)
CREATE TABLE IF NOT EXISTS analytics_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    category VARCHAR(100) NOT NULL,
    value DECIMAL(15,2) NOT NULL,
    quantity INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Tabela para configurações de processamento de documentos
CREATE TABLE IF NOT EXISTS document_processing_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    config_name VARCHAR(100) NOT NULL,
    config_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_document_processing_config UNIQUE (config_name)
);

-- 3. Tabela para histórico de processamento de arquivos
CREATE TABLE IF NOT EXISTS file_processing_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size_bytes BIGINT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_time_ms INTEGER,
    error_message TEXT,
    extracted_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Melhorar tabela fiscal_documents com campos adicionais
ALTER TABLE fiscal_documents ADD COLUMN IF NOT EXISTS document_type VARCHAR(50);
ALTER TABLE fiscal_documents ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;
ALTER TABLE fiscal_documents ADD COLUMN IF NOT EXISTS ocr_confidence_score DECIMAL(5,2);

-- 5. Criar view para dados consolidados de analytics
CREATE OR REPLACE VIEW analytics_consolidated AS
SELECT
    fd.user_id,
    DATE(fd.created_at) as date,
    fd.document_type as category,
    fd.document_value as value,
    1 as quantity,
    json_build_object(
        'document_number', fd.document_number,
        'issuer_name', fd.issuer_name,
        'status', fd.validation_status,
        'classification', fd.classification
    ) as metadata
FROM fiscal_documents fd
WHERE fd.validation_status = 'success'
  AND fd.document_value > 0;

-- 6. Criar função para atualizar estatísticas em tempo real
CREATE OR REPLACE FUNCTION update_user_stats_on_document_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Verificar se a tabela user_analytics_stats existe
    IF NOT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'user_analytics_stats'
    ) THEN
        -- Se não existir, criar a tabela
        CREATE TABLE IF NOT EXISTS user_analytics_stats (
            id UUID PRIMARY KEY,
            email TEXT,
            company_name TEXT,
            industry TEXT,
            total_documents INTEGER DEFAULT 0,
            total_analyses INTEGER DEFAULT 0,
            total_conversations INTEGER DEFAULT 0,
            total_document_value DECIMAL(15,2) DEFAULT 0,
            created_at TIMESTAMP,
            last_login TIMESTAMP,
            UNIQUE(id)  -- Garante que a restrição única está explícita
        );
        
        -- Adicionar índice para melhorar consultas
        CREATE INDEX IF NOT EXISTS idx_user_analytics_stats_id ON user_analytics_stats(id);
    END IF;

    -- Atualizar estatísticas do usuário quando documento é inserido/atualizado
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- Primeiro, verificar se o usuário já existe
        IF EXISTS (SELECT 1 FROM user_analytics_stats WHERE id = NEW.user_id) THEN
            -- Atualizar registro existente
            UPDATE user_analytics_stats
            SET 
                email = u.email,
                company_name = u.company_name,
                industry = u.industry,
                total_documents = (SELECT COUNT(*) FROM fiscal_documents fd WHERE fd.user_id = u.id),
                total_analyses = (SELECT COUNT(*) FROM analyses a WHERE a.user_id = u.id),
                total_conversations = (SELECT COUNT(*) FROM conversations c WHERE c.user_id = u.id),
                total_document_value = COALESCE((SELECT SUM(fd2.document_value) FROM fiscal_documents fd2 WHERE fd2.user_id = u.id), 0),
                last_login = u.last_login
            FROM users u
            WHERE user_analytics_stats.id = u.id AND u.id = NEW.user_id;
        ELSE
            -- Inserir novo registro
            INSERT INTO user_analytics_stats (
                id, email, company_name, industry,
                total_documents, total_analyses, total_conversations, total_document_value,
                created_at, last_login
            )
            SELECT
                u.id, u.email, u.company_name, u.industry,
                (SELECT COUNT(*) FROM fiscal_documents fd WHERE fd.user_id = u.id) as total_docs,
                (SELECT COUNT(*) FROM analyses a WHERE a.user_id = u.id) as total_analyses,
                (SELECT COUNT(*) FROM conversations c WHERE c.user_id = u.id) as total_conversations,
                COALESCE((SELECT SUM(fd2.document_value) FROM fiscal_documents fd2 WHERE fd2.user_id = u.id), 0) as total_value,
                u.created_at, u.last_login
            FROM users u
            WHERE u.id = NEW.user_id;
        END IF;
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 7. Triggers para manter estatísticas atualizadas
DROP TRIGGER IF EXISTS update_user_stats_on_fiscal_document_change ON fiscal_documents;
CREATE TRIGGER update_user_stats_on_fiscal_document_change
    AFTER INSERT OR UPDATE OR DELETE ON fiscal_documents
    FOR EACH ROW EXECUTE FUNCTION update_user_stats_on_document_change();

-- 8. Função para popular analytics_data a partir de documentos existentes
CREATE OR REPLACE FUNCTION populate_analytics_data()
RETURNS void AS $$
BEGIN
    -- Limpar dados existentes
    DELETE FROM analytics_data;

    -- Inserir dados consolidados dos documentos
    INSERT INTO analytics_data (user_id, date, category, value, quantity, metadata)
    SELECT
        user_id,
        DATE(created_at) as date,
        COALESCE(document_type, 'outros') as category,
        COALESCE(document_value, 0) as value,
        1 as quantity,
        json_build_object(
            'document_number', document_number,
            'issuer_name', issuer_name,
            'status', validation_status
        ) as metadata
    FROM fiscal_documents
    WHERE validation_status = 'success'
      AND document_value > 0;
END;
$$ LANGUAGE plpgsql;

-- 9. Índices para performance da nova tabela
CREATE INDEX IF NOT EXISTS idx_analytics_data_user_date ON analytics_data(user_id, date);
CREATE INDEX IF NOT EXISTS idx_analytics_data_category ON analytics_data(category);
CREATE INDEX IF NOT EXISTS idx_analytics_data_user_category ON analytics_data(user_id, category);

-- 10. RLS Policies para as novas tabelas
ALTER TABLE analytics_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_processing_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_processing_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage own analytics" ON analytics_data;
CREATE POLICY "Users can manage own analytics" ON analytics_data FOR ALL USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can manage own processing config" ON document_processing_config;
CREATE POLICY "Users can manage own processing config" ON document_processing_config FOR ALL USING (auth.uid() = user_id OR user_id IS NULL);
DROP POLICY IF EXISTS "Users can view own processing history" ON file_processing_history;
CREATE POLICY "Users can view own processing history" ON file_processing_history FOR SELECT USING (auth.uid() = user_id);

-- 11. Popula dados iniciais de analytics
SELECT populate_analytics_data();

-- 12. Configuração padrão de processamento
INSERT INTO document_processing_config (config_name, config_data) VALUES
('default_processing', '{
    "ocr_enabled": true,
    "validation_enabled": true,
    "auto_categorization": true,
    "notification_enabled": true,
    "max_file_size_mb": 10,
    "supported_formats": ["xml", "pdf", "png", "jpg", "jpeg"],
    "ocr_language": "por",
    "validation_rules": {
        "require_cnpj": true,
        "require_value": true,
        "validate_cfop": false,
        "validate_ncm": false
    }
}') ON CONFLICT (config_name) DO UPDATE SET config_data = EXCLUDED.config_data;

-- 13. Logs de auditoria para as novas operações
-- (já existe na migração 003, mas garantindo cobertura)

-- 14. Função para limpeza automática de dados antigos
CREATE OR REPLACE FUNCTION cleanup_old_analytics_data()
RETURNS void AS $$
BEGIN
    -- Remove dados analíticos com mais de 1 ano
    DELETE FROM analytics_data WHERE created_at < NOW() - INTERVAL '1 year';

    -- Remove histórico de processamento com mais de 6 meses
    DELETE FROM file_processing_history WHERE created_at < NOW() - INTERVAL '6 months';

    -- Remove configurações inativas com mais de 3 meses
    DELETE FROM document_processing_config
    WHERE is_active = false AND updated_at < NOW() - INTERVAL '3 months';
END;
$$ LANGUAGE plpgsql;

-- 15. Trigger para limpeza automática (opcional, pode ser chamado manualmente)
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * 0', 'SELECT cleanup_old_analytics_data();');  -- Domingos 2h

COMMENT ON TABLE analytics_data IS 'Dados analíticos processados para dashboards dinâmicos';
COMMENT ON TABLE document_processing_config IS 'Configurações de processamento por usuário';
COMMENT ON TABLE file_processing_history IS 'Histórico detalhado de processamento de arquivos';
