# Laporan Praktikum Business Intelligence — Coffee Shop Sales

## 1. Hasil audit data

Audit berstatus **LULUS AUDIT DASAR**. Sebanyak 149.116 baris tetap dipertahankan: tidak ada nilai hilang, baris duplikat, atau `transaction_id` berulang. Perbaikan yang dilakukan ialah penghapusan spasi awal/akhir pada `product_detail` sebanyak **1.952** nilai.

Sebanyak **15 produk** memiliki lebih dari satu harga. Ini tidak otomatis salah karena harga dapat sah berbeda akibat ukuran produk, promo, kebijakan harga, atau perubahan harga pada waktu berbeda. Audit mempertahankan variasi itu dan hanya menandainya untuk pemeriksaan bisnis bila diperlukan.

## 2. Empat angka kontrol — seluruh gerai

Periode: **1 Januari–30 Juni 2023**. Filter: **Astoria, Hell's Kitchen, dan Lower Manhattan**.

| Indikator | Nilai |
| --- | ---: |
| Total penjualan | 698.812,33 |
| Transaksi tercatat | 149.116 |
| Rata-rata nilai transaksi | 4,69 |
| Pertumbuhan Juni 2023 terhadap Mei 2023 | 6,23% |

## 3. Filter Astoria

Dengan filter **Astoria** saja, total penjualan menjadi **232.243,91** dan transaksi tercatat menjadi **50.599**.

## 4. Perbandingan tiga gerai

Saat semua gerai dipilih, Hell's Kitchen memiliki penjualan tertinggi: **236.511,17**; Astoria **232.243,91**; dan Lower Manhattan **230.057,25**. Temuan grafik batang: Hell's Kitchen memimpin, tetapi selisihnya dengan Astoria hanya **4.267,26** sehingga ketiga gerai relatif seimbang dan perlu ditelusuri per periode atau produk.

## 5. Kategori terbesar

Kategori terbesar adalah **Coffee**: **269.952,45**, setara **38,63%** dari total penjualan pada cakupan seluruh gerai yang sama.

## 6. Produk teratas

Produk **Sustainably Grown Organic Lg (ID 61)** menghasilkan **21.151,75**. Peringkat grafik memakai **nilai penjualan**, bukan jumlah unit atau keuntungan; produk berharga lebih tinggi dapat berada di atas produk dengan unit lebih banyak.

## 7. Jam transaksi terbesar

Jam **10:00** memiliki transaksi tercatat terbesar, yaitu **18.545** `transaction_id` unik sepanjang periode. Ini belum membuktikan antrean panjang karena data tidak memuat waktu tunggu, jumlah kasir, kapasitas layanan, maupun jumlah orang yang mengantre bersamaan.

## 8. Insight lengkap

Pada periode **Januari–Juni 2023**, dengan filter **seluruh gerai**, kategori **Coffee** menghasilkan **269.952,45** atau **38,63%** dari penjualan sehingga berkontribusi terbesar. Batasannya: data merupakan transaksi tercatat per `transaction_id`, belum memastikan seluruh isi struk atau pelanggan unik, dan mata uang tidak dinyatakan. Tindakan pemeriksaan: analisis penjualan Coffee per gerai, bulan, dan produk untuk mengetahui apakah kontribusi tinggi didominasi satu gerai atau produk sebelum keputusan stok/promosi.

## Definisi empat indikator

| Indikator | Definisi dan rumus | Cakupan/batasan |
| --- | --- | --- |
| Total penjualan | `sum(sales)`, dengan `sales = transaction_qty × unit_price`. | Mengikuti filter gerai dan seluruh periode; mata uang tidak tersedia. |
| Transaksi tercatat | `nunique(transaction_id)`. | Bukan pelanggan unik. |
| Rata-rata nilai transaksi | `total_sales / total_transactions`. | Belum tentu nilai seluruh struk pelanggan. |
| Pertumbuhan bulanan | `(penjualan bulan ini - bulan lalu) / bulan lalu × 100%`. | Juni 2023 terhadap Mei 2023 dalam filter aktif. |
