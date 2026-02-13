$ErrorActionPreference = 'Stop'

$profilePath = $PROFILE
$profileDir = Split-Path -Parent $profilePath
if (-not (Test-Path $profileDir)) {
  New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}
if (-not (Test-Path $profilePath)) {
  New-Item -ItemType File -Path $profilePath -Force | Out-Null
}

$startMarker = '# >>> codex-clipboard-tools >>>'
$endMarker = '# <<< codex-clipboard-tools <<<'

$body = @'
function cb2 {
  (Get-Clipboard -Raw) -split "`r?`n" | ForEach-Object { $_ -replace '^ {2}','' } | Set-Clipboard
}

function cball {
  (Get-Clipboard -Raw) -split "`r?`n" | ForEach-Object { $_ -replace '^[ \t]+','' } | Set-Clipboard
}
'@

$block = $startMarker + "`r`n" + $body + "`r`n" + $endMarker

$current = Get-Content -Path $profilePath -Raw
if ($current -match [regex]::Escape($startMarker) -and $current -match [regex]::Escape($endMarker)) {
  $pattern = [regex]::Escape($startMarker) + '.*?' + [regex]::Escape($endMarker)
  $updated = [regex]::Replace($current, $pattern, $block, [System.Text.RegularExpressions.RegexOptions]::Singleline)
} else {
  if ($current.Length -gt 0 -and -not $current.EndsWith("`n")) {
    $current += "`r`n"
  }
  $updated = $current + $block + "`r`n"
}

Set-Content -Path $profilePath -Value $updated -Encoding UTF8
. $profilePath

Write-Host "Installed clipboard helpers into $profilePath"
Write-Host "Use: cb2   (remove two leading spaces)"
Write-Host "Use: cball (remove all leading spaces/tabs)"
