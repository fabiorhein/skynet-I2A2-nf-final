"""
🚀 SkyNET-I2A2 - Agentes Autônomos para Processamento Fiscal + EDA
Sistema completo com IA Generativa para análise de documentos fiscais e dados

Desenvolvido por: Equipe SkyNET-I2A2
Tecnologias: Streamlit + FastAPI + CrewAI + Google Gemini + Supabase
"""

import streamlit as st
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import uuid
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
import tempfile

# Adiciona o backend ao path
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

# Imports locais
try:
    from backend.config import settings
    from backend.core.memory import SupabaseManager, MemoryManager
    from backend.core.data_manager import data_manager
    from backend.auth.models import UserCreate, UserLogin
    from backend.auth.password import PasswordManager
    from backend.auth.jwt_handler import JWTHandler, TokenValidator
except ImportError as e:
    st.error(f"Erro ao importar módulos: {e}")
    st.stop()

# Configuração da página
st.set_page_config(
    page_title="SkyNET-I2A2 | IA para Fiscal & Análise",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.skynet-i2a2.com',
        'Report a bug': 'https://github.com/skynet-i2a2/issues',
        'About': """
        ## SkyNET-I2A2 v1.0.0
        
        Sistema de agentes autônomos para:
        - 📄 Processamento de documentos fiscais (NFe, NFCe, CTe)
        - 📊 Análise exploratória de dados (EDA)
        - 🤖 Chat inteligente com IA
        - 📈 Geração automática de gráficos
        - 🔐 Autenticação segura com JWT
        
        **Tecnologias:**
        - Frontend: Streamlit
        - Backend: FastAPI
        - Agentes: CrewAI
        - LLM: Google Gemini
        - Banco: Supabase (PostgreSQL)
        
        Desenvolvido com ❤️ pela equipe SkyNET-I2A2
        """
    }
)

# CSS customizado
st.markdown("""
<style>
    /* Layout principal */
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #2a5298;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #333333 !important;
    }
    
    .feature-card h4 {
        color: #2a5298 !important;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .feature-card p {
        color: #555555 !important;
        line-height: 1.5;
    }
    
    .feature-card ul {
        color: #555555 !important;
    }
    
    .feature-card li {
        color: #555555 !important;
        margin-bottom: 0.25rem;
    }
    
    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    
    .sidebar-logo {
        text-align: center;
        padding: 1rem;
        margin-bottom: 2rem;
    }
    
    /* Botões customizados */
    .stButton > button {
        background: linear-gradient(90deg, #2a5298 0%, #1e3c72 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Métricas */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: #f8f9fa;
    }
    
    /* Ocultara menu do Streamlit em produção */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Correção de visibilidade de texto */
    .stMarkdown {
        color: #333333 !important;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #2a5298 !important;
    }
    
    .stMarkdown p {
        color: #555555 !important;
    }
    
    .stMarkdown ul, .stMarkdown ol {
        color: #555555 !important;
    }
    
    .stMarkdown li {
        color: #555555 !important;
    }
    
    /* Garantir que divs customizadas tenham texto visível */
    div[class*="feature-card"] {
        color: #333333 !important;
    }
    
    div[class*="feature-card"] * {
        color: inherit !important;
    }
</style>
""", unsafe_allow_html=True)

