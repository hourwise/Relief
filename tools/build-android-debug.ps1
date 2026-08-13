[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$gradleWrapper = Join-Path $repoRoot 'android\gradlew.bat'

if (-not (Test-Path -LiteralPath $gradleWrapper -PathType Leaf)) {
    Write-Error "Android Gradle wrapper not found at $gradleWrapper"
    exit 1
}

$sdkRoot = $null
if ($env:ANDROID_HOME) {
    $configuredSdk = Join-Path $env:ANDROID_HOME 'platforms'
    if (Test-Path -LiteralPath $configuredSdk -PathType Container) {
        $sdkRoot = (Resolve-Path -LiteralPath $env:ANDROID_HOME).Path
    }
}

if (-not $sdkRoot -and $env:LOCALAPPDATA) {
    $detectedSdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
    if (Test-Path -LiteralPath (Join-Path $detectedSdk 'platforms') -PathType Container) {
        $sdkRoot = (Resolve-Path -LiteralPath $detectedSdk).Path
    }
}

if (-not $sdkRoot) {
    Write-Error 'Android SDK not found. Set ANDROID_HOME to a valid SDK or install it under %LOCALAPPDATA%\Android\Sdk.'
    exit 1
}

if (-not $env:LOCALAPPDATA) {
    Write-Error 'LOCALAPPDATA is not set; cannot create the dedicated Relief Gradle user home.'
    exit 1
}

$gradleUserHome = Join-Path $env:LOCALAPPDATA 'Relief\gradle-user-home'
if ($gradleUserHome -match '(?i)[\\/]scoop[\\/]') {
    Write-Error "Refusing to use a Scoop Gradle home: $gradleUserHome"
    exit 1
}

New-Item -ItemType Directory -Path $gradleUserHome -Force | Out-Null

# These variables are scoped to this PowerShell process and its Gradle child only.
$env:GRADLE_USER_HOME = $gradleUserHome
$env:ANDROID_HOME = $sdkRoot
$env:ANDROID_SDK_ROOT = $sdkRoot

$exitCode = 1
$locationChanged = $false
try {
    Push-Location $repoRoot
    $locationChanged = $true
    & $gradleWrapper -p android :app:assembleDebug -PreactNativeArchitectures=arm64-v8a --stacktrace --no-daemon
    $exitCode = $LASTEXITCODE
}
catch {
    Write-Error $_
}
finally {
    if ($locationChanged) {
        Pop-Location
    }
}

exit $exitCode
