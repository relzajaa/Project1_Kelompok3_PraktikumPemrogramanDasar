# Berisi pengelola data (manager): menyimpan data, memeriksa aturan, dan mengubah data.
from .models import KondisiAlat, Mahasiswa, StatusAlat, StatusTransaksi, Transaksi


# Mengelola data mahasiswa. Disimpan dalam dictionary dengan kunci NIM.
class MahasiswaManager:
    # Siapkan tempat penyimpanan yang masih kosong.
    def __init__(self):
        self._data = {}

    # Periksa nama dan nomor HP; error jika tidak sesuai.
    def _periksa(self, nama, noHp):
        if not nama:
            raise ValueError("Nama mahasiswa wajib diisi.")
        if not noHp.isdigit() or not Mahasiswa.MIN_HP <= len(noHp) <= Mahasiswa.MAX_HP:
            raise ValueError(
                f"No. HP wajib diisi, hanya berisi angka, {Mahasiswa.MIN_HP} sampai {Mahasiswa.MAX_HP} digit."
            )

    # Tambah mahasiswa baru (NIM tidak boleh sama).
    def tambah(self, nim, nama, noHp):
        nim, nama, noHp = nim.strip(), nama.strip(), noHp.strip()
        if not nim:
            raise ValueError("NIM wajib diisi.")
        if nim in self._data:
            raise ValueError(f"NIM {nim} sudah terdaftar.")
        self._periksa(nama, noHp)
        self._data[nim] = Mahasiswa(nim, nama, noHp)

    # Ubah nama / no. HP. Isian kosong berarti tidak diubah.
    def edit(self, nim, nama="", noHp=""):
        mhs = self.ambil(nim)
        nama = nama.strip() or mhs.nama
        noHp = noHp.strip() or mhs.noHp
        self._periksa(nama, noHp)
        mhs.nama = nama
        mhs.noHp = noHp

    # Hapus mahasiswa (ditolak jika masih punya transaksi aktif).
    def hapus(self, nim):
        mhs = self.ambil(nim)
        if mhs.statusAktif:
            raise ValueError(f"{mhs.nama} tidak dapat dihapus karena masih memiliki transaksi aktif.")
        del self._data[nim]

    # Cari mahasiswa dari sebagian NIM atau nama.
    def cari(self, kata):
        kata = kata.lower()
        return [m for m in self._data.values() if kata in m.nim.lower() or kata in m.nama.lower()]

    # Ambil satu mahasiswa berdasarkan NIM (error jika tidak ada).
    def ambil(self, nim):
        if nim not in self._data:
            raise ValueError(f"Mahasiswa dengan NIM {nim} tidak ditemukan.")
        return self._data[nim]

    # Semua mahasiswa.
    def semua(self):
        return list(self._data.values())


# Mengelola data alat. Disimpan dalam dictionary dengan kunci kode alat.
class AlatManager:
    # Siapkan tempat penyimpanan alat dan daftar kategori yang masih kosong.
    def __init__(self):
        self._data = {}
        self.kategori = set()  # kategori yang sudah ada (tanpa duplikat)

    # Tambah alat baru (kode tidak boleh sama).
    def tambah(self, alat):
        alat.kode = alat.kode.strip()
        alat.nama = alat.nama.strip()
        alat.kategori = alat.kategori.strip().title()
        if not (alat.kode and alat.nama and alat.kategori):
            raise ValueError("Kode, nama, dan kategori alat wajib diisi.")
        if alat.kode in self._data:
            raise ValueError(f"Kode alat {alat.kode} sudah terdaftar.")
        self._data[alat.kode] = alat
        self.kategori.add(alat.kategori)

    # Ubah nama / kategori alat. Isian kosong berarti tidak diubah.
    def edit(self, kode, nama="", kategori=""):
        alat = self.ambil(kode)
        alat.nama = nama.strip() or alat.nama
        alat.kategori = kategori.strip().title() or alat.kategori
        self.kategori.add(alat.kategori)

    # Hapus alat (ditolak jika sedang ada di transaksi aktif).
    def hapus(self, kode):
        alat = self.ambil(kode)
        if alat.dalamTrxAktif():
            raise ValueError(f"Alat {kode} tidak dapat dihapus karena sedang dalam transaksi aktif.")
        del self._data[kode]

    # Cari alat dari sebagian kode, nama, atau kategori.
    def cari(self, kriteria, kata):
        if kriteria not in ("kode", "nama", "kategori"):
            raise ValueError("Kriteria pencarian harus kode, nama, atau kategori.")
        kata = kata.lower()
        # getattr(alat, "nama") sama dengan alat.nama; di sini nama atribut mengikuti kriteria
        return [a for a in self._data.values() if kata in getattr(a, kriteria).lower()]

    # Ambil satu alat berdasarkan kode (error jika tidak ada).
    def ambil(self, kode):
        if kode not in self._data:
            raise ValueError(f"Alat dengan kode {kode} tidak ditemukan.")
        return self._data[kode]

    # Semua alat.
    def semua(self):
        return list(self._data.values())

    # Tambah kategori baru.
    def tambahKategori(self, nama):
        nama = nama.strip().title()
        if not nama:
            raise ValueError("Nama kategori wajib diisi.")
        if nama in self.kategori:
            raise ValueError(f"Kategori {nama} sudah ada.")
        self.kategori.add(nama)

    # Alat dengan status tertentu.
    def filterStatus(self, status):
        return [a for a in self._data.values() if a.status == status]

    # Alat yang kondisinya tidak baik.
    def alatRusak(self):
        return [a for a in self._data.values() if a.kondisi != KondisiAlat.BAIK]

    # Jumlah alat yang tersedia (stok).
    def jumlahTersedia(self):
        return len(self.filterStatus(StatusAlat.TERSEDIA))

    # Masukkan alat ke pemeliharaan.
    def masukPemeliharaan(self, kode):
        self.ambil(kode).masukPemeliharaan()

    # Selesaikan pemeliharaan alat.
    def selesaiPemeliharaan(self, kode):
        self.ambil(kode).selesaiPemeliharaan()

    # Alat yang sedang dalam pemeliharaan.
    def daftarPemeliharaan(self):
        return self.filterStatus(StatusAlat.PEMELIHARAAN)


