# Commands arrive as UTF-8 JSON over stdin, never interpolated in shell arguments.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
try {
    $payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
    Set-Location -LiteralPath $payload.cwd
    $global:LASTEXITCODE = 0
    & ([ScriptBlock]::Create([string]$payload.command))
    $succeeded = $?
    $nativeExit = $global:LASTEXITCODE
    if (-not $succeeded) { exit 1 }
    if ($nativeExit -ne 0) { exit $nativeExit }
    exit 0
} catch {
    [Console]::Error.WriteLine($_.ToString())
    exit 1
}
