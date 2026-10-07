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

# --- VERİ ALANLARI (SESSION STATE HAZIRLIĞI) ---
if "rezervasyonlar" not in st.session_state:
    st.session_state["rezervasyonlar"] = pd.DataFrame(
        columns=["ID", "Müşteri Adı", "Oda No", "Giriş Tarihi", "Çıkış Tarihi", "Ücret (TL)"]
    )

if "finans" not in st.session_state:
    st.session_state["finans"] = pd.DataFrame(
        columns=["ID", "Tarih", "Tür", "Kategori", "Açıklama", "Tutar (TL)"]
    )

if "butce" not in st.session_state:
    st.session_state["butce"] = pd.DataFrame(
        columns=["ID", "Tür", "Kategori", "Hedef Bütçe (TL)"]
    )

# 8 ODALI İSİMLENDİRME
ODALAR = ["111", "222", "333", "444", "555", "666", "777", "888"]
KATEGORILER = ["Oda Konaklama", "Restoran/Kafe", "Personel Maaşı", "Fatura/Aidat", "Tedarik/Malzeme", "Diğer"]

st.title("🏨 Butik Otel Yönetim Paneli")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ Yeni Rezervasyon", 
    "📅 Aylık Doluluk Takvimi", 
    "📋 Liste & Rezervasyon Sil",
    "💰 Nakit Akışı & Kategori Özetleri",
    "🎯 Bütçe & Hedef Planlama"
])

# ---------------------------------------------------------
# TAB 1: YENİ REZERVASYON KONTROLÜ & EKLEME
# ---------------------------------------------------------
with tab1:
    st.subheader("Yeni Rezervasyon Oluştur")
    
    col1, col2 = st.columns(2)
    with col1:
        musteri = st.text_input("Müşteri Adı Soyadı")
        secilen_oda = st.selectbox("Oda Seçin", ODALAR)
        ucret = st.number_input("Konaklama Ücreti (TL)", min_value=0.0, value=1500.0, step=100.0)
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
            oda_kayitlari = df[df["Oda No"] == secilen_oda] if not df.empty else pd.DataFrame()
            
            cakisma = False
            if not oda_kayitlari.empty:
                for _, row in oda_kayitlari.iterrows():
                    m_giris = pd.to_datetime(row["Giriş Tarihi"]).date() if isinstance(row["Giriş Tarihi"], str) else row["Giriş Tarihi"]
                    m_cikis = pd.to_datetime(row["Çıkış Tarihi"]).date() if isinstance(row["Çıkış Tarihi"], str) else row["Çıkış Tarihi"]

                    if giris_tarihi < m_cikis and cikis_tarihi > m_giris:
                        cakisma = True
                        break

            if cakisma:
                st.error(f"⛔ **Oda {secilen_oda}** seçtiğiniz **{giris_tarihi.strftime('%d.%m.%Y')} - {cikis_tarihi.strftime('%d.%m.%Y')}** tarihleri arasında ZATEN DOLU!")
            else:
                yeni_id = 1 if df.empty else int(df["ID"].max()) + 1
                
                yeni_kayit = pd.DataFrame([{
                    "ID": yeni_id,
                    "Müşteri Adı": musteri,
                    "Oda No": secilen_oda,
                    "Giriş Tarihi": giris_tarihi,
                    "Çıkış Tarihi": cikis_tarihi,
                    "Ücret (TL)": ucret
                }])
                st.session_state["rezervasyonlar"] = pd.concat([df, yeni_kayit], ignore_index=True)
                
                # Otomatik Finans Geliri Ekleme
                df_finans = st.session_state["finans"]
                finans_id = 1 if df_finans.empty else int(df_finans["ID"].max()) + 1
                yeni_gelir = pd.DataFrame([{
                    "ID": finans_id,
                    "Tarih": giris_tarihi,
                    "Tür": "Gelir",
                    "Kategori": "Oda Konaklama",
                    "Açıklama": f"Oda {secilen_oda} - {musteri}",
                    "Tutar (TL)": ucret
                }])
                st.session_state["finans"] = pd.concat([df_finans, yeni_gelir], ignore_index=True)
                
                st.success(f"✅ Oda {secilen_oda} için {musteri} adına rezervasyon ve {ucret} TL gelir kaydedildi!")

# ---------------------------------------------------------
# TAB 2: AYLIK DOLULUK TAKVİMİ EKRANI (8 ODA)
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

    _, gun_sayisi = calendar.monthrange(secilen_yil, secilen_ay)
    df = st.session_state["rezervasyonlar"]
    matris = {oda: ["🟢 Boş"] * gun_sayisi for oda in ODALAR}

    if not df.empty:
        for _, row in df.iterrows():
            m_giris = pd.to_datetime(row["Giriş Tarihi"]).date() if isinstance(row["Giriş Tarihi"], str) else row["Giriş Tarihi"]
            m_cikis = pd.to_datetime(row["Çıkış Tarihi"]).date() if isinstance(row["Çıkış Tarihi"], str) else row["Çıkış Tarihi"]
            
            for g in range(1, gun_sayisi + 1):
                mevcut_gun = date(secilen_yil, secilen_ay, g)
                if m_giris <= mevcut_gun < m_cikis:
                    if row["Oda No"] in matris:
                        matris[row["Oda No"]][g - 1] = f"🔴 {row['Müşteri Adı']}"

    gun_sutunlari = [f"{g} {secilen_ay_adi[:3]}" for g in range(1, gun_sayisi + 1)]
    takvim_df = pd.DataFrame(matris).T
    takvim_df.columns = gun_sutunlari

    st.dataframe(takvim_df, use_container_width=True)

# ---------------------------------------------------------
# TAB 3: REZERVASYON LİSTESİ VE SİLME İŞLEMİ
# 