# Mengelola transaksi peminjaman. Disimpan dalam dictionary dengan kunci ID transaksi.
class TransaksiManager:
    # Siapkan penyimpanan transaksi; manager mahasiswa dan alat dipakai untuk memeriksa data.
    def __init__(self, mgrMahasiswa, mgrAlat):
        self._data = {}
        self._counter = 0  # nomor urut untuk membuat ID transaksi
        self._mgrMahasiswa = mgrMahasiswa
        self._mgrAlat = mgrAlat

    # Buat transaksi baru setelah semua aturan peminjaman dipenuhi.
    def buat(self, nim, listKode, hari=Transaksi.MAKS_HARI):
        mahasiswa = self._mgrMahasiswa.ambil(nim)
        if not mahasiswa.bolehPinjam():
            raise ValueError(
                f"{mahasiswa.nama} sudah memiliki {Mahasiswa.MAKS_TRX_AKTIF} transaksi aktif (batas maksimum)."
            )
        if not listKode:
            raise ValueError("Pilih minimal satu alat untuk dipinjam.")

        daftarAlat = []
        for kode in listKode:
            alat = self._mgrAlat.ambil(kode)
            if alat not in daftarAlat:  # kode yang diketik dua kali dihitung sekali
                daftarAlat.append(alat)
        for alat in daftarAlat:
            if not alat.tersedia():
                raise ValueError(f"Alat {alat.kode} ({alat.nama}) tidak tersedia, status: {alat.status.value}.")
        if not 1 <= hari <= Transaksi.MAKS_HARI:
            raise ValueError(f"Lama pinjam harus 1 sampai {Transaksi.MAKS_HARI} hari.")

        self._counter += 1
        trx = Transaksi(f"TRX{self._counter:03d}", mahasiswa, hari)  # TRX001, TRX002, ...
        for alat in daftarAlat:
            trx.tambahAlat(alat)
        self._data[trx.id] = trx
        mahasiswa.tambahTrx(trx.id)
        return trx

    # Proses pengembalian satu alat dalam sebuah transaksi.
    def kembalikan(self, idTrx, kode, kondisi, tgl):
        if idTrx not in self._data:
            raise ValueError(f"Transaksi {idTrx} tidak ditemukan.")
        trx = self._data[idTrx]
        trx.kembalikanAlat(kode, kondisi, tgl)
        if not trx.aktif():  # semua alat sudah kembali
            trx.mahasiswa.selesaiTrx(idTrx)

    # Semua transaksi.
    def semua(self):
        return list(self._data.values())

    # Semua transaksi milik satu mahasiswa.
    def cariByMahasiswa(self, nim):
        self._mgrMahasiswa.ambil(nim)  # pastikan NIM terdaftar
        return [t for t in self._data.values() if t.mahasiswa.nim == nim]

    # Transaksi mahasiswa yang sudah selesai, yang terbaru di atas.
    def riwayat(self, nim):
        selesai = [t for t in self.cariByMahasiswa(nim) if not t.aktif()]
        return sorted(selesai, key=lambda t: t.tglPinjam, reverse=True)

    # Urutkan hitungan {nama: jumlah} dari yang terbanyak menjadi daftar pasangan (nama, jumlah).
    def _urutkan(self, hitung):
        return sorted(hitung.items(), key=lambda pasangan: pasangan[1], reverse=True)

    # Alat yang paling sering dipinjam.
    def alatTerpopuler(self):
        hitung = {}
        for trx in self._data.values():
            for detail in trx.daftarDetail:
                nama = detail.alat.nama
                hitung[nama] = hitung.get(nama, 0) + 1
        return self._urutkan(hitung)

    # Mahasiswa yang paling sering meminjam.
    def mahasiswaTerAktif(self):
        hitung = {}
        for trx in self._data.values():
            label = f"{trx.mahasiswa.nama} ({trx.mahasiswa.nim})"
            hitung[label] = hitung.get(label, 0) + 1
        return self._urutkan(hitung)

    # Jumlah transaksi yang sudah selesai.
    def jumlahSelesai(self):
        return len([t for t in self._data.values() if t.status == StatusTransaksi.SELESAI])

    # Jumlah transaksi yang masih aktif.
    def jumlahAktif(self):
        return len([t for t in self._data.values() if t.aktif()])

    # Kumpulan data statistik untuk ditampilkan.
    def statistik(self):
        return {
            "alatTerpopuler": self.alatTerpopuler(),
            "mahasiswaTerAktif": self.mahasiswaTerAktif(),
            "jumlahSelesai": self.jumlahSelesai(),
            "jumlahAktif": self.jumlahAktif(),
        }
