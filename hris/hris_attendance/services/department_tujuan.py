"""K-138: penentuan Department yang dipakai aturan hitung pada satu hari (fungsi murni)."""


def tentukan_department(dept_karyawan, pinjam_dept=None, pinjam_grup_dept=None, ikut="Department"):
    """Mengembalikan (department, sumber).

    Urutan: peminjaman ke Department, peminjaman ke Grup (Department milik Grup), lalu
    Department karyawan. Bila Department dan Grup peminjaman sama-sama terisi dan berbeda,
    pilihan 'Ikut' di HRIS Employee menentukan (bawaan Department).
    """
    if pinjam_dept and pinjam_grup_dept and pinjam_dept != pinjam_grup_dept:
        if ikut == "Grup":
            return pinjam_grup_dept, "Peminjaman Grup"
        return pinjam_dept, "Peminjaman Department"
    if pinjam_dept:
        return pinjam_dept, "Peminjaman Department"
    if pinjam_grup_dept:
        return pinjam_grup_dept, "Peminjaman Grup"
    return dept_karyawan, "Department Karyawan"
