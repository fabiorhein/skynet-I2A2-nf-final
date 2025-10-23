"""
Data Manager Module
Gerencia dados reais de documentos fiscais e análises
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import asyncio
from pathlib import Path
import tempfile
import os
import uuid

from backend.core.memory import SupabaseManager
from backend.core.xml_parser import XMLParser
from backend.core.ocr_processor import OCRProcessor


class DataManager:
    """Gerencia dados reais de documentos e análises"""

    def __init__(self):
        self.supabase = SupabaseManager()
        self.xml_parser = XMLParser()
        self.ocr_processor = OCRProcessor()

    async def get_real_documents(self, user_id: str, filters: Dict = None) -> pd.DataFrame:
        """
        Busca documentos reais do banco de dados

        Args:
            user_id: ID do usuário
            filters: Filtros aplicados (tipo, data, status, valor)

        Returns:
            DataFrame com documentos reais
        """
        try:
            # Buscar documentos do usuário no Supabase
            documents = await self.supabase.get_documents_by_user(user_id, filters)

            if not documents:
                return pd.DataFrame()

            # Converter para DataFrame
            df = pd.DataFrame(documents)

            # Processar dados
            if 'created_at' in df.columns:
                df['Data'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m/%Y')
            if 'total_value' in df.columns:
                df['Valor (R$)'] = df['total_value'].astype(float)
            if 'document_type' in df.columns:
                df['Tipo'] = df['document_type']
            if 'validation_status' in df.columns:
                df['Status'] = df['validation_status'].apply(self._format_status)
            elif 'status' in df.columns:
                df['Status'] = df['status'].apply(self._format_status)
            if 'supplier_name' in df.columns:
                df['Fornecedor'] = df['supplier_name']

            # Selecionar colunas relevantes
            columns = ['Número', 'Tipo', 'Data', 'Fornecedor', 'Valor (R$)', 'Status']
            df = df[[col for col in columns if col in df.columns]]

            return df

        except Exception as e:
            print(f"Erro ao buscar documentos: {e}")
            return pd.DataFrame()

    async def get_real_analytics_data(self, user_id: str, date_range: Tuple = None) -> pd.DataFrame:
        """
        Busca dados reais para análises

        Args:
            user_id: ID do usuário
            date_range: Tuple com (data_inicio, data_fim)

        Returns:
            DataFrame com dados de análise
        """
        try:
            # Buscar dados analíticos do usuário
            analytics_data = await self.supabase.get_analytics_data(user_id, date_range)

            if not analytics_data:
                return pd.DataFrame()

            # Converter para DataFrame
            df = pd.DataFrame(analytics_data)

            # Processar dados
            if 'date' in df.columns:
                df['Data'] = pd.to_datetime(df['date']).astype(str)
            if 'category' in df.columns:
                df['Categoria'] = df['category']
            if 'value' in df.columns:
                df['Valor'] = df['value'].astype(float)
            if 'quantity' in df.columns:
                df['Quantidade'] = df['quantity'].astype(int)

            return df

        except Exception as e:
            print(f"Erro ao buscar dados analíticos: {e}")
            return pd.DataFrame()

    async def process_uploaded_document(self, file_path: str, file_type: str, user_id: str) -> Dict:
        """
        Processa um documento enviado pelo usuário

        Args:
            file_path: Caminho do arquivo
            file_type: Tipo do arquivo (xml, pdf, png, jpg, jpeg)
            user_id: ID do usuário

        Returns:
            Dict com resultado do processamento
        """
        try:
            document_data = {}

            if file_type.lower() == 'xml':
                # Processar XML (NFe, NFCe, etc.)
                document_data = await self.xml_parser.parse_xml(file_path)

            elif file_type.lower() in ['pdf', 'png', 'jpg', 'jpeg']:
                # Processar com OCR
                extracted_text = await self.ocr_processor.process_file(file_path)
                document_data = await self.xml_parser.parse_text(extracted_text)

            else:
                return {"success": False, "error": "Tipo de arquivo não suportado"}

            if not document_data or not document_data.get("success", True):
                return {
                    "success": False,
                    "error": document_data.get("error", "Falha ao processar documento") if isinstance(document_data, dict) else "Falha ao processar documento"
                }

            raw_document = document_data.copy() if isinstance(document_data, dict) else {}

            # Salvar no banco de dados
            document_data['user_id'] = user_id
            document_data['file_name'] = Path(file_path).name
            document_data['file_path'] = file_path
            document_data['file_size_bytes'] = os.path.getsize(file_path) if os.path.exists(file_path) else None
            document_data['file_type'] = self._normalize_file_type(file_type)
            document_data['processed_at'] = datetime.utcnow().isoformat()

            prepared_payload = self._prepare_document_payload(document_data, raw_document)

            result = await self.supabase.save_document(prepared_payload)

            if not result:
                return {
                    "success": False,
                    "error": "Falha ao salvar documento no banco",
                    "data": prepared_payload
                }

            return {
                "success": True,
                "document_id": result.get('id'),
                "data": prepared_payload
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def calculate_real_metrics(self, df: pd.DataFrame) -> Dict:
        """
        Calcula métricas reais baseadas nos dados

        Args:
            df: DataFrame com dados

        Returns:
            Dict com métricas calculadas
        """
        if df.empty:
            return {
                "total_documents": 0,
                "total_value": 0,
                "avg_value": 0,
                "processed_documents": 0,
                "pending_documents": 0
            }

        metrics = {
            "total_documents": len(df),
            "total_value": float(df.get('Valor (R$)', pd.Series([0])).sum()),
            "avg_value": float(df.get('Valor (R$)', pd.Series([0])).mean()),
            "processed_documents": self._count_status(df, 'Processado'),
            "pending_documents": self._count_status(df, 'Pendente')
        }

        return metrics

    def _format_status(self, status: str) -> str:
        """Formata status para exibição"""
        status_mapping = {
            'success': '✅ Processado',
            'processed': '✅ Processado',
            'validated': '✅ Validado',
            'pending': '⚠️ Pendente',
            'warning': '⚠️ Alerta',
            'error': '❌ Erro'
        }
        return status_mapping.get(status, status)

    def _count_status(self, df: pd.DataFrame, keyword: str) -> int:
        if 'Status' not in df.columns:
            return 0
        return df['Status'].astype(str).str.contains(keyword, case=False, na=False).sum()

    def _normalize_file_type(self, file_type: str) -> Optional[str]:
        """Normaliza tipo de arquivo para corresponder ao ENUM do banco"""
        if not file_type:
            return None

        mapping = {
            'xml': 'XML',
            'pdf': 'PDF',
            'png': 'PDF',
            'jpg': 'PDF',
            'jpeg': 'PDF',
            'nfe': 'NFe',
            'nfce': 'NFCe',
            'cte': 'CTe'
        }

        normalized = mapping.get(file_type.lower(), file_type.upper())
        return normalized

    def _normalize_document_type(self, document_type: Optional[str]) -> Optional[str]:
        if not document_type:
            return None

        mapping = {
            'nfe': 'NFe',
            'nfce': 'NFCe',
            'cte': 'CTe',
            'pdf': 'PDF',
            'xml': 'XML'
        }

        return mapping.get(document_type.lower(), document_type.upper())

    def _prepare_document_payload(self, data: Dict[str, Any], raw_data: Dict[str, Any]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}

        payload['user_id'] = data.get('user_id')
        payload['file_name'] = data.get('file_name')
        payload['file_path'] = data.get('file_path')
        payload['file_size_bytes'] = data.get('file_size_bytes')
        payload['file_type'] = data.get('file_type')
        payload['document_type'] = self._normalize_document_type(data.get('document_type') or raw_data.get('document_type'))
        payload['document_number'] = data.get('document_number') or raw_data.get('document_number')
        payload['document_key'] = data.get('document_key') or raw_data.get('document_key')
        payload['issuer_name'] = data.get('issuer_name') or raw_data.get('issuer')
        payload['issuer_cnpj'] = data.get('issuer_cnpj') or raw_data.get('issuer_cnpj')
        payload['recipient_name'] = data.get('recipient_name') or raw_data.get('recipient')
        payload['recipient_cnpj'] = data.get('recipient_cnpj') or raw_data.get('recipient_cnpj')
        payload['document_date'] = self._parse_date_field(data.get('document_date') or raw_data.get('date'))
        payload['document_value'] = self._parse_numeric_field(data.get('document_value') or raw_data.get('total_value'))
        payload['tax_value'] = self._parse_numeric_field(data.get('tax_value') or (raw_data.get('taxes', {}) if isinstance(raw_data.get('taxes'), dict) else None))
        payload['classification'] = data.get('classification') or raw_data.get('classification')
        payload['sector'] = data.get('sector') or raw_data.get('sector')
        payload['cfop'] = data.get('cfop') or raw_data.get('cfop')
        payload['ncm'] = data.get('ncm') or raw_data.get('ncm')
        payload['validation_status'] = data.get('validation_status') or raw_data.get('validation_status') or 'success'
        payload['validation_notes'] = data.get('validation_notes') or raw_data.get('validation_notes')
        payload['processed_at'] = data.get('processed_at')
        payload['ocr_confidence_score'] = data.get('ocr_confidence_score') or raw_data.get('ocr_confidence_score')
        payload['extracted_data'] = raw_data or {}
        payload['created_at'] = data.get('created_at') or datetime.utcnow().isoformat()
        payload['updated_at'] = datetime.utcnow().isoformat()

        # Remover valores None para evitar conflitos na inserção
        cleaned_payload = {k: v for k, v in payload.items() if v is not None}

        return cleaned_payload

    def _parse_date_field(self, value: Optional[Any]) -> Optional[str]:
        if not value:
            return None

        if isinstance(value, datetime):
            return value.date().isoformat()

        try:
            value_str = str(value).replace('Z', '')
            parsed = datetime.fromisoformat(value_str)
            return parsed.date().isoformat()
        except Exception:
            pass

        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y%m%d'):
            try:
                parsed = datetime.strptime(str(value), fmt)
                return parsed.date().isoformat()
            except Exception:
                continue

        return None

    def _parse_numeric_field(self, value: Optional[Any]) -> Optional[float]:
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, dict):
            total = value.get('total')
            if total is not None:
                return self._parse_numeric_field(total)
            return None

        try:
            text = str(value).replace('R$', '').replace(',', '.').strip()
            return float(text)
        except Exception:
            return None

    async def get_dashboard_data(self, user_id: str) -> Dict:
        """
        Busca dados para o dashboard

        Args:
            user_id: ID do usuário

        Returns:
            Dict com dados do dashboard
        """
        try:
            # Buscar documentos recentes
            recent_docs = await self.get_real_documents(user_id, {"limit": 5})

            # Buscar métricas
            metrics = self.calculate_real_metrics(recent_docs)

            # Buscar dados para gráficos
            chart_data = await self.get_real_analytics_data(user_id)

            return {
                "metrics": metrics,
                "recent_documents": recent_docs,
                "chart_data": chart_data,
                "alerts": await self._get_alerts(user_id)
            }

        except Exception as e:
            print(f"Erro ao buscar dados do dashboard: {e}")
            return {}

    async def _get_alerts(self, user_id: str) -> List[Dict]:
        """Busca alertas/notificações"""
        try:
            # Implementar lógica de alertas baseada nos dados reais
            alerts = []

            # Exemplo: documentos pendentes
            pending_docs = await self.supabase.get_pending_documents(user_id)
            if pending_docs:
                alerts.append({
                    "type": "info",
                    "message": f"📅 {len(pending_docs)} documentos pendentes de análise"
                })

            # Exemplo: documentos com possíveis inconsistências
            inconsistent_docs = await self.supabase.get_inconsistent_documents(user_id)
            if inconsistent_docs:
                alerts.append({
                    "type": "warning",
                    "message": f"⚠️ {len(inconsistent_docs)} documentos com possíveis inconsistências"
                })

            return alerts

        except Exception as e:
            print(f"Erro ao buscar alertas: {e}")
            return []


# Instância global do DataManager
data_manager = DataManager()
