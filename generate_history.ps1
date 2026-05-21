# generate_history.ps1

$projectDir   = "C:\Users\admin\.local\bin"
$desktop      = [Environment]::GetFolderPath('Desktop')
$outputFile   = Join-Path $desktop "history.html"
$launchBat    = "$projectDir\launch_claude.bat"
$maxCommits   = 20

function Get-GitHistory { param([string]$dir, [int]$count) }
function Get-SummaryFiles { param([string]$dir) }
function New-CommitHtml { param([hashtable]$commit) }
function New-FileHtml { param([hashtable]$file) }
function New-HistoryHtml { param([hashtable]$gitResult, [array]$files) }
