# Tampilan menu program: membaca pilihan pengguna lalu meneruskannya ke manager.
from datetime import date, datetime

from . import tampilan as ui
from .managers import AlatManager, MahasiswaManager, TransaksiManager
from .models import KondisiAlat, Mahasiswa, StatusAlat, Transaksi

FORMAT_TANGGAL = "%d-%m-%Y"
JUMLAH_TOP = 5          # jumlah baris pada tabel statistik
JUMLAH_MENU_UTAMA = 11  # menu 1-11 masuk menu utama, sisanya menu tantangan


# ---------- fungsi membantu tampilan ----------

# Ubah tanggal menjadi teks, contoh: 25-12-2026.
def _fmt(tgl):
    return tgl.strftime(FORMAT_TANGGAL)


# Status transaksi; ditambah "TERLAMBAT" bila masih aktif dan sudah lewat batas.
def _labelStatus(trx):
    status = trx.status.value
    if trx.aktif() and trx.terlambat(date.today()):
        status += " - TERLAMBAT"
    return status


# Tampilkan tabel mahasiswa.
def _tampilMahasiswa(daftar):
    baris = []
    for mhs in daftar:
        status = "Meminjam" if mhs.statusAktif else "-"
        baris.append([mhs.nim, mhs.nama, mhs.noHp, f"{mhs.jumlahAktif()}/{Mahasiswa.MAKS_TRX_AKTIF}", status])
    ui.tabel(["NIM", "Nama", "No. HP", "Trx Aktif", "Status"], baris)


# Tampilkan tabel alat.
def _tampilAlat(daftar):
    baris = []
    for alat in daftar:
        baris.append([alat.kode, alat.nama, alat.kategori, alat.kondisi.value, alat.status.value, alat.trxAktif or "-"])
    ui.tabel(["Kode", "Nama", "Kategori", "Kondisi", "Status", "Trx Aktif"], baris)


# Tampilkan tabel ringkasan transaksi.
def _tampilTransaksi(daftar):
    baris = []
    for trx in daftar:
        jumlahAlat = f"{len(trx.daftarAlat())} alat, {len(trx.alatBelumKembali())} belum kembali"
        baris.append([trx.id, trx.mahasiswa.nama, _fmt(trx.tglPinjam), _fmt(trx.batasKembali), jumlahAlat, _labelStatus(trx)])
    ui.tabel(["ID", "Mahasiswa", "Tgl Pinjam", "Batas", "Alat", "Status"], baris)


# Tampilkan detail satu transaksi beserta alat-alatnya.
def _tampilDetail(trx):
    ui.kotak(f"TRANSAKSI {trx.id}", [
        f"Mahasiswa      : {trx.mahasiswa.nama} ({trx.mahasiswa.nim})",
        f"Tanggal pinjam : {_fmt(trx.tglPinjam)}",
        f"Batas kembali  : {_fmt(trx.batasKembali)}",
        f"Status         : {_labelStatus(trx)}",
    ])
    baris = []
    for detail in trx.daftarDetail:
        if detail.isKembali():
            baris.append([detail.alat.kode, detail.alat.nama, _fmt(detail.tglKembali), detail.kondisiKembali.value, f"{detail.hariTerlambat} hari"])
        else:
            baris.append([detail.alat.kode, detail.alat.nama, "Belum", "-", "-"])
    ui.tabel(["Kode", "Alat", "Kembali", "Kondisi", "Terlambat"], baris)


# Cari transaksi dengan ID tertentu di dalam daftar.
def _pilihTransaksi(daftar, idTrx):
    for trx in daftar:
        if trx.id == idTrx.upper():
            return trx
    raise ValueError("ID transaksi tidak ada dalam daftar di atas.")


# Tampilkan daftar transaksi, lalu tawarkan melihat detail salah satunya.
def _tampilTransaksiDanDetail(daftar):
    _tampilTransaksi(daftar)
    if daftar:
        idTrx = ui.tanya("Ketik ID transaksi untuk melihat detail (Enter = lewati)")
        if idTrx:
            _tampilDetail(_pilihTransaksi(daftar, idTrx))


