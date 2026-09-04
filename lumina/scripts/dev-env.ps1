#Requires -Version 5.1
<#
.SYNOPSIS
  Discover MSVC BuildTools CMake/Ninja and prepend them to PATH for this session.
  Optionally persist the bins on the User PATH so new shells / agents find cmake.

.DESCRIPTION
  Canonical location on this machine (VS 18 BuildTools):
    D:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin
    D:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja

  Usage (from repo or lumina/):
    . .\lumina\scripts\dev-env.ps1
    . .\lumina\scripts\dev-env.ps1 -PersistUserPath
#>
[CmdletBinding()]
param(
    [switch] $PersistUserPath,
    [switch] $Quiet
)

$ErrorActionPreference = "Stop"

function Write-DevInfo([string] $Message) {
    if (-not $Quiet) { Write-Host "[dev-env] $Message" }
}

function Find-VsInstallPath {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
    $candidates = @()
    if (Test-Path -LiteralPath $vswhere) {
        $candidates += & $vswhere -latest -products * -property installationPath 2>$null
        $candidates += & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.CMake.Project -property installationPath 2>$null
    }
    $candidates += @(
        "D:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools",
        "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools",
        "C:\Program Files\Microsoft Visual Studio\2022\BuildTools",
        "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
    )
    foreach ($path in $candidates) {
        if ($path -and (Test-Path -LiteralPath $path)) { return $path }
    }
    return $null
}

function Resolve-ToolBins([string] $VsRoot) {
    $cmake = Join-Path $VsRoot "Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
    $ninja = Join-Path $VsRoot "Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja"
    $vcvars = Join-Path $VsRoot "VC\Auxiliary\Build\vcvarsall.bat"
    return [pscustomobject]@{
        CMakeBin = $cmake
        NinjaBin = $ninja
        VcVars   = $vcvars
        CMakeExe = Join-Path $cmake "cmake.exe"
        NinjaExe = Join-Path $ninja "ninja.exe"
    }
}

function Ensure-SessionPath([string[]] $Bins) {
    $parts = @($env:Path -split ";" | Where-Object { $_ -and $_.Trim() -ne "" })
    foreach ($bin in $Bins) {
        if (-not (Test-Path -LiteralPath $bin)) { continue }
        if ($parts -notcontains $bin) {
            $parts = @($bin) + $parts
        }
    }
    $env:Path = ($parts -join ";")
}

function Ensure-UserPath([string[]] $Bins) {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($null -eq $userPath) { $userPath = "" }
    $parts = @($userPath -split ";" | Where-Object { $_ -and $_.Trim() -ne "" })
    $changed = $false
    foreach ($bin in $Bins) {
        if (-not (Test-Path -LiteralPath $bin)) { continue }
        $hit = $false
        foreach ($p in $parts) {
            if ($p -ieq $bin) { $hit = $true; break }
        }
        if (-not $hit) {
            $parts = @($bin) + $parts
            $changed = $true
        }
    }
    if ($changed) {
        [Environment]::SetEnvironmentVariable("Path", ($parts -join ";"), "User")
        Write-DevInfo "Persisted CMake/Ninja bins to User PATH (new terminals pick this up)."
    }
    else {
        Write-DevInfo "User PATH already contains CMake/Ninja bins."
    }
}

$vs = Find-VsInstallPath
if (-not $vs) {
    throw "Visual Studio BuildTools not found. Install VS Build Tools with C++ + CMake components."
}

$tools = Resolve-ToolBins $vs
if (-not (Test-Path -LiteralPath $tools.CMakeExe)) {
    throw "cmake.exe missing under $vs (expected CMake component)."
}
if (-not (Test-Path -LiteralPath $tools.NinjaExe)) {
    throw "ninja.exe missing under $vs (expected CMake/Ninja component)."
}

Ensure-SessionPath @($tools.CMakeBin, $tools.NinjaBin)
$env:LUMINA_CMAKE = $tools.CMakeExe
$env:LUMINA_NINJA = $tools.NinjaExe
$env:LUMINA_VCVARS = $tools.VcVars
$env:CMAKE_GENERATOR = "Ninja"
$env:CMAKE_MAKE_PROGRAM = $tools.NinjaExe

if ($PersistUserPath) {
    Ensure-UserPath @($tools.CMakeBin, $tools.NinjaBin)
}

Write-DevInfo "VS=$vs"
Write-DevInfo "cmake=$($tools.CMakeExe)"
Write-DevInfo "ninja=$($tools.NinjaExe)"
Write-DevInfo ("cmake --version => " + (& $tools.CMakeExe --version | Select-Object -First 1))

# Export for callers that dot-source this script
$script:LuminaDevTools = $tools
