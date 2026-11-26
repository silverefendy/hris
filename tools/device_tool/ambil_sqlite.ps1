# Mengunduh System.Data.SQLite (paket resmi NuGet) ke folder lib di samping skrip ini.
# Pakai: powershell -ExecutionPolicy Bypass -File .\ambil_sqlite.ps1
# Jika unduhan diblokir, unduh nupkg lewat browser lalu: .\ambil_sqlite.ps1 -Paket C:\jalur\berkas.nupkg
param(
    [string]$Versi = "1.0.109.0",
    [string]$Paket = ""
)
$ErrorActionPreference = "Stop"
$lib = Join-Path $PSScriptRoot "lib"
$tmp = Join-Path $env:TEMP ("sqlite_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $lib, $tmp | Out-Null
try {
    $zip = Join-Path $tmp "paket.zip"
    if ($Paket -ne "") {
        Write-Host "Memakai berkas lokal: $Paket"
        Copy-Item $Paket $zip -Force
    }
    else {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $url = "https://www.nuget.org/api/v2/package/System.Data.SQLite.Core/$Versi"
        Write-Host "Mengunduh: $url"
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $isi = Join-Path $tmp "isi"
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $isi)

    $dll = $null
    foreach ($p in @("lib\net40", "lib\net45", "lib\net451", "lib\net46")) {
        $k = Join-Path $isi "$p\System.Data.SQLite.dll"
        if (Test-Path $k) { $dll = $k; Write-Host "DLL .NET diambil dari: $p"; break }
    }
    if (-not $dll) { throw "System.Data.SQLite.dll tidak ditemukan di dalam paket." }

    $nat = $null
    foreach ($p in @("build\net40\x86", "build\net45\x86", "build\net46\x86", "build\net451\x86", "build\net20\x86")) {
        $k = Join-Path $isi "$p\SQLite.Interop.dll"
        if (Test-Path $k) { $nat = $k; Write-Host "DLL native diambil dari: $p"; break }
    }
    if (-not $nat) { throw "SQLite.Interop.dll (x86) tidak ditemukan di dalam paket." }

    New-Item -ItemType Directory -Force -Path (Join-Path $lib "x86") | Out-Null
    Copy-Item $dll (Join-Path $lib "System.Data.SQLite.dll") -Force
    Copy-Item $nat (Join-Path $lib "x86\SQLite.Interop.dll") -Force

    Write-Host ""
    Write-Host "Selesai. Isi folder lib:"
    Get-ChildItem -Recurse -File $lib | ForEach-Object {
        "{0}  {1:N0} byte  SHA256={2}" -f $_.FullName, $_.Length, (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    }
}
finally {
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
}
