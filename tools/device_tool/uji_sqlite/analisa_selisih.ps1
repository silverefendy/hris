# Analisa selisih byte antara .mdb dan mesin (hanya membaca)
param([Parameter(Mandatory = $true)][string]$Ip, [int]$Port = 4370, [string]$Mdb = "D:\Att2008\Att2000.mdb")
$ErrorActionPreference = "Stop"
$zk = New-Object -ComObject zkemkeeper.ZKEM
if (-not $zk.Connect_Net($Ip, $Port)) { "GAGAL tidak tersambung"; return }
"TERSAMBUNG"
$hasil = New-Object System.Collections.ArrayList
try {
    $db = @{}
    $c = New-Object System.Data.OleDb.OleDbConnection("Provider=Microsoft.Jet.OLEDB.4.0;Data Source=$Mdb;Mode=Read")
    $c.Open()
    $cmd = $c.CreateCommand()
    $cmd.CommandText = "select u.Badgenumber, t.FINGERID, t.[TEMPLATE4] from USERINFO as u inner join [TEMPLATE] as t on u.USERID = t.USERID"
    $r = $cmd.ExecuteReader()
    while ($r.Read()) {
        $b = $r[2] -as [byte[]]
        if ($r.IsDBNull(1) -or $null -eq $b -or $b.Length -eq 0) { continue }
        $id = ([string]$r[0]).Trim()
        if (-not $db.ContainsKey($id)) { $db[$id] = @{} }
        $db[$id][[int]$r[1]] = $b
    }
    $c.Close()
    [void]$zk.ReadAllUserID(1)
    [void]$zk.ReadAllTemplate(1)
    foreach ($id in $db.Keys) {
        for ($f = 0; $f -le 9; $f++) {
            [int]$flag = 0; [string]$tmp = ""; [int]$len = 0
            $ok = $zk.GetUserTmpExStr(1, [string]$id, $f, [ref]$flag, [ref]$tmp, [ref]$len)
            if (-not $ok -or $tmp.Length -eq 0) { continue }
            if (-not $db[$id].ContainsKey($f)) { [void]$hasil.Add("hanya di mesin"); continue }
            [byte[]]$m = [Convert]::FromBase64String($tmp.Trim([char]0).Trim())
            [byte[]]$a = $db[$id][$f]
            $min = [Math]::Min($a.Length, $m.Length)
            $p = 0; $jml = 0; $pertama = -1
            for ($p = 0; $p -lt $min; $p++) { if ($a[$p] -ne $m[$p]) { $jml++; if ($pertama -lt 0) { $pertama = $p } } }
            $selisih = $a.Length - $m.Length
            if ($jml -eq 0 -and $selisih -eq 0) { [void]$hasil.Add("SAMA-PERSIS") }
            elseif ($jml -eq 0 -and $selisih -gt 0) {
                $nol = $true
                for ($i = $min; $i -lt $a.Length; $i++) { if ($a[$i] -ne 0) { $nol = $false } }
                [void]$hasil.Add("mesin = awalan mdb; ekor $selisih byte; ekor nol semua=$nol")
            } else {
                [void]$hasil.Add("ISI-BEDA; selisih panjang $selisih byte")
                if (@($hasil | Where-Object { $_ -like "ISI-BEDA*" }).Count -le 8) {
                    "contoh beda: panjang mdb $($a.Length), mesin $($m.Length), beda pertama di byte $pertama, byte beda $jml dari $min"
                }
            }
        }
    }
} finally { $zk.Disconnect() }
""
"Jumlah jari dibaca dari mesin: " + $hasil.Count
$hasil | Group-Object | Sort-Object Count -Descending | ForEach-Object { "{0,5}  {1}" -f $_.Count, $_.Name }
