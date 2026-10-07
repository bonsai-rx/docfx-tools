<#
.SYNOPSIS
Exports an SVG image of every Bonsai workflow in a folder, for use in documentation websites.

.DESCRIPTION
Each workflow is exported with the Bonsai environment specified by the bootstrapper path, and
the text in each image follows the light or dark color scheme of the page. Workflows are
exported in parallel. If any export fails, the failures are listed and the script ends with
an error.

Requires PowerShell 7.4 or later.

.PARAMETER libPath
Folders containing assemblies needed by the workflows, such as the build output of the
documented package.

.PARAMETER workflowPath
Folder searched recursively for workflow files. Defaults to .\workflows.

.PARAMETER bootstrapperPath
Bonsai executable of the environment used for exporting. Defaults to ..\.bonsai\Bonsai.exe.

.PARAMETER outputFolder
Folder for the exported images. Defaults to writing each image next to its workflow.

.PARAMETER documentationRoot
Root of the folder structure reproduced in the output folder. Only used with an output
folder. Defaults to the workflow folder.

.PARAMETER throttleLimit
Maximum number of workflows exported at the same time. Defaults to the number of processors.

.EXAMPLE
.\scripts\Export-Image.ps1 "..\src\PackageName\bin\Release\net472"
#>
[CmdletBinding()] param(
    [string[]]$libPath,
    [string]$workflowPath=".\workflows",
    [string]$bootstrapperPath="..\.bonsai\Bonsai.exe",
    [string]$outputFolder="",
    [string]$documentationRoot="",
    [int]$throttleLimit=[Environment]::ProcessorCount
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

function Export-Svg($export, [string[]]$libArgs, [string]$bootstrapperPath, [string]$modulePath) {
    Set-StrictMode -Version 3.0
    $PSNativeCommandUseErrorActionPreference = $false
    Import-Module $modulePath -Verbose:$false

    $bootstrapperArgs = $libArgs + @("--export-image", $export.SvgPath, $export.WorkflowFile)
    if (!$IsWindows) {
        $bootstrapperArgs = @($bootstrapperPath) + $bootstrapperArgs
        $bootstrapperPath = 'mono'
    }

    $command = "$($bootstrapperPath) $($bootstrapperArgs)"
    $output = & $bootstrapperPath $bootstrapperArgs 2>&1 | Out-String
    $failed = $LASTEXITCODE -ne 0
    if (!$failed) {
        Convert-Svg $export.SvgPath
    }
    [pscustomobject]@{ Export = $export; Command = $command; Output = $output.Trim(); Failed = $failed }
}

function Write-ExportResult($result) {
    Write-Verbose $result.Command
    if ($result.Failed) {
        Write-Host "Failed to export $($result.Export.SvgPathRelative)"
    } else {
        Write-Host "Exported $($result.Export.SvgPathRelative)"
    }
    if ($result.Output) {
        Write-Host $result.Output
    }
    $result
}

if (-not $documentationRoot) {
    $documentationRoot = Resolve-Path $workflowPath
}

$modulePath = Join-Path $PSScriptRoot "Export-Tools.psm1"
$bootstrapperPath = (Resolve-Path $bootstrapperPath).Path
$libArgs = @(foreach ($path in $libPath) { "--lib"; "$(Resolve-Path $path)" })

$sessionPath = $ExecutionContext.SessionState.Path
$exports = @(foreach ($workflowFile in Get-ChildItem -File -Recurse (Join-Path $workflowPath "*.bonsai")) {
    $svgPath = Join-Path $workflowFile.DirectoryName "$($workflowFile.BaseName).svg"
    $svgPathRelative = [IO.Path]::GetRelativePath($documentationRoot, $svgPath)

    if ($outputFolder) {
        $svgPath = Join-Path $outputFolder $svgPathRelative
        $null = New-Item -ItemType Directory -Path (Split-Path -Parent $svgPath) -Force
    }

    [pscustomobject]@{
        WorkflowFile = $workflowFile.FullName
        SvgPath = $sessionPath.GetUnresolvedProviderPathFromPSPath($svgPath)
        SvgPathRelative = $svgPathRelative
    }
})

if ($exports.Count -eq 0) {
    return
}

$results = @(Write-ExportResult (Export-Svg $exports[0] $libArgs $bootstrapperPath $modulePath))
if (!$results[0].Failed -and $exports.Count -gt 1) {
    $exportSvgDefinition = ${function:Export-Svg}.ToString()
    $results += $exports | Select-Object -Skip 1 | ForEach-Object -ThrottleLimit $throttleLimit -Parallel {
        ${function:Export-Svg} = $using:exportSvgDefinition
        Export-Svg $_ $using:libArgs $using:bootstrapperPath $using:modulePath
    } | ForEach-Object { Write-ExportResult $_ }
}

$failures = @($results | Where-Object Failed)
if ($failures.Count -gt 0) {
    throw "Failed to export $($failures.Count) of $($exports.Count) workflows: $($failures.Export.SvgPathRelative -join ', ')"
}
