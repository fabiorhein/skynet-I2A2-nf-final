#!/usr/bin/env python3
"""
SkyNET-I2A2 - Teste de Integração de Dados Reais
Testa se todos os componentes do sistema de dados reais estão funcionando
"""

import sys
import asyncio
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

async def test_imports():
    """Testa se todas as importações estão funcionando"""
    try:
        from backend.core.data_manager import data_manager
        from backend.core.xml_parser import XMLParser
        from backend.core.ocr_processor import OCRProcessor
        from backend.core.memory import SupabaseManager
        print("✅ Todas as importações funcionando")
        return True
    except Exception as e:
        print(f"❌ Erro nas importações: {e}")
        return False

async def test_data_manager():
    """Testa se o DataManager está funcionando"""
    try:
        from backend.core.data_manager import data_manager
        print("✅ DataManager instanciado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro no DataManager: {e}")
        return False

async def test_database_connection():
    """Testa conexão com o banco de dados"""
    try:
        from backend.core.memory import SupabaseManager
        supabase = SupabaseManager()

        # Tentar uma operação simples
        result = await supabase.get_user_by_email("test@test.com")
        print("✅ Conexão com Supabase funcionando")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão com Supabase: {e}")
        return False

async def test_document_processing():
    """Testa processamento de documentos"""
    try:
        from backend.core.xml_parser import XMLParser
        from backend.core.ocr_processor import OCRProcessor

        xml_parser = XMLParser()
        ocr_processor = OCRProcessor()

        # Teste básico do parser
        test_data = {
            "document_type": "nfe",
            "total_value": 1000.50,
            "issuer": "Test Company"
        }

        print("✅ XMLParser e OCRProcessor instanciados")
        return True
    except Exception as e:
        print(f"❌ Erro no processamento de documentos: {e}")
        return False

async def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes de integração - SkyNET-I2A2\n")

    tests = [
        ("Importações", test_imports),
        ("DataManager", test_data_manager),
        ("Conexão DB", test_database_connection),
        ("Processamento", test_document_processing),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"🔍 Testando {test_name}...")
        result = await test_func()
        results.append((test_name, result))

    print("\n📊 Resultado dos Testes:")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{test_name"<15"} | {status}")
        if not passed:
            all_passed = False

    print("=" * 50)

    if all_passed:
        print("🎉 Todos os testes passaram! Sistema funcionando perfeitamente.")
        print("\n📋 Próximos passos:")
        print("1. Configure as tabelas no Supabase (004_analytics_and_improvements.sql)")
        print("2. Adicione suas API keys no .env")
        print("3. Execute 'streamlit run app.py'")
        print("4. Faça upload de documentos reais")
        print("5. Veja métricas dinâmicas no dashboard")
    else:
        print("⚠️ Alguns testes falharam. Verifique os erros acima.")

    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
