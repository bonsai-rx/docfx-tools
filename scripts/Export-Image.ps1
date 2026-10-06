[CmdletBinding()] param(
    [string[]]$libPath,
    [string]$workflowPath=".\workflows",
    [string]$bootstrapperPath="..\.bonsai\Bonsai.exe",
    [string]$outputFolder="",
    [string]$documentationRoot="" # Only relevant when outputFolder is set
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

function Export-Svg([string[]]$libPath, [string]$svgPath, [string]$workflowFile) {
    $bootstrapperArgs = @()
    foreach ($path in $libPath) {
        $bootstrapperArgs += "--lib"
        $bootstrapperArgs += "$(Resolve-Path $path)"
    }
    $bootstrapperArgs += "--export-image"
    $bootstrapperArgs += "$svgPath"
    $bootstrapperArgs += "$workflowFile"

    if (!$IsWindows) {
        $bootstrapperArgs = @($bootstrapperPath) + $bootstrapperArgs
        $bootstrapperPath = 'mono'
    }

    Write-Verbose "$($bootstrapperPath) $($bootstrapperArgs)"
    &$bootstrapperPath $bootstrapperArgs
}

if (-not $documentationRoot) {
    $documentationRoot = Resolve-Path $workflowPath
}

Import-Module (Join-Path $PSScriptRoot "Export-Tools.psm1") -Verbose:$false

$sessionPath = $ExecutionContext.SessionState.Path
foreach ($workflowFile in Get-ChildItem -File -Recurse (Join-Path $workflowPath "*.bonsai")) {
    $svgPath = Join-Path $workflowFile.DirectoryName "$($workflowFile.BaseName).svg"
    $svgPathRelative = [IO.Path]::GetRelativePath($documentationRoot, $svgPath)

    if ($outputFolder) {
        $svgPath = Join-Path $outputFolder $svgPathRelative
        $null = New-Item -ItemType Directory -Path (Split-Path -Parent $svgPath) -Force
    }

    Write-Host "Exporting $($svgPathRelative)"
    Write-Verbose "Exporting to $($svgPath)"
    Export-Svg $libPath $svgPath $workflowFile
    Convert-Svg $svgPath
}
