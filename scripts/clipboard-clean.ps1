param(
  [ValidateSet('Two', 'AsciiAll', 'UnicodeAll', 'Common')]
  [string]$Mode = 'UnicodeAll'
)

$ErrorActionPreference = 'Stop'

# Try native clipboard first.
$text = Get-Clipboard -Raw

# Fallback to Windows clipboard via powershell.exe with UTF-8 temp file bridge.
if ([string]::IsNullOrEmpty($text)) {
  if (Get-Command powershell.exe -ErrorAction SilentlyContinue) {
    $tmpRead = [System.IO.Path]::GetTempFileName()
    try {
      $tmpReadForWindows = $tmpRead
      if (Get-Command wslpath -ErrorAction SilentlyContinue) {
        $tmpReadForWindows = (& wslpath -w $tmpRead).Trim()
      }
      $escapedRead = $tmpReadForWindows.Replace("'", "''")
      powershell.exe -NoProfile -Command "`$ProgressPreference='SilentlyContinue'; Get-Clipboard -Raw | Set-Content -LiteralPath '$escapedRead' -Encoding UTF8" | Out-Null
      if (Test-Path -LiteralPath $tmpRead) {
        $text = Get-Content -LiteralPath $tmpRead -Raw -Encoding UTF8
      }
    } finally {
      Remove-Item -LiteralPath $tmpRead -Force -ErrorAction SilentlyContinue
    }
  }
}

if ([string]::IsNullOrEmpty($text)) {
  Write-Host 'Clipboard is empty. Copy text first, then run this command.'
  exit 0
}

switch ($Mode) {
  'Two' {
    # Remove only two ASCII spaces at each line start.
    $fixed = $text -replace '(?m)^ {2}', ''
  }
  'AsciiAll' {
    # Remove all leading ASCII spaces/tabs.
    $fixed = $text -replace '(?m)^[ \t]+', ''
  }
  'UnicodeAll' {
    # Remove leading Unicode separator chars (includes full-width space) and tabs.
    $fixed = $text -replace '(?m)^[\p{Z}\t]+', ''
  }
  'Common' {
    # Remove only the common leading whitespace across non-empty lines.
    # This preserves relative indentation (useful for code blocks).
    $lines = $text -split "`r?`n", -1
    $nonEmpty = $lines | Where-Object { $_ -match '\S' }
    if ($nonEmpty.Count -eq 0) {
      $fixed = $text
    } else {
      $indents = @()
      foreach ($line in $nonEmpty) {
        if ($line -match '^[\p{Z}\t ]+') {
          $indents += $matches[0].Length
        } else {
          $indents += 0
        }
      }
      $common = ($indents | Measure-Object -Minimum).Minimum
      if ($common -le 0) {
        $fixed = $text
      } else {
        $processed = foreach ($line in $lines) {
          if ($line.Length -lt $common) {
            $line
            continue
          }
          $prefix = $line.Substring(0, $common)
          if ($prefix -match '^[\p{Z}\t ]+$') {
            $line.Substring($common)
          } else {
            $line
          }
        }
        $fixed = ($processed -join "`r`n")
      }
    }
  }
}

# Write back to Windows clipboard with Unicode-safe path when available.
$wrote = $false
if (Get-Command powershell.exe -ErrorAction SilentlyContinue) {
  $tmp = [System.IO.Path]::GetTempFileName()
  try {
    Set-Content -LiteralPath $tmp -Value $fixed -Encoding UTF8
    $tmpForWindows = $tmp
    if (Get-Command wslpath -ErrorAction SilentlyContinue) {
      $tmpForWindows = (& wslpath -w $tmp).Trim()
    }
    $escaped = $tmpForWindows.Replace("'", "''")
    powershell.exe -NoProfile -Command "Get-Content -LiteralPath '$escaped' -Raw -Encoding UTF8 | Set-Clipboard" | Out-Null
    if ($LASTEXITCODE -eq 0) {
      $wrote = $true
    }
  } finally {
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
  }
}

if (-not $wrote) {
  Set-Clipboard -Value $fixed
}

Write-Host "Clipboard cleaned with mode: $Mode"
