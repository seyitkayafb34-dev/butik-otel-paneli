import datetime
import sqlite3
import pandas as pd
import streamlit as st

# --- VERİTABANI KURULUMU ---
conn = sqlite3.connect("otel_yonetim.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS rezervasyonlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        musteri_adi TEXT,
        oda_no TEXT,
        giris_tarihi DATE,
        cikis_tarihi DATE,
        toplam_tutar REAL,
        odeme_durumu TEXT
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS kasa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarih DATE,
        islem_tipi TEXT,
        kategori TEXT,
        tutar REAL,
        aciklama TEXT
    )
"""
)
conn.commit()

# --- ARAYÜZ AYARLARI ---
st.set_page_config(
    page_title="Butik Otel Yönetimi", page_icon="🏨", layout="wide"
)
st.title("🏨 Butik Otel Rezervasyon & Nakit Akış Paneli")

ODALAR = [f"Oda {i}" for i in range(101, 109)]  # 8 Oda: 101-108
GIDER_KALEMLERI = [
    "Personel & Maas",
    "Mutfak & Kahvalti",
    "Elektrik / Su / Dogalgaz",
    "Temizlik & Hijyen",
    "Camasirhane & Tekstil",
    "Bakim & Onarim",
    "Yazilim & Pazarlama",
    "Vergi & Sigorta",
    "Diger Giderler",
]

sekme1, sekme2, sekme3 = st.tabs(
    ["🛎️ Rezervasyonlar", "💰 Nakit Akışı (Kasa)", "📊 Finansal Raporlar"]
)

# --- SEKME 1: REZERVASYONLAR ---
with sekme1:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Yeni Rezervasyon Ekle")
        with st.form("rez_form", clear_on_submit=True):
            m_adi = st.text_input("Müşteri Adı Soyadı")
            oda = st.selectbox("Oda Seçimi", ODALAR)
            giris = st.date_input("Giriş Tarihi", datetime.date.today())
            cikis = st.date_input(
                "Çıkış Tarihi", datetime.date.today() + datetime.timedelta(days=1)
            )
            tutar = st.number_input("Toplam Ücret (TL)", min_value=0.0, step=100.0)
            durum = st.selectbox(
                "Ödeme Durumu",
                ["Ödendi", "Kısmi Ödendi", "Ödeme Bekliyor"],
            )

            if st.form_submit_button("Rezervasyonu Kaydet"):
                if m_adi:
                    cursor.execute(
                        "INSERT INTO rezervasyonlar (musteri_adi, oda_no, giris_tarihi, cikis_tarihi, toplam_tutar, odeme_durumu) VALUES (?,?,?,?,?,?)",
                        (m_adi, oda, giris, cikis, tutar, durum),
                    )
                    if durum == "Ödendi":
                        cursor.execute(
                            "INSERT INTO kasa (tarih, islem_tipi, kategori, tutar, aciklama) VALUES (?,?,?,?,?)",
                            (
                                giris,
                                "Gelir",
                                "Oda Konaklama",
                                tutar,
                                f"Rezervasyon: {m_adi} ({oda})",
                            ),
                        )
                    conn.commit()
                    st.success("Rezervasyon başarıyla kaydedildi!")
                    st.rerun()

    with col2:
        st.subheader("Mevcut Rezervasyon Listesi")
        df_rez = pd.read_sql_query(
            "SELECT id as ID, musteri_adi as Müşteri, oda_no as Oda, giris_tarihi as Giriş, cikis_tarihi as Çıkış, toplam_tutar as Tutar, odeme_durumu as Durum FROM rezervasyonlar ORDER BY id DESC",
            conn,
        )
        st.dataframe(df_rez, use_container_width=True)

# --- SEKME 2: NAKİT AKIŞI (KASA) ---
with sekme2:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Yeni Kasa İşlemi")
        with st.form("kasa_form", clear_on_submit=True):
            islem_tipi = st.radio("İşlem Tipi", ["Gider", "Gelir"])
            if islem_tipi == "Gider":
                kategori = st.selectbox("Gider Kalemi", GIDER_KALEMLERI)
            else:
                kategori = st.selectbox(
                    "Gelir Kalemi",
                    [
                        "Oda Konaklama",
                        "Restoran / Cafe",
                        "Ekstra Hizmetler",
                        "Diğer Gelir",
                    ],
                )

            islem_tarihi = st.date_input("Tarih", datetime.date.today())
            islem_tutari = st.number_input(
                "Tutar (TL)", min_value=0.0, step=50.0
            )
            aciklama = st.text_input("Açıklama")

            if st.form_submit_button("İşlemi Kaydet"):
                cursor.execute(
                    "INSERT INTO kasa (tarih, islem_tipi, kategori, tutar, aciklama) VALUES (?,?,?,?,?)",
                    (
                        islem_tarihi,
                        islem_tipi,
                        kategori,
                        islem_tutari,
                        aciklama,
                    ),
                )
                conn.commit()
                st.success("Kasa işlemi kaydedildi!")
                st.rerun()

    with col2:
        st.subheader("Kasa Hareketleri")
        df_kasa = pd.read_sql_query(
            "SELECT id as ID, tarih as Tarih, islem_tipi as Tip, kategori as Kategori, tutar as Tutar, aciklama as Açıklama FROM kasa ORDER BY id DESC",
            conn,
        )
        st.dataframe(df_kasa, use_container_width=True)

# --- SEKME 3: Raporlar ---
with sekme3:
    st.subheader("Finansal Durum Özeti")

    toplam_gelir = (
        cursor.execute(
            "SELECT SUM(tutar) FROM kasa WHERE islem_tipi='Gelir'"
        ).fetchone()[0]
        or 0
    )
    toplam_gider = (
        cursor.execute(
            "SELECT SUM(tutar) FROM kasa WHERE islem_tipi='Gider'"
        ).fetchone()[0]
        or 0
    )
    net_durum = toplam_gelir - toplam_gider

    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Gelir", f"{toplam_gelir:,.2f} TL")
    m2.metric("Toplam Gider", f"{toplam_gider:,.2f} TL")
    m3.metric(
        "Net Kâr / Zarar",
        f"{net_durum:,.2f} TL",
        delta_color="normal" if net_durum >= 0 else "inverse",
    )

    st.divider()

    if toplam_gider > 0:
        st.write("### Gider Dağılımı")
        df_giderler = pd.read_sql_query(
            "SELECT kategori, SUM(tutar) as Toplam FROM kasa WHERE islem_tipi='Gider' GROUP BY kategori",
            conn,
        )
        st.bar_chart(df_giderler.set_index("kategori"))
