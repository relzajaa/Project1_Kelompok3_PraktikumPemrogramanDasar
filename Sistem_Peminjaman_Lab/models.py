from datetime import date, timedelta
from enum import Enum


class StatusTransaksi(Enum):
    DIPINJAM = "Dipinjam"
    SEBAGIAN_DIKEMBALIKAN = "Sebagian dikembalikan"
    SELESAI = "Selesai"


class KondisiAlat(Enum):
    BAIK = "Baik"
    RUSAK_RINGAN = "Rusak ringan"
    RUSAK_BERAT = "Rusak berat"


class StatusAlat(Enum):
    TERSEDIA = "Tersedia"
    DIPINJAM = "Dipinjam"
    TIDAK_TERSEDIA = "Tidak tersedia"
    PEMELIHARAAN = "Pemeliharaan"


class Mahasiswa:
    MAKS_TRX_AKTIF = 2  
    MIN_HP = 10         
    MAX_HP = 13         

    def __init__(self, nim, nama, noHp):
        self.nim = nim
        self.nama = nama
        self.noHp = noHp
        self.trxAktif = set()     
        self.statusAktif = False  

    def jumlahAktif(self):
        return len(self.trxAktif)

    def bolehPinjam(self):
        return self.jumlahAktif() < self.MAKS_TRX_AKTIF

    def tambahTrx(self, idTrx):
        self.trxAktif.add(idTrx)
        self.statusAktif = True

    def selesaiTrx(self, idTrx):
        self.trxAktif.discard(idTrx)
        self.statusAktif = len(self.trxAktif) > 0


class Alat:
    def __init__(self, kode, nama, kategori):
        self.kode = kode
        self.nama = nama
        self.kategori = kategori
        self.kondisi = KondisiAlat.BAIK
        self.status = StatusAlat.TERSEDIA
        self.trxAktif = None  

    def tersedia(self):
        return self.status == StatusAlat.TERSEDIA

    def dalamTrxAktif(self):
        return self.trxAktif is not None
    
    def tandaiDipinjam(self, idTrx):
        self.status = StatusAlat.DIPINJAM
        self.trxAktif = idTrx

    def terimaKembali(self, kondisi):
        self.kondisi = kondisi
        if kondisi == KondisiAlat.BAIK:
            self.status = StatusAlat.TERSEDIA
        else:
            self.status = StatusAlat.TIDAK_TERSEDIA

    def selesaiTrx(self, idTrx):
        if self.trxAktif == idTrx:
            self.trxAktif = None

    def masukPemeliharaan(self):
        if self.status == StatusAlat.DIPINJAM:
            raise ValueError(f"Alat {self.kode} sedang dipinjam, belum bisa dipelihara.")
        if self.status == StatusAlat.PEMELIHARAAN:
            raise ValueError(f"Alat {self.kode} sudah dalam pemeliharaan.")
        if self.kondisi == KondisiAlat.BAIK:
            raise ValueError(f"Alat {self.kode} kondisinya baik, hanya alat rusak yang bisa dipelihara.")
        self.status = StatusAlat.PEMELIHARAAN

    def selesaiPemeliharaan(self):
        if self.status != StatusAlat.PEMELIHARAAN:
            raise ValueError(f"Alat {self.kode} tidak sedang dalam pemeliharaan.")
        self.kondisi = KondisiAlat.BAIK
        self.status = StatusAlat.TERSEDIA


class DetailPeminjaman:
    def __init__(self, alat):
        self.alat = alat
        self.sudahKembali = False
        self.tglKembali = None
        self.kondisiKembali = None
        self.hariTerlambat = 0  

    def prosesKembali(self, kondisi, tgl, batas):
        self.sudahKembali = True
        self.tglKembali = tgl
        self.kondisiKembali = kondisi
        self.hariTerlambat = max(0, (tgl - batas).days)

    def isKembali(self):
        return self.sudahKembali


class Transaksi:
    MAKS_HARI = 7  

    def __init__(self, idTrx, mahasiswa, hari=MAKS_HARI):
        self.id = idTrx
        self.mahasiswa = mahasiswa
        self.daftarDetail = []
        self.tglPinjam = date.today()
        self.batasKembali = self.tglPinjam + timedelta(days=hari)
        self.status = StatusTransaksi.DIPINJAM

    def tambahAlat(self, alat):
        self.daftarDetail.append(DetailPeminjaman(alat))
        alat.tandaiDipinjam(self.id)

    def kembalikanAlat(self, kode, kondisi, tgl):
        if tgl < self.tglPinjam:
            raise ValueError("Tanggal kembali tidak boleh sebelum tanggal pinjam.")
        for detail in self.daftarDetail:
            if detail.alat.kode == kode and not detail.isKembali():
                detail.prosesKembali(kondisi, tgl, self.batasKembali)
                detail.alat.terimaKembali(kondisi)
                detail.alat.selesaiTrx(self.id)
                self.hitungStatus()
                return
        raise ValueError(f"Alat {kode} tidak ada di transaksi {self.id} atau sudah dikembalikan.")

    def hitungStatus(self):
        kembali = [detail.isKembali() for detail in self.daftarDetail]
        if all(kembali):
            self.status = StatusTransaksi.SELESAI
        elif any(kembali):
            self.status = StatusTransaksi.SEBAGIAN_DIKEMBALIKAN
        else:
            self.status = StatusTransaksi.DIPINJAM

    def aktif(self):
        return self.status != StatusTransaksi.SELESAI

    def daftarAlat(self):
        return [detail.alat for detail in self.daftarDetail]

    def alatBelumKembali(self):
        return [detail.alat for detail in self.daftarDetail if not detail.isKembali()]

    def terlambat(self, tgl):
        return tgl > self.batasKembali