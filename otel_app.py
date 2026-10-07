import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar

st.set_page_config(page_title="Butik Otel Paneli", layout="wide")

# --- KULLANICI GİRİŞ KONTROLÜ ---
USERS = {
    "admin": "Otel2026!Sifre"  # Kendi kullanıcı adı ve şifrenizle değiştirin
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Butik Otel Paneli Girişi")
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if username in USERS and USERS[username] == password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Hatalı kullanıcı adı veya şifre!")
    st.stop()

# --- VERİ ALANI (SESSION STATE) ---
if "rezervasyonlar" not in st.session_state:
    st.session_state["rezervasyonlar"] = pd.DataFrame(
        columns=["ID", "Müşteri Adı", "Oda No", "Giriş Tarihi", "Çıkış Tarihi"]
    )

ODALAR = ["101 - Delüks Oda", "102 - Manzaralı Suit", "103 - Standart Oda", "104 - Aile Odası"]

st.title("🏨 Butik Otel Yönetim Paneli")

tab1, tab2, tab3 = st.tabs(["➕ Yeni Rezervasyon", "📅 Aylık Doluluk Takvimi", "📋 Liste & Rezervasyon Sil"])

# ---------------------------------------------------------
# TAB 1: YENİ REZERVASYON KONTROLÜ & EKLEME
# ---------------------------------------------------------
with tab1:
    st.subheader("Yeni Rezervasyon Oluştur")
    
    col1, col2 = st.columns(2)
    with col1:
        musteri = st.text_input("Müşteri Adı Soyadı")
        secilen_oda = st.selectbox("Oda Seçin", ODALAR)
    with col2:
        giris_tarihi = st.date_input("Giriş Tarihi", value=date.today())
        cikis_tarihi = st.date_input("Çıkış Tarihi", value=date.today() + timedelta(days=1))

    if st.button("Rezervasyonu Kaydet", type="primary"):
        if giris_tarihi >= cikis_tarihi:
            st.error("❌ Çıkış tarihi, giriş tarihinden sonraki bir tarih olmalıdır!")
        elif not musteri.strip():
            st.error("❌ Lütfen müşteri adını giriniz.")
        else:
            df = st.session_state["rezervasyonlar"]
            
            # Seçilen odanın mevcut kayıtlarını çek
            oda_kayitlari = df[df["Oda No"] == secilen_oda]
            
            # --- TAM KESİŞİM / ÇAKIŞMA KONTROLÜ ---
            cakisma = False
            for _, row in oda_kayitlari.iterrows():
                m_giris = row["Giriş Tarihi"]
                m_cikis = row["Çıkış Tarihi"]
                
                # Tarih objesi değilse datetime.date formatına dönüştür
                if isinstance(m_giris, str):
                    m_giris = pd.to_datetime(m_giris).date()
                if isinstance(m_cikis, str):
                    m_cikis = pd.to_datetime(m_cikis).date()

                if giris_tarihi < m_cikis and cikis_tarihi > m_giris:
                    cakisma = True
                    break

            if cakisma:
                st.error(f"⛔ **{secilen_oda}** seçtiğiniz **{giris_tarihi.strftime('%d.%m.%Y')} - {cikis_tarihi.strftime('%d.%m.%Y')}** tarihleri arasında ZATEN DOLU!")
            else:
                # Yeni benzersiz ID üret
                yeni_id = 1 if df.empty else int(df["ID"].max()) + 1
                
                yeni_kayit = pd.DataFrame([{
                    "ID": yeni_id,
                    "Müşteri Adı": musteri,
                    "Oda No": secilen_oda,
                    "Giriş Tarihi": giris_tarihi,
                    "Çıkış Tarihi": cikis_tarihi
                }])
                
                st.session_state["rezervasyonlar"] = pd.concat([df, yeni_kayit], ignore_index=True)
                st.success(f"✅ {secilen_oda} için {musteri} adına rezervasyon başarıyla kaydedildi!")

# ---------------------------------------------------------
# TAB 2: AYLIK DOLULUK TAKVİMİ EKRANI
# ---------------------------------------------------------
with tab2:
    st.subheader("Aylık Oda Doluluk Görünümü")
    
    col_yil, col_ay = st.columns(2)
    with col_yil:
        secilen_yil = st.selectbox("Yıl", range(2025, 2030), index=1)
    with col_ay:
        aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        secilen_ay_adi = st.selectbox("Ay", aylar, index=date.today().month - 1)
        secilen_ay = aylar.index(secilen_ay_adi) + 1

    # Ayın gün sayısını bulma
    _, gun_sayisi = calendar.monthrange(secilen_yil, secilen_ay)
    
    # Matris oluşturma (Odalar x Günler)
    df = st.session_state["rezervasyonlar"]
    matris = {oda: ["🟢 Boş"] * gun_sayisi for oda in ODALAR}

    for _, row in df.iterrows():
        m_giris = pd.to_datetime(row["Giriş Tarihi"]).date() if isinstance(row["Giriş Tarihi"], str) else row["Giriş Tarihi"]
        m_cikis = pd.to_datetime(row["Çıkış Tarihi"]).date() if isinstance(row["Çıkış Tarihi"], str) else row["Çıkış Tarihi"]
        
        for g in range(1, gun_sayisi + 1):
            mevcut_gun = date(secilen_yil, secilen_ay, g)
            if m_giris <= mevcut_gun < m_cikis:
                if row["Oda No"] in matris:
                    matris[row["Oda No"]][g - 1] = f"🔴 {row['Müşteri Adı']}"

    # Tablo olarak gösterme
    gun_sutunlari = [f"{g} {secilen_ay_adi[:3]}" for g in range(1, gun_sayisi + 1)]
    takvim_df = pd.DataFrame(matris).T
    takvim_df.columns = gun_sutunlari

    st.dataframe(takvim_df, use_container_width=True)

# ---------------------------------------------------------
# TAB 3: REZERVASYON LİSTESİ VE SİLME İŞLEMİ
# ---------------------------------------------------------
with tab3:
    st.subheader("📋 Mevcut Rezervasyonlar ve Silme")
    
    df = st.session_state["rezervasyonlar"]
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("🗑️ Rezervasyon Sil")
        
        silinecek_id = st.selectbox(
            "Silmek istediğiniz rezervasyon kaydını seçin:",
            options=df["ID"].tolist(),
            format_func=lambda x: f"ID: {x} - Müşteri: {df[df['ID'] == x]['Müşteri Adı'].values[0]} ({df[df['ID'] == x]['Oda No'].values[0]})"
        )
        
        if st.button("Seçilen Rezervasyonu Sil", type="secondary"):
            st.session_state["rezervasyonlar"] = df[df["ID"] != silinecek_id].reset_index(drop=True)
            st.success(f"ID: {silinecek_id} numaralı rezervasyon başarıyla silindi!")
            st.rerun()
    else:
        st.info("Sistemde henüz kayıtlı bir rezervasyon bulunmuyor.")

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar

st.set_page_config(page_title="Butik Otel Paneli", layout="wide")

# --- KULLANICI GİRİŞ KONTROLÜ ---
USERS = {
    "admin": "yigido58"  # Kendi kullanıcı adı ve şifrenizle değiştirin
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Butik Otel Paneli Girişi")
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if username in USERS and USERS[username] == password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Hatalı kullanıcı adı veya şifre!")
    st.stop()

# --- VERİ ALANI (SESSION STATE) ---
if "rezervasyonlar" not in st.session_state:
    st.session_state["rezervasyonlar"] = pd.DataFrame(
        columns=["ID", "Müşteri Adı", "Oda No", "Giriş Tarihi", "Çıkış Tarihi"]
    )

ODALAR = ["101 - Delüks Oda", "102 - Manzaralı Suit", "103 - Standart Oda", "104 - Aile Odası"]

st.title("🏨 Butik Otel Yönetim Paneli")

tab1, tab2, tab3 = st.tabs(["➕ Yeni Rezervasyon", "📅 Aylık Doluluk Takvimi", "📋 Liste & Rezervasyon Sil"])

# ---------------------------------------------------------
# TAB 1: YENİ REZERVASYON KONTROLÜ & EKLEME
# ---------------------------------------------------------
with tab1:
    st.subheader("Yeni Rezervasyon Oluştur")
    
    col1, col2 = st.columns(2)
    with col1:
        musteri = st.text_input("Müşteri Adı Soyadı")
        secilen_oda = st.selectbox("Oda Seçin", ODALAR)
    with col2:
        giris_tarihi = st.date_input("Giriş Tarihi", value=date.today())
        cikis_tarihi = st.date_input("Çıkış Tarihi", value=date.today() + timedelta(days=1))

    if st.button("Rezervasyonu Kaydet", type="primary"):
        if giris_tarihi >= cikis_tarihi:
            st.error("❌ Çıkış tarihi, giriş tarihinden sonraki bir tarih olmalıdır!")
        elif not musteri.strip():
            st.error("❌ Lütfen müşteri adını giriniz.")
        else:
            df = st.session_state["rezervasyonlar"]
            
            # Seçilen odanın mevcut kayıtlarını çek
            oda_kayitlari = df[df["Oda No"] == secilen_oda]
            
            # --- TAM KESİŞİM / ÇAKIŞMA KONTROLÜ ---
            # İki tarih aralığının (A1-A2 ile B1-B2) kesişme şartı: A1 < B2 ve A2 > B1
            cakisma = False
            for _, row in oda_kayitlari.iterrows():
                m_giris = row["Giriş Tarihi"]
                m_cikis = row["Çıkış Tarihi"]
                
                # Tarih objesi değilse datetime.date formatına dönüştür
                if isinstance(m_giris, str):
                    m_giris = pd.to_datetime(m_giris).date()
                if isinstance(m_cikis, str):
                    m_cikis = pd.to_datetime(m_cikis).date()

                if giris_tarihi < m_cikis and cikis_tarihi > m_giris:
                    cakisma = True
                    break

            if cakisma:
                st.error(f"⛔ **{secilen_oda}** seçtiğiniz **{giris_tarihi.strftime('%d.%m.%Y')} - {cikis_tarihi.strftime('%d.%m.%Y')}** tarihleri arasında ZATEN DOLU!")
            else:
                # Yeni benzersiz ID üret
                yeni_id = 1 if df.empty else df["ID"].max() + 1
                
                yeni_kayit = pd.DataFrame([{
                    "ID": yeni_id,
                    "Müşteri Adı": musteri,
                    "Oda No": secilen_oda,
                    "Giriş Tarihi": giris_tarihi,
                    "Çıkış Tarihi": cikis_tarihi
                }])
                
                st.session_state["rezervasyonlar"] = pd.concat([df, yeni_kayit], ignore_index=True)
                st.success(f"✅ {secilen_oda} için {musteri} adına rezervasyon başarıyla kaydedildi!")

# ---------------------------------------------------------
# TAB 2: AYLIK DOLULUK TAKVİMİ EKRANI
# ---------------------------------------------------------
with tab2:
    st.subheader("Aylık Oda Doluluk Görünümü")
    
    col_yil, col_ay = st.columns(2)
    with col_yil:
        secilen_yil = st.selectbox("Yıl", range(2025, 2030), index=1)
    with col_ay:
        aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        secilen_ay_adi = st.selectbox("Ay", aylar, index=date.today().month - 1)
        secilen_ay = aylar.index(secilen_ay_adi) + 1

    # Ayın gün sayısını bulma
    _, gun_sayisi = calendar.monthrange(secilen_yil, secilen_ay)
    
    # Matris oluşturma (Odalar x Günler)
    df = st.session_state["rezervasyonlar"]
    matris = {oda: ["🟢 Boş"] * gun_sayisi for oda in ODALAR}

    for _, row in df.iterrows():
        m_giris = pd.to_datetime(row["Giriş Tarihi"]).date() if isinstance(row["Giriş Tarihi"], str) else row["Giriş Tarihi"]
        m_cikis = pd.

import streamlit as st
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="Butik Otel Paneli", layout="wide")

# --- KULLANICI GİRİŞ KONTROLÜ ---
USERS = {
    "admin": "yigido58"  # Kendi kullanıcı adı ve şifrenizle değiştirin
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Butik Otel Paneli Girişi")
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if username in USERS and USERS[username] == password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Hatalı kullanıcı adı veya şifre!")
    st.stop()

# --- VERİ ALANI HAZIRLIĞI ---
# Mevcut rezervasyonları saklamak için hafıza alanı
if "rezervasyonlar" not in st.session_state:
    st.session_state["rezervasyonlar"] = pd.DataFrame(
        columns=["Müşteri Adı", "Oda No", "Giriş Tarihi", "Çıkış Tarihi"]
    )

ODALAR = ["101 - Delüks Oda", "102 - Manzaralı Suit", "103 - Standart Oda", "104 - Aile Odası"]

st.title("🏨 Butik Otel Yönetim Paneli")

# Sekmeler oluşturuyoruz
tab1, tab2 = st.tabs(["➕ Yeni Rezervasyon Ekleyin", "📅 Oda Doluluk Takvimi & Durumu"])

# ---------------------------------------------------------
# TAB 1: REZERVASYON EKLEME & ÇAKIŞMA KONTROLÜ
# ---------------------------------------------------------
with tab1:
    st.subheader("Yeni Rezervasyon Oluştur")
    
    col1, col2 = st.columns(2)
    with col1:
        musteri = st.text_input("Müşteri Adı Soyadı")
        secilen_oda = st.selectbox("Oda Seçin", ODALAR)
    with col2:
        giris_tarihi = st.date_input("Giriş Tarihi", min_value=date.today())
        cikis_tarihi = st.date_input("Çıkış Tarihi", min_value=giris_tarihi)

    if st.button("Rezervasyonu Kaydet"):
        if giris_tarihi >= cikis_tarihi:
            st.error("Çıkış tarihi, giriş tarihinden sonra olmalıdır!")
        elif not musteri.strip():
            st.error("Lütfen müşteri adını giriniz.")
        else:
            # --- ÇAKIŞMA KONTROLÜ (Aynı Oda ve Tarih Kesişimi) ---
            df = st.session_state["rezervasyonlar"]
            
            # Seçilen odanın mevcut rezervasyonlarını filtrele
            oda_rezervasyonlari = df[df["Oda No"] == secilen_oda]
            
            cakisma = False
            for _, row in oda_rezervasyonlari.iterrows():
                m_giris = row["Giriş Tarihi"]
                m_cikis = row["Çıkış Tarihi"]
                
                # Tarih aralıklarının kesişip kesişmediğini kontrol et
                if not (cikis_tarihi <= m_giris or giris_tarihi >= m_cikis):
                    cakisma = True
                    break
            
            if cakisma:
                st.error(f"❌ **{secilen_oda}** seçilen tarihler arasında ({giris_tarihi} - {cikis_tarihi}) DOLUDUR! Başka bir tarih veya oda seçiniz.")
            else:
                yeni_kayit = pd.DataFrame([{
                    "Müşteri Adı": musteri,
                    "Oda No": secilen_oda,
                    "Giriş Tarihi": giris_tarihi,
                    "Çıkış Tarihi": cikis_tarihi
                }])
                st.session_state["rezervasyonlar"] = pd.concat([df, yeni_kayit], ignore_index=True)
                st.success(f"✅ {secilen_oda} için {musteri} adına rezervasyon başarıyla oluşturuldu!")

# ---------------------------------------------------------
# TAB 2: ODALARIN DOLU/BOŞ TARİH EKRANI
# ---------------------------------------------------------
with tab2:
    st.subheader("Tarih Bazlı Oda Doluluk Durumu")
    
    sorgu_tarihi = st.date_input("Hangi Tarihteki Durumu Görmek İstiyorsunuz?", value=date.today())
    
    df = st.session_state["rezervasyonlar"]
    
    # Seçilen tarihte hangi odaların dolu olduğunu tespit et
    dolu_odalar = []
    dolu_detay = {}
    
    for _, row in df.iterrows():
        if row["Giriş Tarihi"] <= sorgu_tarihi < row["Çıkış Tarihi"]:
            dolu_odalar.append(row["Oda No"])
            dolu_detay[row["Oda No"]] = row["Müşteri Adı"]

    st.markdown(f"### 📊 **{sorgu_tarihi.strftime('%d.%m.%Y')}** Tarihindeki Odaların Durumu")
    
    # Visual Kartlar (Metrikler) Halinde Gösterim
    cols = st.columns(len(ODALAR))
    for idx, oda in enumerate(ODALAR):
        with cols[idx]:
            if oda in dolu_odalar:
                st.error(f"🔴 **{oda}**\n\n**DOLU**\n\nMüşteri: {dolu_detay[oda]}")
            else:
                st.success(f"🟢 **{oda}**\n\n**BOŞ**\n\nKonaklamaya Uygun")

    st.divider()
    st.subheader("📋 Tüm Rezervasyon Listesi")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Henüz kaydedilmiş bir rezervasyon bulunmuyor.")

import streamlit as st

# Kullanıcı adı ve şifre tanımlamaları
USERS = {
    "admin": "yigido58",  # Kullanıcı adı: admin, Şifre: yigido58
    "yonetici": "sifre456"
}

def check_password():
    """Kullanıcı adı ve şifreyi doğrular."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔒 Butik Otel Paneli Girişi")
        
        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
        
        if st.button("Giriş Yap"):
            if username in USERS and USERS[username] == password:
                st.session_state["authenticated"] = True
                st.success("Giriş başarılı!")
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı!")
        return False
    return True

# Eğer giriş yapılmadıysa uygulamanın geri kalanını çalıştırma
if not check_password():
    st.stop()

# --- BURADAN SONRASI MEVCUT UYGULAMA KODLARINIZ ---
st.title("🏨 Butik Otel Yönetim Paneli")
# ... mevcut otel_app.py kodlarınız buraya gelecek ...

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