# Tampilkan pilihan dari sebuah Enum bernomor, lalu kembalikan pilihan pengguna.
def _pilihEnum(kelas, pertanyaan):
    pilihan = list(kelas)
    ui.kotak("", [f"{nomor}. {opsi.value}" for nomor, opsi in enumerate(pilihan, 1)])
    nomor = ui.tanya(pertanyaan)
    if not nomor.isdigit() or not 1 <= int(nomor) <= len(pilihan):
        raise ValueError("Pilihan tidak valid.")
    return pilihan[int(nomor) - 1]


# Minta tanggal kembali; Enter berarti hari ini.
def _inputTanggal():
    teks = ui.tanya("Tanggal kembali (DD-MM-YYYY, Enter = hari ini)")
    if not teks:
        return date.today()
    try:
        return datetime.strptime(teks, FORMAT_TANGGAL).date()
    except ValueError:
        raise ValueError("Format tanggal harus DD-MM-YYYY, contoh 25-12-2026.")


# Tanya ya/tidak; hasilnya True jika pengguna mengetik y.
def _konfirmasi(pertanyaan):
    return ui.tanya(f"{pertanyaan} (y/n)").lower() == "y"


# Tampilkan tabel peringkat (alat terpopuler / mahasiswa teraktif).
def _tampilPeringkat(judul, kolom, daftar):
    ui.subjudul(f"{judul} (top {JUMLAH_TOP})")
    baris = []
    for urutan, (nama, jumlah) in enumerate(daftar[:JUMLAH_TOP], 1):
        baris.append([urutan, nama, f"{jumlah}x"])
    ui.tabel(["No"] + kolom, baris)


# ---------- kelas utama ----------

