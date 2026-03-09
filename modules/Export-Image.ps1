[CmdletBinding()] param(
    [string[]]$libPath,
    [string]$workflowPath=".\workflows",
    [string]$bootstrapperPath="..\.bonsai\Bonsai.exe",
    [string]$outputFolder="",
    [string]$documentationRoot="" # Only relevant when outputFolder is set
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Get-RelativePath([string]$basePath, [string]$targetPath) {
    $baseUri = New-Object System.Uri(($basePath.TrimEnd('\', '/') + '\'))
    $targetUri = New-Object System.Uri($targetPath)
    $relUri = $baseUri.MakeRelativeUri($targetUri)
    return [System.Uri]::UnescapeDataString($relUri.ToString()) -replace '/', [IO.Path]::DirectorySeparatorChar
}

function Export-Svg([string[]]$libPath, [string]$svgPath, [string]$workflowFile) {
    $bootstrapperArgs = @()
    foreach ($path in $libPath) {
        $bootstrapperArgs += "--lib"
        $bootstrapperArgs += "$(Resolve-Path $path)"
    }
    $bootstrapperArgs += "--export-image"
    $bootstrapperArgs += "$svgPath"
    $bootstrapperArgs += "$workflowFile"

    $isWindowsPlatform = if ($null -eq (Get-Variable 'IsWindows' -ErrorAction SilentlyContinue)) { $true } else { $IsWindows }
    if (!$isWindowsPlatform) {
        $bootstrapperArgs = @($bootstrapperPath) + $bootstrapperArgs
        $bootstrapperPath = 'mono'
    }

    Write-Verbose "$($bootstrapperPath) $($bootstrapperArgs)"
    &$bootstrapperPath $bootstrapperArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Export failed for '$workflowFile' with exit code $LASTEXITCODE."
    }
}

if (-not $documentationRoot) {
    $documentationRoot = Resolve-Path $workflowPath
}

Import-Module (Join-Path $PSScriptRoot "Export-Tools.psm1") -Verbose:$false

foreach ($workflowFile in Get-ChildItem -File -Recurse (Join-Path $workflowPath "*.bonsai")) {
    $svgPath = Join-Path $workflowFile.DirectoryName "$($workflowFile.BaseName).svg"
    $svgPathRelative = Get-RelativePath $documentationRoot $svgPath

    if ($outputFolder) {
        $svgPath = Join-Path $outputFolder $svgPathRelative
        $null = New-Item -ItemType Directory -Path (Split-Path -Parent $svgPath) -Force
    }

    Write-Host "Exporting $($svgPathRelative)"
    Write-Verbose "Exporting to $($svgPath)"
    Export-Svg $libPath $svgPath $workflowFile
    Convert-Svg $svgPath
}
