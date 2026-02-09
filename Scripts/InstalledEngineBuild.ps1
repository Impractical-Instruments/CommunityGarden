<#
Build-UEInstalledBuild.ps1

Creates a Windows-only Unreal Engine Installed Build with full PDBs.
Run from ANY folder. You point it at the engine source root.

Example:
  .\Build-UEInstalledBuild.ps1 -EngineRoot "D:\UE\UnrealEngine" -Clean

Output (default):
  <EngineRoot>\Engine\LocalBuilds\Engine\Windows\
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateScript({ Test-Path $_ -PathType Container })]
    [string]$EngineRoot,

    [string]$Target = 'Make Installed Build Win64',

    [switch]$Clean,

    [bool]$WithDDC = $false,

    [string[]]$GameConfigurations = @('Development','Shipping','DebugGame'),

    [bool]$WithFullDebugInfo = $true,

    [string[]]$ExtraUatArgs = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-FullPath([string]$p) {
    (Resolve-Path -LiteralPath $p).Path
}

$EngineRoot = Resolve-FullPath $EngineRoot

$UatBat = Join-Path $EngineRoot 'Engine\Build\BatchFiles\RunUAT.bat'
if (-not (Test-Path $UatBat -PathType Leaf)) {
    throw "RunUAT.bat not found at expected path: $UatBat`nEngineRoot should contain Engine\Build\BatchFiles\RunUAT.bat"
}

$InstalledBuildXml = 'Engine/Build/InstalledEngineBuild.xml'
$cfgString = ($GameConfigurations -join ';')

# Build arguments as an ARRAY of tokens (no manual quoting games)
$Args = @(
    'BuildGraph'
    "-script=$InstalledBuildXml"
    "-target=$Target"
    '-nosign'
    '-set:HostPlatformOnly=true'
    '-set:WithWin64=true'
    '-set:WithWin32=false'
    '-set:WithMac=false'
    '-set:WithLinux=false'
    '-set:WithLinuxArm64=false'
    '-set:WithAndroid=false'
    '-set:WithIOS=false'
    '-set:WithTVOS=false'
    "-set:WithDDC=$($WithDDC.ToString().ToLower())"
    "-set:GameConfigurations=$cfgString"
    "-set:WithFullDebugInfo=$($WithFullDebugInfo.ToString().ToLower())"
)

if ($Clean) { $Args += '-clean' }
if ($ExtraUatArgs.Count -gt 0) { $Args += $ExtraUatArgs }

Write-Host "=== Unreal Installed Build (Win64) ==="
Write-Host "EngineRoot:           $EngineRoot"
Write-Host "RunUAT:               $UatBat"
Write-Host "Target:               $Target"
Write-Host "Clean:                $Clean"
Write-Host "WithDDC:              $WithDDC"
Write-Host "GameConfigurations:   $cfgString"
Write-Host "WithFullDebugInfo:    $WithFullDebugInfo"
Write-Host "-------------------------------------"
Write-Host "Command (tokenized):"
Write-Host "  $UatBat"
$Args | ForEach-Object { Write-Host "  $_" }
Write-Host "-------------------------------------"

Push-Location $EngineRoot
try {
    # IMPORTANT: invoke with & and an argument array so spaces are handled correctly
    & $UatBat @Args

    if ($LASTEXITCODE -ne 0) {
        throw "RunUAT failed with exit code $LASTEXITCODE"
    }

    $outDir = Join-Path $EngineRoot 'Engine\LocalBuilds\Engine\Windows'
    Write-Host "=== SUCCESS ==="
    Write-Host "Installed build output (default): $outDir"
}
finally {
    Pop-Location
}
