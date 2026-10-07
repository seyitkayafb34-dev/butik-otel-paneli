import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar

st.set_page_config(page_title="Butik Otel Paneli", layout="wide")

# --- KULLANICI GİRİŞ KONTROLÜ ---
USERS = {
    "admin": "yigido58"  # Kendi kullanıcı adı ve şifrenizi girin
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
