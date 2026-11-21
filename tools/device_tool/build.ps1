# build.ps1 - kompilasi HRIS Device Tool tanpa Visual Studio
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$csc  = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
if (-not (Test-Path $csc)) { throw "csc.exe tidak ditemukan: $csc" }

# Pengaman: data pengguna dan hasil build tidak boleh terdaftar di Git.
# Berlaku juga bila folder ini berada di dalam repo yang lebih besar.
if (Get-Command git -ErrorAction SilentlyContinue) {
    $inGit = $null
    try { $inGit = git -C $root rev-parse --is-inside-work-tree 2>$null } catch { }
    if ($inGit -eq 'true') {
        $bad = git -C $root ls-files | Select-String -Pattern '^data/|^bin/|\.exe$|\.hdt(data|sec|tmpl|log|bak)$'
        if ($bad) {
            Write-Host "BERHENTI: berkas data atau hasil build terdaftar di Git:" -ForegroundColor Red
            $bad | ForEach-Object { Write-Host "  $_" }
            exit 1
        }
    }
}

$bin = Join-Path $root 'bin'
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$out = Join-Path $bin 'HrisDeviceTool.exe'
$src = Get-ChildItem (Join-Path $root 'src') -Filter *.cs | ForEach-Object { $_.FullName }

$cscArgs = @('/nologo', '/platform:x86', '/target:winexe', "/out:$out",
    '/r:System.dll', '/r:System.Core.dll', '/r:System.Xml.dll',
    '/r:System.Drawing.dll', '/r:System.Windows.Forms.dll', '/r:Microsoft.CSharp.dll') + $src
& $csc $cscArgs
if ($LASTEXITCODE -ne 0) { Write-Host "Compile GAGAL." -ForegroundColor Red; exit 1 }

Write-Host "Berhasil: $out" -ForegroundColor Green
