"""
SkyNET-I2A2 - Integração com Supabase
Gerenciamento de memória persistente e operações de banco de dados
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import uuid
import hashlib

from supabase import create_client, Client
from ..config import settings


class SupabaseManager:
    """Gerenciador de operações Supabase"""

    def __init__(self):
        # Cliente para operações de leitura (usa anon key)
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )

        # Cliente para operações administrativas (usa service_role key)
        self.supabase_admin: Client = None

        # Inicializar cliente administrativo com verificações
        self._init_admin_client()

    def _init_admin_client(self):
        """Inicializa cliente administrativo com verificações robustas"""
        try:
            service_role_key = settings.supabase_service_role_key
            if not service_role_key:
                print("WARNING: SUPABASE_SERVICE_ROLE_KEY não configurada!")
                return

            if service_role_key == "your_service_role_key_here":
                print("WARNING: SUPABASE_SERVICE_ROLE_KEY ainda está com valor de exemplo!")
                return

            self.supabase_admin = create_client(
                settings.supabase_url,
                service_role_key
            )

            # Testar se a chave funciona
            test_result = self.supabase_admin.table('fiscal_documents').select('count', count='exact').limit(1).execute()
            print(f"Service role key test: OK (found {test_result.count if hasattr(test_result, 'count') else 'unknown'} records)")

        except Exception as e:
            print(f"ERROR: Falha ao inicializar cliente administrativo: {e}")
            self.supabase_admin = None
    
    # ==================== OPERAÇÕES DE USUÁRIO ====================
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria novo usuário"""
        try:
            result = self.supabase.table('users').insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Erro ao criar usuário: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca usuário por email"""
        try:
            result = self.supabase.table('users').select('*').eq('email', email).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Busca usuário por ID"""
        try:
            result = self.supabase.table('users').select('*').eq('id', str(user_id)).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    
    async def update_user(self, user_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza dados do usuário"""
        try:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            result = self.supabase.table('users').update(update_data).eq('id', str(user_id)).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Erro ao atualizar usuário: {str(e)}")
    
    # ==================== OPERAÇÕES DE SESSÃO ====================
    
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria nova sessão"""
        try:
            result = self.supabase.table('sessions').insert(session_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Erro ao criar sessão: {str(e)}")
    
    async def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Busca sessão por token"""
        try:
            result = self.supabase.table('sessions').select('*').eq('session_token', session_token).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    
    async def invalidate_session(self, session_id: UUID) -> bool:
        """Invalida sessão"""
        try:
            self.supabase.table('sessions').update({
                'is_active': False,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', str(session_id)).execute()
            return True
        except Exception:
            return False
    
    # ==================== OPERAÇÕES DE RESET DE SENHA ====================
    
    async def create_password_reset_token(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria token de reset de senha"""
        try:
            result = self.supabase.table('password_reset_tokens').insert(token_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Erro ao criar token de reset: {str(e)}")
    
    async def get_password_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Busca token de reset"""
        try:
            result = self.supabase.table('password_reset_tokens').select('*').eq('token', token).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    
    async def update_password_reset_token(self, token_id: UUID, update_data: Dict[str, Any]) -> bool:
        """Atualiza token de reset"""
        try:
            self.supabase.table('password_reset_tokens').update(update_data).eq('id', str(token_id)).execute()
            return True
        except Exception:
            return False
    
    # ==================== OPERAÇÕES DE DOCUMENTOS FISCAIS ====================
    
    async def create_fiscal_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria documento fiscal"""
        try:
            result = self.supabase_admin.table('fiscal_documents').insert(doc_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Erro ao criar documento: {str(e)}")
    
    async def get_fiscal_documents(self, user_id: UUID, limit: int = 50) -> List[Dict[str, Any]]:
        """Lista documentos fiscais do usuário"""
        try:
            result = self.supabase.table('fiscal_documents')\
                .select('*')\
                .eq('user_id', str(user_id))\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return result.data or []
        except Exception:
            return []
    
    async def get_fiscal_document(self, doc_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Busca documento específico"""
        try:
            result = self.supabase.table('fiscal_documents')\
                .select('*')\
                .eq('id', str(doc_id))\
                .eq('user_id', str(user_id))\
                .execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    
    async def update_fiscal_document(self, doc_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza documento fiscal"""
        try:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            result = self.supabase_admin.table('fiscal_documents').update(update_data).eq('id', str(doc_id)).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Erro ao atualizar documento: {str(e)}")
    
    async def get_documents_by_user(self, user_id: str, filters: Dict = None) -> List[Dict[str, Any]]:
        """Busca documentos do usuário com filtros (compatível com DataManager)"""
        try:
            query = self.supabase.table('fiscal_documents').select('*').eq('user_id', user_id)

            # Aplicar filtros se fornecidos
            if filters:
                if 'limit' in filters:
                    query = query.limit(filters['limit'])

                if 'doc_type' in filters:
                    query = query.eq('document_type', filters['doc_type'])

                if 'status' in filters:
                    query = query.eq('status', filters['status'])

                if 'date_from' in filters and 'date_to' in filters:
                    query = query.gte('created_at', filters['date_from']).lte('created_at', filters['date_to'])

                if 'min_value' in filters and 'max_value' in filters:
                    query = query.gte('document_value', filters['min_value']).lte('document_value', filters['max_value'])

            result = query.order('created_at', desc=True).execute()
            return result.data or []

        except Exception as e:
            print(f"Erro ao buscar documentos: {e}")
            return []

    async def save_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Salva documento processado no banco de dados"""
        try:
            # Adicionar campos obrigatórios se não existirem
            if 'id' not in document_data:
                document_data['id'] = str(uuid.uuid4())

            if 'created_at' not in document_data:
                document_data['created_at'] = datetime.utcnow().isoformat()

            if 'status' not in document_data:
                document_data['status'] = 'processed'

            if 'validation_status' not in document_data and 'status' in document_data:
                status_map = {
                    'processed': 'success',
                    'validated': 'success',
                    'pending': 'pending',
                    'error': 'error'
                }
                document_data['validation_status'] = status_map.get(document_data['status'], document_data['status'])

            print(f"Attempting to save document with ID: {document_data.get('id')}")

            # Tentar usar cliente administrativo primeiro
            if self.supabase_admin:
                print("Using admin client (service_role key)")
                result = self.supabase_admin.table('fiscal_documents').insert(document_data).execute()

                if result.data:
                    print(f"Document saved successfully with admin client: {result.data[0].get('id')}")
                    return result.data[0]
                else:
                    print("Admin client returned no data, trying fallback...")

            # Fallback: tentar com cliente regular
            print("Using regular client (anon key) as fallback")
            result = self.supabase.table('fiscal_documents').insert(document_data).execute()

            if result.data:
                print(f"Document saved successfully with regular client: {result.data[0].get('id')}")
                return result.data[0]
            else:
                print("Regular client also returned no data")
                return None

        except Exception as e:
            print(f"Erro ao salvar documento: {e}")
            print(f"Error details: {type(e).__name__}")
            return None

    async def get_analytics_data(self, user_id: str, date_range: tuple = None) -> List[Dict[str, Any]]:
        """Busca dados analíticos do usuário - Fallback para documentos fiscais"""
        try:
            # Primeiro tenta buscar da tabela analytics_data
            try:
                query = self.supabase.table('analytics_data').select('*').eq('user_id', user_id)

                if date_range:
                    query = query.gte('date', date_range[0].isoformat()).lte('date', date_range[1].isoformat())

                result = query.order('date', desc=True).execute()
                if result.data:
                    return result.data
            except Exception as e:
                print(f"Tabela analytics_data não encontrada, usando fallback: {e}")

            # Fallback: gerar dados analíticos a partir dos documentos fiscais
            documents = await self.get_fiscal_documents(user_id, limit=100)

            if not documents:
                return []

            # Converter para formato analítico
            analytics_data = []
            for doc in documents:
                # Usar data do documento como data da análise
                doc_date = doc.get('created_at', doc.get('document_date', datetime.utcnow().isoformat()))
                if isinstance(doc_date, str) and 'T' in doc_date:
                    doc_date = doc_date.split('T')[0]  # Extrair só a data

                # Categorizar por tipo de documento
                doc_type = doc.get('document_type', 'outros')
                category_mapping = {
                    'nfe': 'Serviços',
                    'nfce': 'Varejo',
                    'cte': 'Transporte',
                    'outros': 'Outros'
                }
                category = category_mapping.get(doc_type, 'Outros')

                # Adicionar dados analíticos
                analytics_data.append({
                    'date': doc_date,
                    'category': category,
                    'value': float(doc.get('document_value', 0)),
                    'quantity': 1,
                    'metadata': {
                        'document_type': doc_type,
                        'document_number': doc.get('document_number', ''),
                        'status': doc.get('status', 'unknown')
                    }
                })

            return analytics_data

        except Exception as e:
            print(f"Erro ao buscar dados analíticos: {e}")
            return []

    async def get_pending_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Busca documentos pendentes"""
        try:
            result = self.supabase.table('fiscal_documents')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('status', 'pending')\
                .order('created_at', desc=True)\
                .execute()
            return result.data or []
        except Exception:
            return []

    async def get_inconsistent_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Busca documentos com inconsistências"""
        try:
            result = self.supabase.table('fiscal_documents')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('status', 'error')\
                .order('created_at', desc=True)\
                .execute()
            return result.data or []
        except Exception:
            return []
    
    # ==================== OPERAÇÕES DE ANÁLISES ====================
    
    async def create_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria análise EDA"""
        try:
            result = self.supabase.table('analyses').insert(analysis_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Erro ao criar análise: {str(e)}")
    
    async def get_analyses(self, user_id: UUID, limit: int = 50) -> List[Dict[str, Any]]:
        """Lista análises do usuário"""
        try:
            result = self.supabase.table('analyses')\
                .select('*')\
                .eq('user_id', str(user_id))\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return result.data or []
        except Exception:
            return []
    
    async def get_analysis(self, analysis_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Busca análise específica"""
        try:
            result = self.supabase.table('analyses')\
                .select('*')\
                .eq('id', str(analysis_id))\
                .eq('user_id', str(user_id))\
                .execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    
    async def update_analysis(self, analysis_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza análise"""
        try:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            result = self.supabase.table('analyses').update(update_data).eq('id', str(analysis_id)).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Erro ao atualizar análise: {str(e)}")
    
    # ==================== OPERAÇÕES DE CONVERSAS/CHAT ====================
    
    async def create_conversation(self, conv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria entrada de conversa"""
        try:
            result = self.supabase.table('conversations').insert(conv_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Erro ao criar conversa: {str(e)}")
    
    async def get_conversations(self, user_id: UUID, session_id: Optional[UUID] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Lista conversas do usuário"""
        try:
            query = self.supabase.table('conversations').select('*').eq('user_id', str(user_id))
            
            if session_id:
                query = query.eq('session_id', str(session_id))
            
            result = query.order('created_at', desc=False).limit(limit).execute()
            return result.data or []
        except Exception:
            return []
    
    # ==================== CACHE DE TOKENS LLM ====================
    
    async def get_cached_token(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Busca token cached"""
        try:
            result = self.supabase.table('token_cache')\
                .select('*')\
                .eq('cache_key', cache_key)\
                .gt('expires_at', datetime.utcnow().isoformat())\
                .execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    
    async def cache_token(self, cache_data: Dict[str, Any]) -> Dict[str, Any]:
        """Armazena token no cache"""
        try:
            # Remove cache expirado primeiro
            await self.cleanup_expired_cache()
            
            result = self.supabase.table('token_cache').insert(cache_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Erro ao cachear token: {str(e)}")
    
    async def update_cache_hit(self, cache_id: UUID) -> bool:
        """Atualiza contador de hits do cache"""
        try:
            # Usa função SQL para incrementar atomicamente
            self.supabase.rpc('increment_cache_hit', {'cache_id': str(cache_id)}).execute()
            return True
        except Exception:
            return False
    
    async def cleanup_expired_cache(self) -> int:
        """Remove cache expirado"""
        try:
            result = self.supabase.table('token_cache')\
                .delete()\
                .lt('expires_at', datetime.utcnow().isoformat())\
                .execute()
            return len(result.data) if result.data else 0
        except Exception:
            return 0
    
    # ==================== LOG DE AUDITORIA ====================
    
    async def log_audit(self, user_id: UUID, action: str, resource_type: str, 
                       resource_id: str, details: Dict[str, Any], ip_address: str = None,
                       user_agent: str = None) -> Dict[str, Any]:
        """Registra log de auditoria"""
        try:
            audit_data = {
                'id': str(UUID()),
                'user_id': str(user_id),
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'details': details,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('audit_log').insert(audit_data).execute()
            return result.data[0] if result.data else None
        except Exception:
            # Log de auditoria não deve quebrar a aplicação
            return None
    
    async def get_audit_logs(self, user_id: UUID, limit: int = 100) -> List[Dict[str, Any]]:
        """Busca logs de auditoria do usuário"""
        try:
            result = self.supabase.table('audit_log')\
                .select('*')\
                .eq('user_id', str(user_id))\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return result.data or []
        except Exception:
            return []
    
    # ==================== EMAIL LOG ====================
    
    async def log_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Registra envio de email"""
        try:
            result = self.supabase.table('email_log').insert(email_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Erro ao registrar email: {str(e)}")
    
    async def update_email_status(self, email_id: UUID, status: str, details: Dict[str, Any] = None) -> bool:
        """Atualiza status do email"""
        try:
            update_data = {'status': status}
            if details:
                update_data.update(details)
            
            self.supabase.table('email_log').update(update_data).eq('id', str(email_id)).execute()
            return True
        except Exception:
            return False
    
    # ==================== ESTATÍSTICAS ====================
    
    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Obtém estatísticas do usuário"""
        try:
            # Usa view criada no SQL
            result = self.supabase.table('user_stats').select('*').eq('id', str(user_id)).execute()
            return result.data[0] if result.data else {
                'total_documents': 0,
                'total_analyses': 0,
                'total_conversations': 0,
                'total_document_value': 0.0
            }
        except Exception:
            return {
                'total_documents': 0,
                'total_analyses': 0,
                'total_conversations': 0,
                'total_document_value': 0.0
            }
    
    # ==================== UTILITÁRIOS ====================
    
    @staticmethod
    def generate_cache_key(prompt: str, user_id: UUID, model: str = "gemini-pro") -> str:
        """Gera chave de cache baseada no prompt e contexto"""
        content = f"{prompt}:{str(user_id)}:{model}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    def serialize_for_cache(data: Any) -> str:
        """Serializa dados para cache"""
        try:
            return json.dumps(data, default=str, ensure_ascii=False)
        except Exception:
            return "{}"
    
    @staticmethod
    def deserialize_from_cache(data: str) -> Any:
        """Deserializa dados do cache"""
        try:
            return json.loads(data)
        except Exception:
            return {}


class MemoryManager:
    """Gerenciador de memória para agentes"""
    
    def __init__(self, user_id: UUID, session_id: Optional[UUID] = None):
        self.user_id = user_id
        self.session_id = session_id
        self.supabase = SupabaseManager()
    
    async def store_conversation(self, user_message: str, agent_response: str, 
                                agent_name: str, reasoning: Dict[str, Any] = None,
                                analysis_id: UUID = None, document_id: UUID = None) -> Dict[str, Any]:
        """Armazena conversa na memória"""
        conv_data = {
            'id': str(UUID()),
            'user_id': str(self.user_id),
            'session_id': str(self.session_id) if self.session_id else None,
            'analysis_id': str(analysis_id) if analysis_id else None,
            'document_id': str(document_id) if document_id else None,
            'user_message': user_message,
            'agent_response': agent_response,
            'agent_name': agent_name,
            'reasoning': reasoning or {},
            'created_at': datetime.utcnow().isoformat()
        }
        
        return await self.supabase.create_conversation(conv_data)
    
    async def get_conversation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtém histórico de conversas"""
        return await self.supabase.get_conversations(
            self.user_id, 
            self.session_id, 
            limit
        )
    
    async def get_context_for_analysis(self, analysis_id: UUID) -> str:
        """Obtém contexto para análise específica"""
        analysis = await self.supabase.get_analysis(analysis_id, self.user_id)
        if not analysis:
            return ""
        
        context_parts = [
            f"Análise: {analysis.get('analysis_type', 'EDA')}",
            f"Arquivo: {analysis.get('csv_file_name', 'N/A')}",
            f"Status: {analysis.get('status', 'pending')}"
        ]
        
        if analysis.get('insights'):
            context_parts.append(f"Insights anteriores: {analysis['insights']}")
        
        return "\n".join(context_parts)
    
    async def get_context_for_document(self, document_id: UUID) -> str:
        """Obtém contexto para documento específico"""
        document = await self.supabase.get_fiscal_document(document_id, self.user_id)
        if not document:
            return ""
        
        context_parts = [
            f"Documento: {document.get('file_name', 'N/A')}",
            f"Tipo: {document.get('file_type', 'N/A')}",
            f"Valor: R$ {document.get('document_value', 0):,.2f}",
            f"Emissor: {document.get('issuer_name', 'N/A')}",
            f"Status: {document.get('validation_status', 'pending')}"
        ]
        
        if document.get('validation_notes'):
            context_parts.append(f"Observações: {document['validation_notes']}")
        
        return "\n".join(context_parts)