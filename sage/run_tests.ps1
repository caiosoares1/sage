# Script para executar os testes do projeto SAGE
# Execute este script com: .\run_tests.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SAGE - Sistema de Gestão de Estágios" -ForegroundColor Cyan
Write-Host "       Execução de Testes Unitários" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Função para executar testes
function Run-Tests {
    param (
        [string]$TestModule = "",
        [string]$Description = "Todos os testes"
    )
    
    Write-Host "Executando: $Description" -ForegroundColor Yellow
    Write-Host ""
    
    if ($TestModule -eq "") {
        python manage.py test --verbosity=2
    } else {
        python manage.py test $TestModule --verbosity=2
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

# Menu de opções
Write-Host "Escolha uma opção:" -ForegroundColor Green
Write-Host "1. Executar todos os testes"
Write-Host "2. Testes de Decorators"
Write-Host "3. Testes de Models"
Write-Host "4. Testes de Forms"
Write-Host "5. Testes de Views de Aluno"
Write-Host "6. Testes de Views de Supervisor e Coordenador"
Write-Host "7. Testes de Utilidades"
Write-Host "8. Testes de Integração"
Write-Host "9. Executar com cobertura (Coverage)"
Write-Host "0. Sair"
Write-Host ""

$opcao = Read-Host "Digite o número da opção"

switch ($opcao) {
    "1" {
        Run-Tests -Description "Todos os testes"
    }
    "2" {
        Run-Tests -TestModule "utils.test_decorators" -Description "Testes de Decorators"
    }
    "3" {
        Run-Tests -TestModule "utils.test_models" -Description "Testes de Models"
    }
    "4" {
        Run-Tests -TestModule "utils.test_forms" -Description "Testes de Forms"
    }
    "5" {
        Run-Tests -TestModule "estagio.tests" -Description "Testes de Views de Aluno"
    }
    "6" {
        Run-Tests -TestModule "admin.tests" -Description "Testes de Views de Supervisor e Coordenador"
    }
    "7" {
        Run-Tests -TestModule "utils.test_utilities" -Description "Testes de Utilidades"
    }
    "8" {
        Run-Tests -TestModule "utils.test_integration" -Description "Testes de Integração"
    }
    "9" {
        Write-Host "Executando testes com cobertura..." -ForegroundColor Yellow
        Write-Host ""
        
        # Verificar se coverage está instalado
        $coverageInstalled = pip show coverage 2>$null
        if (-not $coverageInstalled) {
            Write-Host "Coverage não está instalado. Instalando..." -ForegroundColor Yellow
            pip install coverage
        }
        
        # Executar testes com coverage
        coverage run --source='.' manage.py test
        
        Write-Host ""
        Write-Host "Gerando relatório de cobertura..." -ForegroundColor Yellow
        coverage report
        
        Write-Host ""
        Write-Host "Gerando relatório HTML..." -ForegroundColor Yellow
        coverage html
        
        Write-Host ""
        Write-Host "Relatório HTML gerado em: htmlcov/index.html" -ForegroundColor Green
        Write-Host "Abrir relatório no navegador? (s/n)" -ForegroundColor Yellow
        $abrir = Read-Host
        
        if ($abrir -eq "s" -or $abrir -eq "S") {
            Start-Process "htmlcov/index.html"
        }
    }
    "0" {
        Write-Host "Saindo..." -ForegroundColor Yellow
        exit
    }
    default {
        Write-Host "Opção inválida!" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Pressione qualquer tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
