# Cek isi hdt.sqlite (baca saja). Tidak menampilkan nama atau data pribadi.
param([string]$Db = "")
$ErrorActionPreference = "Stop"

if ([Environment]::Is64BitProcess) {
    $ps32 = Join-Path $env:WINDIR "SysWOW64\WindowsPowerShell\v1.0\powershell.exe"
    $a = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $PSCommandPath)
    if ($Db) { $a += @("-Db", $Db) }
    & $ps32 @a
    exit $LASTEXITCODE
}

$bin = Join-Path $PSScriptRoot "bin"
$dll = Join-Path $bin "System.Data.SQLite.dll"
if (-not (Test-Path $dll)) { throw "Build dulu: $dll tidak ada." }
if (-not $Db) { $Db = Join-Path $bin "data\db\hdt.sqlite" }
if (-not (Test-Path $Db)) { throw "Database belum ada: $Db (buka aplikasi lalu klik Cek database)." }

Add-Type -Path $dll
$conn = New-Object System.Data.SQLite.SQLiteConnection("Data Source=$Db;Version=3;Read Only=True;")
$conn.Open()

function Tampil($judul, $sql) {
    Write-Host ""
    Write-Host "== $judul" -ForegroundColor Cyan
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = $sql
    $r = $cmd.ExecuteReader()
    $n = 0
    while ($r.Read()) {
        $v = @()
        for ($i = 0; $i -lt $r.FieldCount; $i++) { $v += ($r.GetName($i) + "=" + $r.GetValue($i)) }
        Write-Host ("  " + ($v -join "   "))
        $n++
    }
    $r.Close()
    if ($n -eq 0) { Write-Host "  (tidak ada baris)" }
}

try {
    Write-Host "Berkas: $Db"
    Tampil "1. Versi skema" "PRAGMA user_version"
    Tampil "2. Keutuhan database" "PRAGMA integrity_check"
    Tampil "3. Jumlah baris per tabel" "select 'induk_aplikasi_lama' as tabel, count(*) as baris from induk_aplikasi_lama union all select 'user_mesin', count(*) from user_mesin union all select 'template_jari', count(*) from template_jari union all select 'mesin', count(*) from mesin union all select 'karyawan_hris', count(*) from karyawan_hris union all select 'department_hris', count(*) from department_hris"
    Tampil "4. Kelengkapan data aplikasi lama (jumlah yang kosong)" "select count(*) as total, sum(coalesce(trim(no_induk),'')='') as no_induk_kosong, sum(coalesce(trim(nama),'')='') as nama_kosong, sum(coalesce(tgl_lahir,'')='') as tgl_lahir_kosong, sum(coalesce(mulai_bekerja,'')='') as mulai_kosong, sum(coalesce(trim(departemen),'')='') as dept_kosong, sum(coalesce(trim(nomor_kartu),'')='') as kartu_kosong, sum(coalesce(trim(batasan),'')='') as batasan_kosong, sum(data_lain is not null) as ada_data_lain from induk_aplikasi_lama"
    Tampil "5. No Induk ganda (maks 20)" "select no_induk, count(*) as n from induk_aplikasi_lama where coalesce(trim(no_induk),'')<>'' group by no_induk having count(*)>1 limit 20"
    Tampil "6. Bentuk No. Akun" "select sum(id_akun glob '*[^0-9]*') as bukan_angka, sum(id_akun glob '0[0-9]*') as berawalan_nol, min(length(id_akun)) as terpendek, max(length(id_akun)) as terpanjang from induk_aplikasi_lama"
    Tampil "7. Tanggal" "select sum(tgl_lahir is not null and tgl_lahir not glob '[12][0-9][0-9][0-9]-[01][0-9]-[0-3][0-9]') as lahir_bukan_iso, sum(mulai_bekerja is not null and mulai_bekerja not glob '[12][0-9][0-9][0-9]-[01][0-9]-[0-3][0-9]') as mulai_bukan_iso, sum(data_lain like '%(mentah)=%') as tanggal_tak_terbaca from induk_aplikasi_lama"
    Tampil "8. Per berkas impor" "select sumber, count(*) as baris, min(diimpor) as pertama, max(diimpor) as terakhir from induk_aplikasi_lama group by sumber"
    Tampil "9. Sebaran Batasan" "select coalesce(batasan,'(kosong)') as batasan, count(*) as n from induk_aplikasi_lama group by 1 order by 2 desc"
    Tampil "10. Sebaran Departemen (maks 30)" "select coalesce(departemen,'(kosong)') as departemen, count(*) as n from induk_aplikasi_lama group by 1 order by 2 desc limit 30"
    Tampil "11. Silang user mesin dan aplikasi lama" "select (select count(*) from user_mesin u where not exists (select 1 from induk_aplikasi_lama i where i.id_akun = u.id_mesin)) as user_mesin_tak_ada_di_aplikasi_lama, (select count(*) from induk_aplikasi_lama i where not exists (select 1 from user_mesin u where u.id_mesin = i.id_akun)) as aplikasi_lama_tak_ada_di_mesin"
    Write-Host ""
    Write-Host "Selesai. Tidak ada nama atau data pribadi yang ditampilkan." -ForegroundColor Green
}
finally {
    $conn.Close()
}
