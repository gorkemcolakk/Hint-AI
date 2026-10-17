"""PII Maskeleme Birim Testleri."""

from app.modules.llm_gateway.mask import (
    MaskedText,
    is_valid_tckn,
    is_valid_tr_iban,
    mask_pii,
)


def test_tckn_validation() -> None:
    # 10000000146 geçerli bir TCKN örneğidir
    assert is_valid_tckn("10000000146") is True
    # Geçersiz 11 haneli sayı
    assert is_valid_tckn("12345678901") is False
    # Sıfırla başlayan
    assert is_valid_tckn("01234567890") is False
    # Eksik/fazla basamak
    assert is_valid_tckn("1000000014") is False
    assert is_valid_tckn("100000001460") is False
    # Harf içeren
    assert is_valid_tckn("1000000014A") is False


def test_mask_pii_valid_tckn() -> None:
    text = "Benim kimlik numaram 10000000146, lütfen kontrol et."
    res = mask_pii(text)
    assert "[TCKN]" in res.masked_text
    assert "10000000146" not in res.masked_text
    assert "TCKN" in res.detected_types
    assert res.has_pii is True
    assert isinstance(res.masked_text, MaskedText)


def test_mask_pii_does_not_mask_invalid_11_digit_numbers() -> None:
    # Matematik sorularındaki 11 basamaklı rastgele sayılar maskelenmemelidir
    text = "Soruda 12345678901 sayısı ile 10000000000 sayısının toplamı soruluyor."
    res = mask_pii(text)
    assert "[TCKN]" not in res.masked_text
    assert "12345678901" in res.masked_text
    assert "10000000000" in res.masked_text
    assert res.has_pii is False


def test_mask_pii_phone_numbers() -> None:
    cases = [
        ("Bana +90 532 123 45 67 numarasından ulaşabilirsiniz.", "[TELEFON]"),
        ("İletişim: 0532 123 45 67", "[TELEFON]"),
        ("Cep: 0 532 123 45 67", "[TELEFON]"),
        ("Numaram 05321234567", "[TELEFON]"),
        ("Tel: 532-123-45-67", "[TELEFON]"),
        ("Arayın: +905321234567", "[TELEFON]"),
    ]
    for text, expected in cases:
        res = mask_pii(text)
        assert expected in res.masked_text
        assert "TELEFON" in res.detected_types
        assert res.has_pii is True


def test_mask_pii_preserves_math_expressions() -> None:
    text = "500 elma ile 250 armut toplandığında 750 meyve olur. 5 * 10 = 50."
    res = mask_pii(text)
    assert res.has_pii is False
    assert res.masked_text == text


def test_mask_pii_email() -> None:
    text = "Ödevimi ogrenci.ali@okul.k12.tr adresine ve veli_test@example.com'a gönderdim."
    res = mask_pii(text)
    assert "ogrenci.ali@okul.k12.tr" not in res.masked_text
    assert "veli_test@example.com" not in res.masked_text
    assert res.masked_text.count("[E-POSTA]") == 2
    assert "E-POSTA" in res.detected_types


def test_mask_pii_iban() -> None:
    # Geçerli TR IBAN: TR42 0006 1000 0000 0012 3456 78 (mod 97 = 1)
    valid_iban = "TR42 0006 1000 0000 0012 3456 78"
    assert is_valid_tr_iban(valid_iban) is True
    text = f"Burs için IBAN: {valid_iban}"
    res = mask_pii(text)
    assert "[IBAN]" in res.masked_text
    assert "IBAN" in res.detected_types

    # Geçersiz TR IBAN maskelenmemeli
    invalid_text = "Hesap: TR00 1234 5678 9012 3456 7890 12"
    res_inv = mask_pii(invalid_text)
    assert "[IBAN]" not in res_inv.masked_text


def test_mask_pii_names_heuristic() -> None:
    cases = [
        ("Benim adım Ahmet, bu soruyu anlamadım.", "Benim adım [ISIM], bu soruyu anlamadım."),
        ("Adım Zeynep Kaya, yardım eder misin?", "Adım [ISIM], yardım eder misin?"),
        ("İsmim Mehmet, 7. sınıftayım.", "İsmim [ISIM], 7. sınıftayım."),
        ("Bana Can derler, nasıl çözebilirim?", "Bana [ISIM] derler, nasıl çözebilirim?"),
    ]
    for inp, expected in cases:
        res = mask_pii(inp)
        assert res.masked_text == expected
        assert "ISIM" in res.detected_types


def test_mask_pii_school_heuristic() -> None:
    cases = [
        (
            "Ben Atatürk İlkokulu öğrencisiyim.",
            "Ben [OKUL] öğrencisiyim.",
        ),
        (
            "Kadıköy Anadolu Lisesi 9. sınıf matematik sorusu.",
            "[OKUL] 9. sınıf matematik sorusu.",
        ),
        (
            "Mehmet Akif Ersoy Ortaokulu fen sınavı.",
            "[OKUL] fen sınavı.",
        ),
        (
            "İzmir Fen Lisesi deneme sınavı.",
            "[OKUL] deneme sınavı.",
        ),
    ]
    for inp, expected in cases:
        res = mask_pii(inp)
        assert res.masked_text == expected
        assert "OKUL" in res.detected_types


def test_mask_pii_combined_child_input() -> None:
    text = (
        "Merhaba, benim adım Ayşe. Atatürk İlkokulu 4. sınıftayım. "
        "Babamın numarası 0532 999 88 77 ve e-postası veli@example.com. "
        "Sorum şu: 24/6 işleminin sonucu kaçtır?"
    )
    res = mask_pii(text)
    assert "Ayşe" not in res.masked_text
    assert "Atatürk İlkokulu" not in res.masked_text
    assert "0532 999 88 77" not in res.masked_text
    assert "veli@example.com" not in res.masked_text
    assert "24/6 işleminin sonucu kaçtır?" in res.masked_text
    assert set(res.detected_types) == {"ISIM", "OKUL", "TELEFON", "E-POSTA"}
    assert isinstance(res.masked_text, MaskedText)