# Funções de sessão
def init_session_state():
    """Inicializa o estado da sessão"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"

def check_authentication():
    """Verifica se usuário está autenticado"""
    if not st.session_state.authenticated:
        return False
    
    # Verifica se há token válido nos cookies ou session state
    if 'access_token' in st.session_state:
        token_data = TokenValidator.validate_access_token(st.session_state.access_token)
        if token_data:
            return True
    
    # Token inválido, desloga
    logout_user()
    return False

def logout_user():
    """Realiza logout do usuário"""
    st.session_state.authenticated = False
    st.session_state.user_data = None
    st.session_state.session_id = None
    if 'access_token' in st.session_state:
        del st.session_state.access_token
    if 'refresh_token' in st.session_state:
        del st.session_state.refresh_token

async def authenticate_user(email: str, password: str) -> tuple[bool, str]:
    """Autentica usuário"""
    try:
        supabase = SupabaseManager()
        
        # Busca usuário
        user = await supabase.get_user_by_email(email)
        if not user:
            return False, "Email ou senha incorretos"
        
        # Verifica senha
        if not PasswordManager.verify_password(password, user['password_hash']):
            return False, "Email ou senha incorretos"
        
        # Verifica se conta está ativa
        if not user.get('is_active', False):
            return False, "Conta inativa. Contate o suporte."
        
        # Gera tokens
        tokens = JWTHandler.create_token_pair(user['id'], user['email'])
        
        # Salva no session state
        st.session_state.authenticated = True
        st.session_state.user_data = user
        st.session_state.access_token = tokens['access_token']
        st.session_state.refresh_token = tokens['refresh_token']
        st.session_state.session_id = str(uuid.uuid4())
        
        return True, "Login realizado com sucesso!"
        
    except Exception as e:
        return False, f"Erro interno: {str(e)}"

async def register_user(user_data: dict) -> tuple[bool, str]:
    """Registra novo usuário"""
    try:
        supabase = SupabaseManager()
        
        # Verifica se email já existe
        existing_user = await supabase.get_user_by_email(user_data['email'])
        if existing_user:
            return False, "Email já está em uso"
        
        # Valida senha
        is_strong, issues = PasswordManager.check_password_strength(user_data['password'])
        if not is_strong:
            return False, f"Senha fraca: {', '.join(issues)}"
        
        # Cria usuário
        password_hash = PasswordManager.hash_password(user_data['password'])
        user_dict = {**user_data}
        del user_dict['password']
        del user_dict['confirm_password']
        user_dict['password_hash'] = password_hash
        user_dict['id'] = str(uuid.uuid4())
        
        await supabase.create_user(user_dict)
        return True, "Usuário criado com sucesso! Faça login para continuar."
        
    except Exception as e:
        return False, f"Erro ao criar usuário: {str(e)}"

# Interface principal
def main():
    """Função principal da aplicação"""
    init_session_state()
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🚀 SkyNET-I2A2</h1>
        <h3>Agentes Autônomos para Processamento Fiscal + EDA</h3>
        <p>Análise inteligente de documentos fiscais e dados com IA Generativa</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <h2>🤖 SkyNET-I2A2</h2>
            <p>Powered by AI</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Menu de navegação
        if st.session_state.authenticated:
            st.success(f"👋 Olá, {st.session_state.user_data.get('full_name', 'Usuário')}")
            
            # Estatísticas rápidas
            st.markdown("### 📊 Resumo")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Documentos", "12", "↗️ +3")
            with col2:
                st.metric("Análises", "8", "↗️ +2")
            
            st.markdown("---")
            
            # Botões de navegação
            if st.button("🏠 Dashboard", use_container_width=True):
                st.session_state.nav_trigger = "🏠 Dashboard"
                st.rerun()

            if st.button("📊 Análise de Dados", use_container_width=True):
                st.session_state.nav_trigger = "📊 Análise de Dados"
                st.rerun()

            if st.button("📄 Documentos Fiscais", use_container_width=True):
                st.session_state.nav_trigger = "📄 Documentos Fiscais"
                st.rerun()

            if st.button("💬 Chat IA", use_container_width=True):
                st.session_state.nav_trigger = "💬 Chat IA"
                st.rerun()

            if st.button("👤 Perfil", use_container_width=True):
                st.session_state.nav_trigger = "👤 Perfil"
                st.rerun()
            
            st.markdown("---")
            
            if st.button("🚪 Logout", use_container_width=True):
                logout_user()
                st.rerun()
        
        else:
            st.markdown("### 🔐 Acesso")
            auth_mode = st.selectbox("Escolha uma opção:", ["Login", "Registrar"])
            
            if auth_mode == "Login":
                show_login_form()
            else:
                show_register_form()
    
    # Conteúdo principal
    if st.session_state.authenticated:
        show_authenticated_content()
    else:
        show_public_content()

def show_login_form():
    """Formulário de login"""
    with st.form("login_form"):
        st.markdown("#### 📧 Login")
        email = st.text_input("Email", placeholder="seu@email.com")
        password = st.text_input("Senha", type="password", placeholder="Sua senha")
        remember_me = st.checkbox("Lembrar de mim")
        
        if st.form_submit_button("🔓 Entrar", use_container_width=True):
            if email and password:
                # Executa autenticação
                with st.spinner("Autenticando..."):
                    success, message = asyncio.run(authenticate_user(email, password))
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Preencha todos os campos")

def show_register_form():
    """Formulário de registro"""
    with st.form("register_form"):
        st.markdown("#### 📝 Criar Conta")
        
        email = st.text_input("Email", placeholder="seu@email.com")
        full_name = st.text_input("Nome Completo", placeholder="Seu nome")
        company_name = st.text_input("Empresa (opcional)", placeholder="Nome da empresa")
        industry = st.selectbox("Setor", [
            "Indústria", "Comércio", "Agronegócio", 
            "Serviços", "Tecnologia", "Outros"
        ])
        
        col1, col2 = st.columns(2)
        with col1:
            password = st.text_input("Senha", type="password", placeholder="Mín. 8 caracteres")
        with col2:
            confirm_password = st.text_input("Confirmar Senha", type="password")
        
        terms = st.checkbox("Li e aceito os termos de uso")
        
        if st.form_submit_button("✅ Criar Conta", use_container_width=True):
            if not all([email, full_name, password, confirm_password]):
                st.warning("Preencha todos os campos obrigatórios")
            elif password != confirm_password:
                st.error("Senhas não coincidem")
            elif not terms:
                st.warning("Aceite os termos de uso para continuar")
            else:
                user_data = {
                    'email': email,
                    'full_name': full_name,
                    'company_name': company_name,
                    'industry': industry,
                    'password': password,
                    'confirm_password': confirm_password
                }
                
                with st.spinner("Criando conta..."):
                    success, message = asyncio.run(register_user(user_data))
                
                if success:
                    st.success(message)
                else:
                    st.error(message)

def show_public_content():
    """Conteúdo para usuários não autenticados"""
    
    # Seção de recursos
    st.markdown("## 🌟 Recursos Principais")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>📄 Documentos Fiscais</h4>
            <p>Processamento automático de NFe, NFCe e CTe com OCR e validação fiscal inteligente.</p>
            <ul>
                <li>Extração automática de dados</li>
                <li>Validação de CFOP e NCM</li>
                <li>Classificação por setor</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>📊 Análise de Dados</h4>
            <p>EDA automatizada com geração de insights e gráficos interativos.</p>
            <ul>
                <li>Upload de CSV/Excel</li>
                <li>Estatísticas descritivas</li>
                <li>Detecção de outliers</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>🤖 Agentes IA</h4>
            <p>Sistema de agentes autônomos para análise e consultoria inteligente.</p>
            <ul>
                <li>Chat contextualizado</li>
                <li>Recomendações automáticas</li>
                <li>Relatórios personalizados</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Demonstração
    st.markdown("## 🎯 Demonstração")
    
    demo_tab1, demo_tab2, demo_tab3 = st.tabs(["📊 Análise", "📄 Documentos", "💬 Chat"])
    
    with demo_tab1:
        st.markdown("### Exemplo: Análise de Vendas")
        
        # Dados de exemplo
        import pandas as pd
        import numpy as np
        
        # Gera dados sintéticos
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        data = {
            'Data': dates,
            'Vendas': np.random.normal(10000, 2000, 100),
            'Produto': np.random.choice(['A', 'B', 'C'], 100),
            'Região': np.random.choice(['Norte', 'Sul', 'Sudeste'], 100)
        }
        df = pd.DataFrame(data)
        
        st.dataframe(df.head(), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Vendas", f"R$ {df['Vendas'].sum():,.2f}")
        with col2:
            st.metric("Ticket Médio", f"R$ {df['Vendas'].mean():,.2f}")
    
    with demo_tab2:
        st.markdown("### Exemplo: NFe Processada")
        st.json({
            "numero_documento": "000000123",
            "emissor": "Empresa XYZ Ltda",
            "cnpj_emissor": "12.345.678/0001-99",
            "valor_total": 15750.80,
            "data_emissao": "2024-10-20",
            "cfop": "5102",
            "status_validacao": "✅ Válido"
        })
    
    with demo_tab3:
        st.markdown("### Exemplo: Conversa com IA")
        
        # Simulação de chat
        messages = [
            {"role": "user", "content": "Analise as vendas do último trimestre"},
            {"role": "assistant", "content": "Com base nos dados analisados, identifiquei os seguintes insights:\n\n1. **Crescimento**: Aumento de 15% nas vendas\n2. **Produto líder**: Produto A representa 45% do faturamento\n3. **Região forte**: Sudeste concentra 60% das vendas\n\n**Recomendação**: Expandir marketing na região Norte para equilibrar a distribuição."}
        ]
        
        for msg in messages:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])

def show_authenticated_content():
    """Conteúdo para usuários autenticados"""
    # Definir a página padrão se não existir
    if "navigation" not in st.session_state:
        st.session_state.navigation = "🏠 Dashboard"
    if "nav_trigger" not in st.session_state:
        st.session_state.nav_trigger = "🏠 Dashboard"
    
    # Atualizar a navegação baseada na seleção do usuário
    nav_options = [
        "🏠 Dashboard", 
        "📊 Análise de Dados", 
        "📄 Documentos Fiscais", 
        "💬 Chat IA", 
        "👤 Perfil"
    ]
    
    # Usar o índice para evitar problemas com emojis
    selected_index = nav_options.index(st.session_state.nav_trigger) if st.session_state.nav_trigger in nav_options else 0
    
    # Widget de navegação na sidebar
    with st.sidebar:
        selected = st.selectbox(
            "Navegação",
            nav_options,
            index=selected_index,
            key="nav_selectbox",
            label_visibility="collapsed"
        )
        
        # Atualizar a navegação se mudou
        if selected != st.session_state.navigation:
            st.session_state.navigation = selected
            st.session_state.nav_trigger = selected
    
    # Mostrar a página selecionada
    if st.session_state.navigation == "🏠 Dashboard":
        show_dashboard()
    elif st.session_state.navigation == "📊 Análise de Dados":
        show_analysis_page()
    elif st.session_state.navigation == "📄 Documentos Fiscais":
        show_documents_page()
    elif st.session_state.navigation == "💬 Chat IA":
        show_chat_page()
    elif st.session_state.navigation == "👤 Perfil":
        show_profile_page()

async def get_dashboard_data(user_id: str) -> dict:
    """Busca dados reais para o dashboard"""
    return await data_manager.get_dashboard_data(user_id)

def show_dashboard():
    """Dashboard principal"""
    st.markdown("## 📊 Dashboard")

    # Buscar dados reais
    if st.session_state.authenticated:
        user_id = st.session_state.user_data.get('id')
        dashboard_data = asyncio.run(get_dashboard_data(user_id))
    else:
        dashboard_data = {}

    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)

    metrics = dashboard_data.get('metrics', {})

    with col1:
        st.metric("📄 Documentos Processados", f"{metrics.get('total_documents', 0):,}", "↗️ 12%")
    with col2:
        st.metric("💰 Valor Total", f"R$ {metrics.get('total_value', 0):,.2f}", "↗️ 8%")
    with col3:
        st.metric("🏢 Empresas", "24", "→ 0%")
    with col4:
        st.metric("💬 Conversas", "45", "↗️ +12")

    st.markdown("---")

    # Gráficos e visualizações
    tab1, tab2, tab3 = st.tabs(["📈 Visão Geral", "📅 Mensal", "🏷️ Por Categoria"])

    chart_data = dashboard_data.get('chart_data', pd.DataFrame())

    with tab1:
        st.markdown("### 📈 Visão Geral")

        if not chart_data.empty:
            # Gráfico com dados reais
            st.area_chart(
                chart_data,
                x='Data',
                y='Valor',
                use_container_width=True,
                color=["#2a5298"]
            )

            # Tabela com dados reais
            st.dataframe(
                chart_data.head(10),
                use_container_width=True,
                hide_index=True
            )
        else:
            # Fallback para dados vazios
            st.info("📊 Nenhum dado disponível. Envie documentos para ver análises.")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Média Diária", "R$ 0,00", "0%")
            with col2:
                st.metric("Documentos/Dia", "0", "0%")

    with tab2:
        st.markdown("### 📅 Análise Mensal")
        if not chart_data.empty:
            # Gráfico mensal com dados reais
            monthly_data = chart_data.groupby(pd.to_datetime(chart_data['Data']).dt.strftime('%b')).agg({'Valor': 'sum'}).reset_index()
            st.bar_chart(
                monthly_data.set_index('Data')['Valor'],
                use_container_width=True,
                color=["#2a5298"]
            )
        else:
            st.info("📊 Dados mensais não disponíveis")

    with tab3:
        st.markdown("### 🏷️ Por Categoria")
        if not chart_data.empty:
            # Gráfico por categoria com dados reais
            category_data = chart_data.groupby('Categoria').agg({'Valor': 'sum'}).reset_index()
            st.bar_chart(
                category_data.set_index('Categoria')['Valor'],
                use_container_width=True,
                color=["#2a5298"]
            )
        else:
            st.info("📊 Dados por categoria não disponíveis")

    # Seção de alertas
    st.markdown("### ⚠️ Alertas e Notificações")

    alerts = dashboard_data.get('alerts', [])

    if alerts:
        alert_col1, alert_col2 = st.columns(2)

        with alert_col1:
            with st.expander(f"🔔 Notificações ({len(alerts)})", expanded=True):
                for alert in alerts[:3]:  # Mostrar primeiros 3 alertas
                    if alert['type'] == 'info':
                        st.info(alert['message'])
                    elif alert['type'] == 'warning':
                        st.warning(alert['message'])
                    elif alert['type'] == 'success':
                        st.success(alert['message'])
    else:
        alert_col1, alert_col2 = st.columns(2)

        with alert_col1:
            with st.expander("🔔 Notificações", expanded=True):
                st.info("✅ Nenhum alerta no momento")

    with alert_col2:
        with st.expander("📊 Insights", expanded=True):
            if not chart_data.empty:
                top_category = chart_data.groupby('Categoria')['Valor'].sum().idxmax()
                avg_value = chart_data['Valor'].mean()
                st.info(f"💡 Categoria principal: **{top_category}**")
                st.info(f"📈 Valor médio: **R$ {avg_value:,.2f}**")
            else:
                st.info("💡 Envie documentos para ver insights")

    # Últimos documentos processados
    st.markdown("### 📋 Últimos Documentos")

    recent_documents = dashboard_data.get('recent_documents', pd.DataFrame())

    if not recent_documents.empty:
        st.dataframe(
            recent_documents,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Data': st.column_config.TextColumn("Data"),
                'Número': "Número",
                'Fornecedor': "Fornecedor",
                'Valor (R$)': st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                'Status': "Status"
            }
        )
    else:
        st.info("📄 Nenhum documento encontrado. Use a seção 'Documentos Fiscais' para enviar documentos.")

    # Seção de atividades recentes
    st.markdown("### 📈 Atividade Recente")

    # Lista de atividades simuladas (por enquanto)
    activities = [
        {"time": "10:30", "action": "Sistema inicializado", "status": "✅"},
        {"time": "10:15", "action": "Aguardando upload de documentos", "status": "⏳"},
        {"time": "09:45", "action": "Dashboard carregado", "status": "✅"},
    ]

    for activity in activities:
        with st.container():
            cols = st.columns([1, 4, 1])
            with cols[0]:
                st.text(activity["time"])
            with cols[1]:
                st.text(activity["action"])
            with cols[2]:
                st.text(activity["status"])
        st.markdown("---", unsafe_allow_html=True)

    # Ações rápidas na sidebar ou em uma nova coluna
    col1, col2 = st.columns([3, 1])

    with col2:
        st.markdown("### 🎯 Ações Rápidas")

        if st.button("📄 Novo Documento", use_container_width=True):
            st.session_state.nav_trigger = "📄 Documentos Fiscais"
            st.rerun()

        if st.button("📊 Nova Análise", use_container_width=True):
            st.session_state.nav_trigger = "📊 Análise de Dados"
            st.rerun()

        if st.button("💬 Abrir Chat", use_container_width=True):
            st.session_state.nav_trigger = "💬 Chat IA"
            st.rerun()

def show_analysis_page():
    """Página de análise de dados"""
    st.markdown("## 📊 Análise de Dados")

    # Buscar dados reais
    if st.session_state.authenticated:
        user_id = st.session_state.user_data.get('id')
        # Buscar dados de análise do usuário
        analytics_data = asyncio.run(data_manager.get_real_analytics_data(user_id))
    else:
        analytics_data = pd.DataFrame()

    # Filtros
    st.sidebar.markdown("### 🔍 Filtros")
    date_range = st.sidebar.date_input(
        "Período",
        value=[datetime.now() - pd.Timedelta(days=30), datetime.now()],
        max_value=datetime.now(),
        format="DD/MM/YYYY"
    )

    categories = st.sidebar.multiselect(
        "Categorias",
        options=["Alimentos", "Eletrônicos", "Vestuário", "Serviços", "Outros"],
        default=["Alimentos", "Eletrônicos"]
    )

    # Filtrar dados por data e categoria
    if not analytics_data.empty:
        # Converter Data para datetime para filtrar
        analytics_data['Data'] = pd.to_datetime(analytics_data['Data'])

        # Aplicar filtros de data
        mask_date = (analytics_data['Data'] >= pd.to_datetime(date_range[0])) & \
                   (analytics_data['Data'] <= pd.to_datetime(date_range[1]))

        # Aplicar filtros de categoria
        if categories:
            mask_category = analytics_data['Categoria'].isin(categories)
            filtered_data = analytics_data[mask_date & mask_category]
        else:
            filtered_data = analytics_data[mask_date]

        # Converter Data de volta para string
        filtered_data['Data'] = filtered_data['Data'].astype(str)
        df = filtered_data
    else:
        df = pd.DataFrame()

    # Métricas principais
    st.markdown("### 📈 Métricas Principais")

    col1, col2, col3, col4 = st.columns(4)

    if not df.empty:
        with col1:
            st.metric("📊 Total de Vendas", f"R$ {df['Valor'].sum():,.2f}")
        with col2:
            st.metric("📦 Itens Vendidos", f"{df['Quantidade'].sum():,}")
        with col3:
            st.metric("🏪 Categorias", len(categories) if categories else df['Categoria'].nunique())
        with col4:
            st.metric("📅 Período", f"{date_range[0].strftime('%d/%m/%Y')} - {date_range[1].strftime('%d/%m/%Y')}")
    else:
        with col1:
            st.metric("📊 Total de Vendas", "R$ 0,00")
        with col2:
            st.metric("📦 Itens Vendidos", "0")
        with col3:
            st.metric("🏪 Categorias", "0")
        with col4:
            st.metric("📅 Período", f"{date_range[0].strftime('%d/%m/%Y')} - {date_range[1].strftime('%d/%m/%Y')}")

        st.info("📊 Nenhum dado encontrado para os filtros selecionados")

    st.markdown("---")

    # Gráficos
    tab1, tab2, tab3 = st.tabs(["📅 Evolução Temporal", "📊 Por Categoria", "🧮 Análise Detalhada"])

    with tab1:
        st.markdown("### 📅 Evolução das Vendas")

        if not df.empty:
            # Gráfico de linha para valor total
            st.area_chart(
                df,
                x='Data',
                y='Valor',
                use_container_width=True,
                color=["#2a5298"]
            )

            # Tabela com os dados
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Data': st.column_config.TextColumn("Data"),
                    'Valor': st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                    'Quantidade': "Quantidade",
                    'Categoria': "Categoria"
                }
            )
        else:
            st.info("📊 Nenhum dado temporal disponível")

    with tab2:
        st.markdown("### 📊 Vendas por Categoria")

        if not df.empty:
            # Gráfico de barras
            category_chart = df.groupby('Categoria')['Valor'].sum().reset_index()
            st.bar_chart(
                category_chart.set_index('Categoria')['Valor'],
                use_container_width=True,
                color=["#2a5298"]
            )

            # Gráfico de pizza
            st.markdown("#### Distribuição por Categoria")
            fig, ax = plt.subplots()
            ax.pie(
                category_chart['Valor'],
                labels=category_chart['Categoria'],
                autopct='%1.1f%%',
                startangle=90,
                colors=['#2a5298', '#5b6abf', '#8a89e8', '#b9a9ff', '#e8c9ff']
            )
            ax.axis('equal')
            st.pyplot(fig)
        else:
            st.info("📊 Nenhum dado por categoria disponível")

    with tab3:
        st.markdown("### 🧮 Análise Detalhada")

        if not df.empty:
            # Estatísticas descritivas
            st.markdown("#### Estatísticas Descritivas")
            st.dataframe(
                df.describe(),
                use_container_width=True
            )

            # Correlação
            st.markdown("#### Matriz de Correlação")
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 1:
                corr = df[numeric_cols].corr()
                fig, ax = plt.subplots()
                sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1, ax=ax)
                st.pyplot(fig)
            else:
                st.info("📊 Dados insuficientes para correlação")

            # Análise de tendência (se houver dados suficientes)
            if len(df) > 5:
                st.markdown("#### Análise de Tendência")

                # Modelo de regressão simples
                df_sorted = df.sort_values('Data')
                X = np.arange(len(df_sorted)).reshape(-1, 1)
                y = df_sorted['Valor'].values

                model = LinearRegression().fit(X, y)
                trend = model.predict(X)

                fig, ax = plt.subplots()
                ax.plot(df_sorted['Data'], y, label='Vendas')
                ax.plot(df_sorted['Data'], trend, 'r--', label='Tendência')
                ax.set_xlabel('Data')
                ax.set_ylabel('Valor (R$)')
                ax.legend()
                st.pyplot(fig)
        else:
            st.info("📊 Nenhum dado disponível para análise detalhada")

    # Seção de insights
    st.markdown("---")
    st.markdown("### 💡 Insights e Recomendações")

    if not df.empty:
        # Gerar insights básicos
        top_category = df.groupby('Categoria')['Valor'].sum().idxmax()
        avg_sale = df['Valor'].mean()
        total_value = df['Valor'].sum()

        col1, col2 = st.columns(2)

        with col1:
            with st.expander("🔍 Principais Descobertas", expanded=True):
                st.info(f"📌 A categoria **{top_category}** representa a maior fatia das vendas")
                st.info(f"📌 O valor médio por venda é de **R$ {avg_sale:,.2f}**")
                st.info(f"📌 Volume total analisado: **R$ {total_value:,.2f}**")

        with col2:
            with st.expander("🚀 Recomendações", expanded=True):
                st.success("✅ Aumentar o estoque da categoria de maior venda")
                st.success("✅ Criar promoções para as categorias com menor desempenho")
                st.success("✅ Manter o foco na tendência de crescimento observada")
    else:
        st.info("💡 Envie documentos fiscais para gerar insights automáticos")

def show_documents_page():
    """Página de documentos fiscais"""
    st.markdown("## 📄 Documentos Fiscais")

    # Buscar documentos reais
    if st.session_state.authenticated:
        user_id = st.session_state.user_data.get('id')
        documents_data = asyncio.run(data_manager.get_real_documents(user_id))
    else:
        documents_data = pd.DataFrame()

    # Filtros
    st.sidebar.markdown("### 🔍 Filtros")

    # Filtro de tipo de documento
    doc_type = st.sidebar.selectbox(
        "Tipo de Documento",
        ["Todos", "NFe", "NFCe", "CTe", "MDFe", "Outros"]
    )

    # Filtro de data
    date_range = st.sidebar.date_input(
        "Período",
        value=[datetime.now() - pd.Timedelta(days=30), datetime.now()],
        max_value=datetime.now(),
        format="DD/MM/YYYY"
    )

    # Filtro de status
    status = st.sidebar.multiselect(
        "Status",
        ["Pendente", "Processado", "Erro", "Validado"],
        default=["Pendente", "Processado"]
    )

    # Filtro de valor
    min_val, max_val = st.sidebar.slider(
        "Faixa de Valor (R$)",
        0.0, 100000.0, (0.0, 10000.0),
        step=100.0,
        format="R$ %.2f"
    )

    # Upload de novos documentos
    st.sidebar.markdown("### 📤 Novo Documento")
    uploaded_files = st.sidebar.file_uploader(
        "Arraste ou selecione arquivos",
        type=["xml", "pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    if uploaded_files:
        progress_text = "Processando documentos..."
        progress_bar = st.sidebar.progress(0, text=progress_text)

        for i, uploaded_file in enumerate(uploaded_files):
            # Salvar arquivo temporariamente e processar
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_file_path = temp_file.name

            try:
                # Processar documento
                result = asyncio.run(data_manager.process_uploaded_document(
                    temp_file_path,
                    uploaded_file.name.split('.')[-1],
                    user_id
                ))

                if result["success"]:
                    st.sidebar.success(f"✅ Documento {uploaded_file.name} processado com sucesso!")
                else:
                    st.sidebar.error(f"❌ Erro ao processar {uploaded_file.name}: {result['error']}")

            except Exception as e:
                st.sidebar.error(f"❌ Erro ao processar {uploaded_file.name}: {str(e)}")

            finally:
                # Limpar arquivo temporário
                os.unlink(temp_file_path)

            # Atualizar progresso
            progress = (i + 1) / len(uploaded_files)
            progress_bar.progress(progress, text=f"Processando {i+1} de {len(uploaded_files)}...")

        progress_bar.empty()
        st.rerun()  # Recarregar página para mostrar novos documentos

    # Título e ações
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### 📋 Lista de Documentos")

    with col2:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.rerun()

    # Aplicar filtros aos dados
    df_docs = documents_data.copy() if not documents_data.empty else pd.DataFrame()

    if not df_docs.empty:
        # Filtros de data
        if 'Data' in df_docs.columns:
            df_docs['Data'] = pd.to_datetime(df_docs['Data'], format='%d/%m/%Y', errors='coerce')
            mask_date = (df_docs['Data'] >= pd.to_datetime(date_range[0])) & \
                       (df_docs['Data'] <= pd.to_datetime(date_range[1]))
            df_docs = df_docs[mask_date]
            df_docs['Data'] = df_docs['Data'].dt.strftime('%d/%m/%Y')

        # Filtro de tipo
        if doc_type != "Todos" and 'Tipo' in df_docs.columns:
            df_docs = df_docs[df_docs['Tipo'] == doc_type]

        # Filtro de status
        if status and 'Status' in df_docs.columns:
            status_filter = [s.replace('✅ ', '').replace('⚠️ ', '').replace('❌ ', '') for s in status]
            df_docs = df_docs[df_docs['Status'].isin(status_filter)]

        # Filtro de valor
        if 'Valor (R$)' in df_docs.columns:
            df_docs = df_docs[
                (df_docs['Valor (R$)'] >= min_val) &
                (df_docs['Valor (R$)'] <= max_val)
            ]

        # Ordenar por data (mais recente primeiro)
        if 'Data' in df_docs.columns:
            df_docs['Data'] = pd.to_datetime(df_docs['Data'], format='%d/%m/%Y', errors='coerce')
            df_docs = df_docs.sort_values('Data', ascending=False, na_position='last')
            df_docs['Data'] = df_docs['Data'].dt.strftime('%d/%m/%Y').fillna('N/A')

    # Exibir tabela de documentos
    if not df_docs.empty:
        st.dataframe(
            df_docs,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Número": "Número",
                "Tipo": "Tipo",
                "Data": st.column_config.TextColumn("Data"),
                "Fornecedor": "Fornecedor",
                "Valor (R$)": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    help="Status do documento",
                    options=["Pendente", "Processado", "Erro", "Validado"],
                    width="medium"
                ),
                "Ações": "Ações"
            }
        )
    else:
        if documents_data.empty:
            st.info("📄 Nenhum documento encontrado. Use o upload para enviar seus documentos fiscais.")
        else:
            st.warning("📄 Nenhum documento encontrado com os filtros selecionados.")

    # Estatísticas
    st.markdown("### 📊 Estatísticas dos Documentos")

    if not df_docs.empty:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📄 Total", len(df_docs))
        with col2:
            total_value = df_docs.get('Valor (R$)', pd.Series([0])).sum()
            st.metric("💰 Valor Total", f"R$ {total_value:,.2f}")
        with col3:
            avg_daily = len(df_docs) / 30 if len(date_range) > 1 and (date_range[1] - date_range[0]).days > 0 else 0
            st.metric("📅 Média Diária", f"{avg_daily:.1f}")
        with col4:
            processed_count = len(df_docs[df_docs.get('Status') == 'Processado']) if 'Status' in df_docs.columns else 0
            st.metric("✅ Processados", f"{processed_count}")

        # Gráficos
        tab1, tab2 = st.tabs(["📅 Por Data", "📊 Por Tipo"])

        with tab1:
            # Gráfico por data
            if 'Data' in df_docs.columns and 'Valor (R$)' in df_docs.columns:
                df_date = df_docs.groupby('Data').agg({'Valor (R$)': 'sum', 'Número': 'count'}).reset_index()
                if not df_date.empty:
                    st.bar_chart(
                        df_date.set_index('Data')['Valor (R$)'],
                        use_container_width=True,
                        color=["#2a5298"]
                    )
                else:
                    st.info("📊 Nenhum dado temporal disponível")

        with tab2:
            # Gráfico por tipo
            if 'Tipo' in df_docs.columns and 'Valor (R$)' in df_docs.columns:
                df_type = df_docs.groupby('Tipo').agg({'Valor (R$)': 'sum', 'Número': 'count'}).reset_index()
                if not df_type.empty:
                    fig, ax = plt.subplots()
                    ax.pie(
                        df_type['Valor (R$)'],
                        labels=df_type['Tipo'],
                        autopct='%1.1f%%',
                        startangle=90,
                        colors=['#2a5298', '#5b6abf', '#8a89e8', '#b9a9ff']
                    )
                    ax.axis('equal')
                    st.pyplot(fig)
                else:
                    st.info("📊 Nenhum dado por tipo disponível")
    else:
        st.info("📊 Envie documentos para ver estatísticas detalhadas")

def show_chat_page():
    """Página de chat com IA"""
    st.markdown("## 💬 Chat com IA")
    
    # Inicializar o histórico de mensagens na sessão
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Olá! Sou o assistente virtual do SkyNET-I2A2. Como posso ajudar você hoje?"}
        ]
    
    # Sidebar com configurações
    with st.sidebar:
        st.markdown("### ⚙️ Configurações do Chat")
        
        # Modelo de IA
        model = st.selectbox(
            "Modelo de IA",
            ["Gemini Pro", "GPT-4", "Claude 3"],
            index=0
        )
        
        # Temperatura (criatividade)
        temperature = st.slider(
            "Criatividade",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Controle o nível de criatividade das respostas"
        )
        
        # Histórico de conversas
        st.markdown("---")
        st.markdown("### 💾 Histórico")
        
        # Opção para limpar o chat
        if st.button("🗑️ Limpar Chat", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "Olá! Sou o assistente virtual do SkyNET-I2A2. Como posso ajudar você hoje?"}
            ]
            st.rerun()
        
        # Salvar conversa
        if st.button("💾 Salvar Conversa", use_container_width=True):
            # Gera um nome de arquivo com a data/hora atual
            filename = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            # Formata as mensagens para salvar
            chat_content = ""
            for msg in st.session_state.messages:
                role = "Você" if msg["role"] == "user" else "Assistente"
                chat_content += f"{role}: {msg['content']}\n\n"
            
            # Cria um botão de download
            st.download_button(
                label="⬇️ Baixar Conversa",
                data=chat_content,
                file_name=filename,
                mime="text/plain"
            )
    
    # Exibir mensagens do chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Área de entrada de mensagem
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Adiciona a mensagem do usuário ao histórico
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Exibe a mensagem do usuário
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Simula o processamento da IA
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Simula o streaming da resposta
            assistant_response = generate_ai_response(prompt, model, temperature)
            
            # Simula o carregamento da resposta
            for chunk in assistant_response.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
        
        # Adiciona a resposta da IA ao histórico
        st.session_state.messages.append({"role": "assistant", "content": full_response})

def generate_ai_response(prompt: str, model: str, temperature: float) -> str:
    """Gera uma resposta simulada da IA com base no prompt"""
    # Palavras-chave para respostas específicas
    prompt_lower = prompt.lower()
    
    # Respostas baseadas em palavras-chave
    if "olá" in prompt_lower or "oi" in prompt_lower or "bom dia" in prompt_lower or "boa tarde" in prompt_lower or "boa noite" in prompt_lower:
        return f"Olá! Como posso ajudar você hoje com suas análises e documentos fiscais?"
    
    elif "como você está" in prompt_lower or "tudo bem" in prompt_lower:
        return "Estou funcionando perfeitamente! Pronto para ajudar com análises de dados, documentos fiscais e muito mais. E você, como está?"
    
    elif "obrigad" in prompt_lower:
        return "De nada! Estou aqui para ajudar. Se precisar de mais alguma coisa, é só chamar! 😊"
    
    elif "nfe" in prompt_lower or "nota fiscal" in prompt_lower:
        return """Sobre Notas Fiscais Eletrônicas (NF-e), posso ajudar com:
        
        - Consulta de chave de acesso
        - Validação de documentos
        - Cálculo de impostos
        - Emissão de relatórios
        
        O que você gostaria de saber especificamente sobre NF-e?"""
    
    elif "imposto" in prompt_lower or "icms" in prompt_lower or "ipi" in prompt_lower or "pis" in prompt_lower or "cofins" in prompt_lower:
        return """Sobre impostos, posso ajudar com:
        
        - Cálculo de ICMS, IPI, PIS e COFINS
        - Alíquotas por estado
        - Regras de substituição tributária
        - Planejamento tributário
        
        Qual imposto específico você gostaria de consultar?"""
    
    elif "relatório" in prompt_lower or "análise" in prompt_lower or "gráfico" in prompt_lower:
        return """Para gerar relatórios e análises, você pode:
        
        1. Acessar a seção "Análise de Dados"
        2. Selecionar os filtros desejados
        3. Visualizar os gráficos e métricas
        4. Exportar os resultados em diferentes formatos
        
        Posso te ajudar com alguma análise específica?"""
    
    elif "ajuda" in prompt_lower or "como usar" in prompt_lower:
        return """# Ajuda do SkyNET-I2A2
        
        ## Principais funcionalidades:
        - **Dashboard**: Visualize métricas e indicadores em tempo real
        - **Documentos Fiscais**: Gerencie e consulte notas fiscais
        - **Análise de Dados**: Gere relatórios e insights
        - **Chat IA**: Tire suas dúvidas em tempo real
        
        Como posso te ajudar hoje?"""
    
    # Resposta padrão para mensagens não reconhecidas
    return f"""Entendi que você está perguntando sobre: "{prompt}"
    
    No momento, estou configurando a integração com o modelo {model} para fornecer respostas mais precisas. Enquanto isso, posso te ajudar com:
    
    - Dúvidas sobre documentos fiscais (NF-e, NFC-e, CT-e, etc.)
    - Cálculos tributários
    - Análise de dados e relatórios
    - Configurações do sistema
    
    Como posso te ajudar hoje?"""

def show_profile_page():
    """Página de perfil do usuário"""
    st.markdown("## 👤 Perfil do Usuário")
    
    user_data = st.session_state.user_data
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📋 Informações")
        st.write(f"**Nome:** {user_data.get('full_name', 'N/A')}")
        st.write(f"**Email:** {user_data.get('email', 'N/A')}")
        st.write(f"**Empresa:** {user_data.get('company_name', 'N/A')}")
        st.write(f"**Setor:** {user_data.get('industry', 'N/A')}")
        st.write(f"**Membro desde:** {user_data.get('created_at', 'N/A')[:10]}")
    
    with col2:
        st.markdown("### ⚙️ Configurações")
        
        with st.form("profile_form"):
            full_name = st.text_input("Nome Completo", value=user_data.get('full_name', ''))
            company_name = st.text_input("Empresa", value=user_data.get('company_name', ''))
            industry = st.selectbox("Setor", [
                "Indústria", "Comércio", "Agronegócio", 
                "Serviços", "Tecnologia", "Outros"
            ], index=0)
            
            if st.form_submit_button("💾 Salvar Alterações"):
                st.success("Perfil atualizado com sucesso!")

# Execução principal
if __name__ == "__main__":
    # Carrega variáveis de ambiente em desenvolvimento
    if settings.is_development:
        from dotenv import load_dotenv
        load_dotenv()
    
    main()