# Kelas utama program: menampilkan menu dan menjalankan pilihan pengguna.
class MenuApp:
    # Siapkan manager dan daftar menu. Isi menu: nomor -> (nama, fungsi, perlu jeda "Tekan Enter").
    def __init__(self):
        self.mgrMahasiswa = MahasiswaManager()
        self.mgrAlat = AlatManager()
        self.mgrTransaksi = TransaksiManager(self.mgrMahasiswa, self.mgrAlat)
        self._berjalan = True
        self._menu = {
            1: ("Kelola Data Mahasiswa", self._menuMahasiswa, False),
            2: ("Kelola Data Alat", self._menuAlat, False),
            3: ("Buat Transaksi Peminjaman", self._pinjamAlat, True),
            4: ("Tampilkan Transaksi", self._daftarTransaksi, True),
            5: ("Proses Pengembalian Alat", self._kembalikanAlat, True),
            6: ("Cari Transaksi Berdasarkan Mahasiswa", self._cariTransaksiMahasiswa, True),
            7: ("Tampilkan Alat yang Tersedia", self._alatTersedia, True),
            8: ("Tampilkan Alat yang Sedang Dipinjam", self._alatDipinjam, True),
            9: ("Tampilkan Alat yang Rusak", self._alatRusak, True),
            10: ("Tampilkan Riwayat Peminjaman Mahasiswa", self._riwayatMahasiswa, True),
            11: ("Keluar dari Program", self.keluar, False),
            12: ("Pencarian Alat", self._cariAlat, True),
            13: ("Statistik Peminjaman", self._statistik, True),
            14: ("Pemeliharaan Alat", self._menuPemeliharaan, False),
        }

    # Jalankan program: tampilkan menu berulang kali sampai pengguna keluar.
    def jalankan(self):
        try:
            while self._berjalan:
                self.tampilkanMenu()
                self.prosesPilihan(ui.tanya(f"Pilih menu (1-{len(self._menu)})"))
        except (KeyboardInterrupt, EOFError):  # Ctrl+C / Ctrl+D
            self.keluar()

    # Tampilkan judul utama, menu utama, dan menu tantangan.
    def tampilkanMenu(self):
        ui.judulHalaman("SISTEM PEMINJAMAN PERALATAN LABORATORIUM", utama=True)
        ui.tengah(f"Hari ini: {_fmt(date.today())}   |   Transaksi aktif: {self.mgrTransaksi.jumlahAktif()}")
        print()
        ui.kotak("MENU UTAMA", [f"{nomor:>2}. {menu[0]}" for nomor, menu in self._menu.items() if nomor <= JUMLAH_MENU_UTAMA])
        ui.kotak("MENU TANTANGAN", [f"{nomor:>2}. {menu[0]}" for nomor, menu in self._menu.items() if nomor > JUMLAH_MENU_UTAMA])

    # Jalankan menu sesuai nomor yang dipilih.
    def prosesPilihan(self, pilihan):
        if not pilihan.isdigit() or int(pilihan) not in self._menu:
            ui.pesan(f"Pilihan tidak valid. Masukkan angka 1 sampai {len(self._menu)}.", "error")
            ui.tekanEnter()
            return
        label, aksi, pakaiJeda = self._menu[int(pilihan)]
        if pakaiJeda:
            self._eksekusi(label, aksi)
        else:
            aksi()

    # Hentikan program dan tampilkan salam perpisahan.
    def keluar(self):
        self._berjalan = False
        ui.bersihkan()
        print("\n")
        ui.pesan("Terima kasih telah menggunakan sistem peminjaman lab. Sampai jumpa!", "sukses")

    # Tampilkan judul halaman, jalankan aksi, tampilkan pesan jika terjadi kesalahan, lalu beri jeda.
    def _eksekusi(self, judul, aksi):
        ui.judulHalaman(judul.upper())
        try:
            aksi()
        except ValueError as e:
            ui.pesan(str(e), "error")
        ui.tekanEnter()

    # Tampilkan submenu berulang kali sampai pengguna memilih 0 (kembali).
    # `daftarAksi` berisi pasangan (nama menu, fungsi).
    def _submenu(self, judul, daftarAksi):
        while True:
            ui.judulHalaman(judul)
            teksMenu = [f"{nomor}. {item[0]}" for nomor, item in enumerate(daftarAksi, 1)]
            ui.kotak("", teksMenu + ["0. Kembali ke menu utama"])
            pilihan = ui.tanya("Pilih")
            if pilihan == "0":
                return
            if pilihan.isdigit() and 1 <= int(pilihan) <= len(daftarAksi):
                label, aksi = daftarAksi[int(pilihan) - 1]
                self._eksekusi(label, aksi)
            else:
                ui.pesan("Pilihan tidak valid.", "error")
                ui.tekanEnter()

    # ---------- menu 1: mahasiswa ----------

    # Submenu kelola data mahasiswa.
    def _menuMahasiswa(self):
        self._submenu("KELOLA DATA MAHASISWA", [
            ("Tambah mahasiswa", self._tambahMahasiswa),
            ("Edit mahasiswa", self._editMahasiswa),
            ("Hapus mahasiswa", self._hapusMahasiswa),
            ("Cari mahasiswa", self._cariMahasiswa),
            ("Daftar mahasiswa", self._daftarMahasiswa),
        ])

    # Tambah mahasiswa baru.
    def _tambahMahasiswa(self):
        nim = ui.tanya("NIM")
        nama = ui.tanya("Nama")
        noHp = ui.tanya(f"No. HP ({Mahasiswa.MIN_HP}-{Mahasiswa.MAX_HP} digit)")
        self.mgrMahasiswa.tambah(nim, nama, noHp)
        ui.pesan("Mahasiswa berhasil ditambahkan.", "sukses")

    # Ubah data mahasiswa.
    def _editMahasiswa(self):
        mhs = self.mgrMahasiswa.ambil(ui.tanya("NIM mahasiswa yang diedit"))
        _tampilMahasiswa([mhs])
        ui.pesan("Kosongkan isian (Enter) bila tidak ingin mengubah.")
        nama = ui.tanya("Nama baru")
        noHp = ui.tanya(f"No. HP baru ({Mahasiswa.MIN_HP}-{Mahasiswa.MAX_HP} digit)")
        if not nama and not noHp:
            ui.pesan("Tidak ada perubahan.")
            return
        self.mgrMahasiswa.edit(mhs.nim, nama, noHp)
        ui.pesan("Data mahasiswa berhasil diubah.", "sukses")

    # Hapus mahasiswa setelah dikonfirmasi.
    def _hapusMahasiswa(self):
        mhs = self.mgrMahasiswa.ambil(ui.tanya("NIM mahasiswa yang dihapus"))
        _tampilMahasiswa([mhs])
        if _konfirmasi(f"Hapus {mhs.nama}?"):
            self.mgrMahasiswa.hapus(mhs.nim)
            ui.pesan("Mahasiswa berhasil dihapus.", "sukses")
        else:
            ui.pesan("Penghapusan dibatalkan.")

    # Cari mahasiswa berdasarkan NIM atau nama.
    def _cariMahasiswa(self):
        _tampilMahasiswa(self.mgrMahasiswa.cari(ui.tanya("Kata kunci (NIM / nama)")))

    # Tampilkan semua mahasiswa.
    def _daftarMahasiswa(self):
        _tampilMahasiswa(self.mgrMahasiswa.semua())

    # ---------- menu 2: alat ----------

    # Submenu kelola data alat.
    def _menuAlat(self):
        self._submenu("KELOLA DATA ALAT", [
            ("Tambah alat", self._tambahAlat),
            ("Edit alat", self._editAlat),
            ("Hapus alat", self._hapusAlat),
            ("Cari alat", self._cariAlatNama),
            ("Daftar alat", self._daftarAlat),
            ("Tambah kategori", self._tambahKategori),
        ])

    # Tambah alat baru, boleh langsung banyak unit sekaligus.
    def _tambahAlat(self):
        if self.mgrAlat.kategori:
            ui.pesan("Kategori yang ada: " + ", ".join(sorted(self.mgrAlat.kategori)))
        ui.pesan(f"Jika jumlah lebih dari 1, kode dibuat otomatis (KODE-01, KODE-02, ...), maks {AlatManager.MAKS_TAMBAH} unit.")
        kode = ui.tanya("Kode alat (jika banyak, dipakai sebagai awalan)").upper()
        nama = ui.tanya("Nama alat")
        kategori = ui.tanya("Kategori")
        teksJumlah = ui.tanya("Jumlah unit (Enter = 1)")
        if teksJumlah and not teksJumlah.isdigit():
            raise ValueError("Jumlah unit harus berupa angka bulat.")
        jumlah = int(teksJumlah) if teksJumlah else 1

        alatBaru = self.mgrAlat.tambahBanyak(kode, nama, kategori, jumlah)
        if len(alatBaru) == 1:
            ui.pesan("Alat berhasil ditambahkan.", "sukses")
        else:
            ui.pesan(f"{len(alatBaru)} unit alat berhasil ditambahkan: {alatBaru[0].kode} s/d {alatBaru[-1].kode}.", "sukses")
        ui.pesan(f"Total stok tersedia sekarang: {self.mgrAlat.jumlahTersedia()} unit")

    # Ubah data alat.
    def _editAlat(self):
        alat = self.mgrAlat.ambil(ui.tanya("Kode alat yang diedit").upper())
        _tampilAlat([alat])
        ui.pesan("Kosongkan isian (Enter) bila tidak ingin mengubah.")
        nama = ui.tanya("Nama baru")
        kategori = ui.tanya("Kategori baru")
        if not nama and not kategori:
            ui.pesan("Tidak ada perubahan.")
            return
        self.mgrAlat.edit(alat.kode, nama, kategori)
        ui.pesan("Data alat berhasil diubah.", "sukses")

    # Hapus alat setelah dikonfirmasi.
    def _hapusAlat(self):
        alat = self.mgrAlat.ambil(ui.tanya("Kode alat yang dihapus").upper())
        _tampilAlat([alat])
        if _konfirmasi(f"Hapus {alat.nama}?"):
            self.mgrAlat.hapus(alat.kode)
            ui.pesan("Alat berhasil dihapus.", "sukses")
        else:
            ui.pesan("Penghapusan dibatalkan.")

    # Cari alat berdasarkan nama.
    def _cariAlatNama(self):
        _tampilAlat(self.mgrAlat.cari("nama", ui.tanya("Nama alat")))

    # Tampilkan semua alat.
    def _daftarAlat(self):
        _tampilAlat(self.mgrAlat.semua())

    # Tambah kategori baru.
    def _tambahKategori(self):
        self.mgrAlat.tambahKategori(ui.tanya("Nama kategori baru"))
        ui.pesan("Kategori sekarang: " + ", ".join(sorted(self.mgrAlat.kategori)), "sukses")

    # ---------- menu 3: buat transaksi peminjaman ----------

    # Buat transaksi: pilih mahasiswa, alat (boleh lebih dari satu), dan lama pinjam.
    def _pinjamAlat(self):
        mhs = self.mgrMahasiswa.ambil(ui.tanya("NIM mahasiswa"))
        ui.pesan(f"{mhs.nama} - transaksi aktif {mhs.jumlahAktif()}/{Mahasiswa.MAKS_TRX_AKTIF}")
        ui.subjudul("Alat yang tersedia")
        _tampilAlat(self.mgrAlat.filterStatus(StatusAlat.TERSEDIA))

        listKode = []
        for kode in ui.tanya("Kode alat (pisahkan dengan koma)").split(","):
            if kode.strip():
                listKode.append(kode.strip().upper())

        teksHari = ui.tanya(f"Lama pinjam dalam hari (maks {Transaksi.MAKS_HARI}, Enter = {Transaksi.MAKS_HARI})")
        if teksHari and not teksHari.isdigit():
            raise ValueError("Lama pinjam harus berupa angka.")
        hari = int(teksHari) if teksHari else Transaksi.MAKS_HARI

        trx = self.mgrTransaksi.buat(mhs.nim, listKode, hari)
        print()
        ui.pesan("Peminjaman berhasil dicatat.", "sukses")
        _tampilDetail(trx)

    # ---------- menu 4 dan 6: tampilkan / cari transaksi ----------

    # Tampilkan semua transaksi.
    def _daftarTransaksi(self):
        _tampilTransaksiDanDetail(self.mgrTransaksi.semua())

    # Tampilkan transaksi milik satu mahasiswa.
    def _cariTransaksiMahasiswa(self):
        _tampilTransaksiDanDetail(self.mgrTransaksi.cariByMahasiswa(ui.tanya("NIM mahasiswa")))

    # ---------- menu 5: proses pengembalian ----------

    # Kembalikan satu alat: pilih mahasiswa, transaksi, alat, kondisi, dan tanggal.
    def _kembalikanAlat(self):
        nim = ui.tanya("NIM mahasiswa")
        aktif = [trx for trx in self.mgrTransaksi.cariByMahasiswa(nim) if trx.aktif()]
        if not aktif:
            raise ValueError("Mahasiswa ini tidak memiliki transaksi aktif.")
        _tampilTransaksi(aktif)

        trx = _pilihTransaksi(aktif, ui.tanya("ID transaksi"))
        _tampilDetail(trx)

        kode = ui.tanya("Kode alat yang dikembalikan").upper()
        kondisi = _pilihEnum(KondisiAlat, "Kondisi alat saat dikembalikan")
        tgl = _inputTanggal()

        self.mgrTransaksi.kembalikan(trx.id, kode, kondisi, tgl)
        print()
        ui.pesan(f"Alat {kode} berhasil dikembalikan.", "sukses")
        for detail in trx.daftarDetail:
            if detail.alat.kode == kode and detail.hariTerlambat > 0:
                ui.pesan(f"Terlambat {detail.hariTerlambat} hari dari batas pengembalian.")
        _tampilDetail(trx)

    # ---------- menu 7-9: tampilkan alat ----------

    # Tampilkan alat yang tersedia beserta jumlah stoknya.
    def _alatTersedia(self):
        _tampilAlat(self.mgrAlat.filterStatus(StatusAlat.TERSEDIA))
        ui.pesan(f"Total stok tersedia: {self.mgrAlat.jumlahTersedia()} unit")

    # Tampilkan alat yang sedang dipinjam.
    def _alatDipinjam(self):
        _tampilAlat(self.mgrAlat.filterStatus(StatusAlat.DIPINJAM))

    # Tampilkan alat yang rusak.
    def _alatRusak(self):
        _tampilAlat(self.mgrAlat.alatRusak())

    # ---------- menu 10: riwayat ----------

    # Tampilkan transaksi mahasiswa yang sudah selesai.
    def _riwayatMahasiswa(self):
        daftar = self.mgrTransaksi.riwayat(ui.tanya("NIM mahasiswa"))
        if not daftar:
            ui.pesan("Belum ada riwayat transaksi yang selesai.")
        for trx in daftar:
            _tampilDetail(trx)

    # ---------- menu 12: pencarian alat (tantangan A) ----------

    # Cari alat berdasarkan kode, nama, atau kategori.
    def _cariAlat(self):
        pilihan = ui.tanya("Cari berdasarkan (1 = Kode, 2 = Nama, 3 = Kategori)")
        kriteria = {"1": "kode", "2": "nama", "3": "kategori"}.get(pilihan)
        if kriteria is None:
            raise ValueError("Pilihan tidak valid.")
        _tampilAlat(self.mgrAlat.cari(kriteria, ui.tanya("Kata kunci")))

    # ---------- menu 13: statistik (tantangan B) ----------

    # Tampilkan ringkasan transaksi, alat terpopuler, dan mahasiswa teraktif.
    def _statistik(self):
        stat = self.mgrTransaksi.statistik()
        ui.kotak("RINGKASAN TRANSAKSI", [
            f"Transaksi aktif   : {stat['jumlahAktif']}",
            f"Transaksi selesai : {stat['jumlahSelesai']}",
        ])
        _tampilPeringkat("Alat Terpopuler", ["Alat", "Dipinjam"], stat["alatTerpopuler"])
        _tampilPeringkat("Mahasiswa Teraktif", ["Mahasiswa", "Transaksi"], stat["mahasiswaTerAktif"])

    # ---------- menu 14: pemeliharaan (tantangan C) ----------

    # Submenu pemeliharaan alat.
    def _menuPemeliharaan(self):
        self._submenu("PEMELIHARAAN ALAT", [
            ("Masukkan alat ke pemeliharaan", self._masukPemeliharaan),
            ("Selesaikan pemeliharaan alat", self._selesaiPemeliharaan),
            ("Daftar alat dalam pemeliharaan", self._daftarPemeliharaan),
        ])

    # Masukkan alat ke pemeliharaan.
    def _masukPemeliharaan(self):
        self.mgrAlat.masukPemeliharaan(ui.tanya("Kode alat").upper())
        ui.pesan("Alat dimasukkan ke pemeliharaan.", "sukses")

    # Selesaikan pemeliharaan; alat kembali tersedia dalam kondisi baik.
    def _selesaiPemeliharaan(self):
        self.mgrAlat.selesaiPemeliharaan(ui.tanya("Kode alat").upper())
        ui.pesan("Pemeliharaan selesai, alat kembali tersedia dalam kondisi baik.", "sukses")

    # Tampilkan alat yang sedang dipelihara.
    def _daftarPemeliharaan(self):
        _tampilAlat(self.mgrAlat.daftarPemeliharaan())