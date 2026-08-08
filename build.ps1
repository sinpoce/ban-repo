param(
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"

if (-not $Python) {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        & $pyLauncher.Source -3 (Join-Path $PSScriptRoot "build.py")
        if ($LASTEXITCODE -ne 0) { throw "build.py 执行失败，退出码：$LASTEXITCODE" }
        return
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "找不到 Python 3。请安装 Python 3，或使用：.\build.ps1 -Python C:\path\to\python.exe"
    }
    $Python = $pythonCommand.Source
}

& $Python (Join-Path $PSScriptRoot "build.py")
if ($LASTEXITCODE -ne 0) { throw "build.py 执行失败，退出码：$LASTEXITCODE" }
