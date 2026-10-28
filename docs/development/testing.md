# Testing

Unit test per modul belum ditulis; folder `tests/` per modul sudah ada. Sementara itu pengujian dilakukan manual di bench kerja (lihat catatan di bawah). Uji bridge ke ERPNext menunggu bridge ada.

## Pola uji manual di `bench console`
1. Tulis skrip uji ke file sementara (`/tmp/uji_*.py`) lewat heredoc.
2. Jalankan lewat satu baris di console:

   ```bash
   bench --site <nama> console <<'EOF'
   exec(open("/tmp/uji_x.py").read(), {"frappe": frappe})
   EOF
   ```

3. Akhiri skrip dengan `frappe.db.rollback()` di blok `finally` agar tidak ada data tersisa; cetak hasil dengan `print()`.
4. Hapus file sementara setelahnya.

## Catatan teknis
- Blok bertingkat (`try`, `for`, `def`) yang diketik langsung di heredoc console tidak dieksekusi tanpa baris kosong; karena itu dipakai `exec` dari file.
- `exec` harus memakai satu ruang nama (`{"frappe": frappe}`); tanpa itu fungsi di dalam skrip tidak melihat variabel global skrip.
- Skrip heredoc memakai spasi, bukan tab: tab hilang saat ditempel ke terminal.
- `mandatory_depends_on` hanya berlaku di browser. Aturan wajib bersyarat harus ditulis juga di controller.
- Field wajib yang diisi otomatis oleh controller harus punya `fetch_from` atau default agar form tidak menolak simpan di browser.
- Uji lewat skrip tidak menggantikan uji form di browser (validasi sisi klien, tab, penguncian, warna).
- Setelah mengubah JS DocType: hard refresh browser (Ctrl+Shift+R).

## Daftar uji yang sudah dijalankan (28 Okt 2026)
| Objek | Uji |
|---|---|
| HRIS Device | Serial wajib dan unik; mode Pull wajib IP dan port; IP tidak valid ditolak; mode ADMS tanpa IP diterima |
| HRIS Raw Log | Insert; duplikat ditolak; ubah tanpa alasan ditolak; ubah dengan alasan; Version tercatat |
| Audit trail | API mengembalikan perubahan dan baris "dokumen dibuat"; DocType non-HRIS ditolak |
| UI | Simpan Raw Log, alasan wajib, tab audit, status Disetujui, warna list view |

## Belum diuji
Pencocokan Employee nyata, pengguna non-editor, status Terkirim terkunci, uji beban data besar.
