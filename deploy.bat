@echo off
REM Deploy Antigravity Command Center to Google Cloud Run
REM Usage: deploy.bat
REM 
REM Prerequisites:
REM   1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
REM   2. Run: gcloud auth login
REM   3. Run this script

set PROJECT_ID=gen-lang-client-0988614926
set REGION=us-central1
set SERVICE_NAME=command-center
set IMAGE_NAME=gcr.io/%PROJECT_ID%/%SERVICE_NAME%

echo.
echo ========================================
echo   Antigravity Command Center Deploy
echo ========================================
echo   Project: %PROJECT_ID%
echo   Region: %REGION%
echo.

REM Check if gcloud is available
where gcloud >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] gcloud not found!
    echo.
    echo Please install Google Cloud SDK:
    echo   https://cloud.google.com/sdk/docs/install
    echo.
    echo Or use Cloud Shell:
    echo   https://console.cloud.google.com/cloudshell
    echo.
    pause
    exit /b 1
)

echo [1/5] Setting project...
gcloud config set project %PROJECT_ID%

echo [2/5] Enabling APIs...
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

echo [3/5] Building container...
gcloud builds submit --tag %IMAGE_NAME%:latest .

echo [4/5] Deploying to Cloud Run...
gcloud run deploy %SERVICE_NAME% ^
    --image %IMAGE_NAME%:latest ^
    --region %REGION% ^
    --platform managed ^
    --allow-unauthenticated ^
    --memory 256Mi ^
    --cpu 1 ^
    --min-instances 0 ^
    --max-instances 3 ^
    --port 8080

echo [5/5] Getting URL...
for /f "tokens=*" %%a in ('gcloud run services describe %SERVICE_NAME% --region %REGION% --format "value(status.url)"') do set URL=%%a

echo.
echo ========================================
echo   Deploy Complete!
echo ========================================
echo.
echo Your Command Center is live at:
echo   %URL%
echo.
echo Next: Update CLOUD_URL in local_agent.js with this URL
echo.
pause
