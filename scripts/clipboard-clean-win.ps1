param(
  [ValidateSet('Two', 'All', 'Common')]
  [string]$Mode = 'Common'
)

$ErrorActionPreference = 'Stop'

$text = Get-Clipboard -Raw
if ([string]::IsNullOrEmpty($text)) {
  Write-Host 'Clipboard is empty. Copy text first, then run this command.'
  exit 0
}

switch ($Mode) {
  'Two' {
    $fixed = $text -replace '(?m)^ {2}', ''
  }
  'All' {
    # Remove leading spaces/tabs/full-width spaces only.
    # Do not use \s here, because it also matches CR/LF and can collapse blank lines.
    $fixed = $text -replace '(?m)^[ \t\u3000]+', ''
  }
  'Common' {
    # Remove only common leading whitespace across non-empty lines.
    $lines = $text -split "`r?`n", -1
    $nonEmpty = $lines | Where-Object { $_ -match '\S' }
    if ($nonEmpty.Count -eq 0) {
      $fixed = $text
    } else {
      $indents = @()
      foreach ($line in $nonEmpty) {
        if ($line -match '^[ \t\u3000]+') {
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
          if ($prefix -match '^[ \t\u3000]+$') {
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

Set-Clipboard -Value $fixed
Write-Host "Clipboard cleaned with mode: $Mode (Windows pipeline)"
