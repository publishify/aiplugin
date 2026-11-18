# Publishify — Your AI Editorial Board

**Publishify kapsamlı bir yayın kuruludur.**

İstediğin yerde yaz. Metnine, kendi yapay zekânda bir de kurul baksın.

[Site](https://publishify.app/tr/) · [English README](README.md) · [İş akışı](docs/architecture.md) · [Güncel durum](docs/status.md)

![Publishify yayın kurulu ve Yolcunun Yedi Merhalesi](docs/assets/editorial-board-tr.png)

*Temsilî kurul görselidir; gerçek bir kitap incelemesi veya ölçüm sonucu değildir.*

Publishify, zaten kullandığın yapay zekâ uygulamasına eklenen bir **yayın kurulu eklentisi**. Editör, Süreklilik denetçisi ve simüle Okur Paneli; metne bağlı notlarını bir pano ve indirilebilir raporda buluşturmak için birlikte çalışır.

> **15 Kasım 2026 — Ürün geliştirmesi sürüyor.** İlk kapsam Claude için **Kurgu masası**. Depodaki `spike/` tamamlanmış teknik denemenin kaydıdır; sunucusu kaldırılmıştır. Üretim kurulumu ve tam roman kalite ölçümü henüz hazır değil. Eski deneme komutları ürün kurulumu değildir.

## Kurulda kim var?

| Rol | Görev |
| --- | --- |
| **Editör** | Bölüm yapısı, tempo, bakış açısı, karakter davranışları ve güçlü yanlar |
| **Süreklilik denetçisi** | Olgu dosyası ve betik adaylarından hareketle isim, tarih, yaş ve olay tutarlılığı |
| **Okur Paneli** | Farklı okur bakışlarından merak, açıklık, duygusal etki ve beklenti |

Betikler dosyayı okur, böler, sayar ve kaynakları eşleştirir. Yapay zekâ bağlamı yorumlar. Alıntının metinde bulunması, yorumun mutlaka doğru olduğu anlamına gelmez. Son karar yazarda veya sorumlu editördedir.

## Nasıl çalışacak?

1. Eklentiyi kurup Publishify hesabınla giriş yaparsın.
2. Kurgu masasını ve inceleme kapsamını seçersin.
3. Dosyanı AI uygulamasına eklersin; Python betikleri o ortamda işler.
4. Sunucu rol kartlarını ve sıradaki görevi verir; okuma kendi yapay zekânda yapılır.
5. Kaynakları görünen notları panoda inceler, raporunu indirirsin.

**Dosya ve çıkarılan tam metin Publishify sunucusuna gönderilmez.** Sonuçlar kısa alıntılar içerebilir. AI sağlayıcının dosya işleme koşulları geçerlidir; “Publishify’a yüklenmez” demek “hiçbir bulutta işlenmez” demek değildir.

Sunucu; giriş, lisans, kullanım hakkı, oturum, masa kataloğu ve görev akışını yönetir. Pano ve rapor AI ortamında oluşur. Sunucuda okuma modeli ya da kalıcı kitap/rapor arşivi sunulmuyor.

## Kurulum durumu

Üretim kurulum rehberi henüz yayımlanmadı. Planlanan komutlar:

```text
/publishify:review
/publishify:status
```

İlk hedef Claude. ChatGPT Plus ve Codex CLI teknik denemeleri, tamamlanmış ürün entegrasyonu anlamına gelmiyor. Dosya biçimleri için DOCX, EPUB, Markdown ve TXT hazırlanıyor; PDF rapor çıktısıdır.

## Ücret ve kapsam

Kesin fiyat yok. Limitli tek seferlik, aylık ve yıllık lisanslar; ayda üç ücretsiz ön değerlendirme planlanıyor. Kelime sınırı ve yeniden inceleme kapsamı satıştan önce açıklanacak. Okumalar kendi AI hesabında, sağlayıcının kullanım koşullarıyla çalışır.

Kurgu dışındaki kitap, yayına hazırlık, öğrenci, akademik ve kurum masaları yol haritasındadır. Sözleşme, patent ve tıbbi metinler kapsam dışıdır.

## Belgeler

- [Mimari ve veri akışı](docs/architecture.md)
- [Kurgu masası](docs/fiction-desk.md)
- [Kurulum ve önkoşullar](docs/installation.md)
- [Deneme sonuçları ve açık noktalar](docs/status.md)
- [F1 yol haritası](docs/roadmap.md)
- [Gizlilik sınırları](docs/privacy.md)
- [Katkı rehberi](docs/contributing.md)

[Yolcunun Yedi Merhalesi](https://publishify.app/tr/blog/yolcunun-yedi-merhalesi/), **Ali Osman Akçaoğlu** tarafından geliştirilen bir anlatı merceğidir; zorunlu olay örgüsü kalıbı değildir.

[Publishify yazı editörü](https://github.com/publishify/publishify) · [İletişim](mailto:info@publishify.app)

Depoda henüz yazılım lisansı seçilmedi. Deponun açık görünmesi, kod, marka veya görsel için kendiliğinden yeniden kullanım izni vermez.
