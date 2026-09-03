@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  Atualizando o Painel de Fechamento
echo ============================================
echo.

echo [1/4] Gerando data.json e data_intra_patronal.json...
python build_data.py
if errorlevel 1 (
    echo.
    echo ERRO ao gerar os dados. Corrija o problema acima e tente novamente.
    pause
    exit /b 1
)

echo.
echo [2/4] Adicionando arquivos ao git...
git add Despesa_Orcamentaria_Fiscal_2027.csv Orcamento_Receita.csv repasse-recurso.csv Despesa_Intraorcamentaria_2027.csv data.json data_intra_patronal.json

git diff --cached --quiet
if %errorlevel% equ 0 (
    echo.
    echo Nenhuma mudanca nos dados desde a ultima atualizacao. Nada para publicar.
    pause
    exit /b 0
)

echo.
echo [3/4] Criando commit...
git commit -m "Update source data and regenerate data.json"
if errorlevel 1 (
    echo.
    echo ERRO ao criar o commit. Veja a mensagem acima.
    pause
    exit /b 1
)

echo.
echo [4/4] Enviando para o GitHub...
git push
if errorlevel 1 (
    echo.
    echo ERRO ao enviar para o GitHub. Verifique sua conexao/autenticacao e tente rodar "git push" manualmente.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Painel atualizado! O site publica em 1-2 minutos:
echo  https://splor-mg.github.io/painel-fechamento-receita-despesa/
echo ============================================
pause
