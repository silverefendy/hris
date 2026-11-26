# Mengompilasi dan menjalankan uji SQLite (berdiri sendiri, tidak memakai build.ps1).
# Pakai: powershell -ExecutionPolicy Bypass -File .\jalankan.ps1
$ErrorActionPreference = "Stop"
$dir = $PSScriptRoot
$lib = Join-Path (Split-Path $dir -Parent) "lib"
$dll = Join-Path $lib "System.Data.SQLite.dll"
$nat = Join-Path $lib "x86\SQLite.Interop.dll"
if (-not (Test-Path $dll) -or -not (Test-Path $nat)) {
    Write-Host "Pustaka belum ada. Jalankan dulu ..\ambil_sqlite.ps1"
    exit 1
}
$csc = Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe"
if (-not (Test-Path $csc)) { throw "csc.exe tidak ditemukan: $csc" }

$bin = Join-Path $dir "bin"
New-Item -ItemType Directory -Force -Path $bin, (Join-Path $bin "x86") | Out-Null
Copy-Item $dll $bin -Force
Copy-Item $nat (Join-Path $bin "x86") -Force
Copy-Item $nat $bin -Force

& $csc /nologo /target:exe /platform:x86 "/out:$bin\UjiSqlite.exe" "/reference:$dll" "$dir\UjiSqlite.cs"
if ($LASTEXITCODE -ne 0) { Write-Host "Kompilasi GAGAL"; exit 1 }
Write-Host "Kompilasi OK. Menjalankan uji..."
Write-Host ""
& "$bin\UjiSqlite.exe"
exit $LASTEXITCODE
