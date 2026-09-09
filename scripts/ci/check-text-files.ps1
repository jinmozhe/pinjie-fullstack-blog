param(
    [string]$Root = (Resolve-Path (Join-Path (Join-Path $PSScriptRoot "..") ".."))
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$rootPath = (Resolve-Path -LiteralPath $Root).Path
$utf8 = [System.Text.UTF8Encoding]::new($false, $true)
$issues = [System.Collections.Generic.List[string]]::new()
$extensions = @(
    ".css", ".example", ".ini", ".js", ".json", ".jsx", ".md", ".mjs",
    ".ps1", ".py", ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml"
)
$names = @(".editorconfig", ".gitattributes", ".gitignore", "CODEOWNERS")

$tracked = & git -C $rootPath -c core.quotepath=false ls-files --cached --others --exclude-standard
if ($LASTEXITCODE -ne 0) {
    throw "Unable to enumerate repository files."
}

foreach ($relativePath in $tracked) {
    $fullPath = Join-Path $rootPath $relativePath
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        continue
    }

    $item = Get-Item -Force -LiteralPath $fullPath
    if ($extensions -notcontains $item.Extension.ToLowerInvariant() -and $names -notcontains $item.Name) {
        continue
    }

    $bytes = [System.IO.File]::ReadAllBytes($fullPath)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        $issues.Add("$relativePath contains a UTF-8 BOM.")
    }

    try {
        [void]$utf8.GetString($bytes)
    } catch {
        $issues.Add("$relativePath is not valid UTF-8.")
    }

    if ($bytes.Length -gt 0 -and $bytes[$bytes.Length - 1] -ne 0x0A) {
        $issues.Add("$relativePath has no final line feed.")
    }
}

if ($issues.Count -gt 0) {
    foreach ($issue in $issues) {
        Write-Error $issue
    }
    exit 1
}

Write-Host "Text encoding and final line feed checks passed."
