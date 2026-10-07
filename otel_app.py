import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar

st.set_page_config(page_title="Butik Otel Paneli", layout="wide")

# --- KULLANICI GİRİŞ KONTROLÜ ---
USERS = {
    "admin": "Otel2026!Sifre"  # Kendi kullanıcı adı ve şifrenizi girin
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

# --- VERİ ALANLARI (SESSION STATE) ---
if "rezervasyonlar" not in st.session_state:
    st.session_state["rezervasyonlar"] = pd.DataFrame(
        columns=["ID", "Müşteri Adı", "Oda No", "Giriş Tarihi", "Çıkış Tarihi", "Ücret (TL)"]
    )

if "finans" not in st.session_state:
    st.session_state["finans"] = pd.DataFrame(
        columns=["ID", "Tarih", "Tür", "Kategori", "Açıklama", "Tutar (TL)"]
    )

ODALAR = ["101 - Delüks Oda", "102 - Manzaralı Suit", "103 - Standart Oda", "104 - Aile Odası"]

st.title("🏨 Butik Otel Yönetim Paneli")

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Yeni Rezervasyon", 
    "📅 Aylık Doluluk Takvimi", 
    "📋 Liste & Rezervasyon Sil",
    "💰 Nakit Akışı & Gelir/Gider"
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
            oda_kayitlari = df[df["Oda No"] == secilen_oda]
            
            # Tam çakışma kontrolü
            cakisma = False
            for _, row in oda_kayitlari.iterrows():
                m_giris = pd.to_datetime(row["Giriş Tarihi"]).date() if isinstance(row["Giriş Tarihi"], str) else row["Giriş Tarihi"]
                m_cikis = pd.to_datetime(row["Çıkış Tarihi"]).date() if isinstance(row["Çıkış Tarihi"], str) else row["Çıkış Tarihi"]

                if giris_tarihi < m_cikis and cikis_tarihi > m_giris:
                    cakisma = True
                    break

            if cakisma:
                st.error(f"⛔ **{secilen_oda}** seçtiğiniz **{giris_tarihi.strftime('%d.%m.%Y')} - {cikis_tarihi.strftime('%d.%m.%Y')}** tarihleri arasında ZATEN DOLU!")
            else:
                yeni_id = 1 if df.empty else int(df["ID"].max()) + 1
                
                # 1. Rezervasyonu Ekle
                yeni_kayit = pd.DataFrame([{
                    "ID": yeni_id,
                    "Müşteri Adı": musteri,
                    "Oda No": secilen_oda,
                    "Giriş Tarihi": giris_tarihi,
                    "Çıkış Tarihi": cikis_tarihi,
                    "Ücret (TL)": ucret
                }])
                st.session_state["rezervasyonlar"] = pd.concat([df, yeni_kayit], ignore_index=True)
                
                # 2. Ücreti Otomatik Gelir Olarak Nakit Akışına Ekle
                df_finans = st.session_state["finans"]
                finans_id = 1 if df_finans.empty else int(df_finans["ID"].max()) + 1
                yeni_gelir = pd.DataFrame([{
                    "ID": finans_id,
                    "Tarih": giris_tarihi,
                    "Tür": "Gelir",
                    "Kategori": "Oda Konaklama",
                    "Açıklama": f"{secilen_oda} - {musteri}",
                    "Tutar (TL)": ucret
                }])
                st.session_state["finans"] = pd.concat([df_finans, yeni_gelir], ignore_index=True)
                
                st.success(f"✅ {secilen_oda} için {musteri} adına rezervasyon ve {ucret} TL gelir kaydedildi!")

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

    _, gun_sayisi = calendar.monthrange(secilen_yil, secilen_ay)
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

# ---------------------------------------------------------
# TAB 4: NAKİT AKIŞI & GELİR / GİDER TAKİBİ
# ---------------------------------------------------------
with tab4:
    st.subheader("💰 Nakit Akışı & Finansal Özet")
    
    df_f = st.session_state["finans"]
    
    # Finans Özet Metrikleri
    toplam_gelir = df_f[df_f["Tür"] == "Gelir"]["Tutar (TL)"].sum() if not df_f.empty else 0.0
    toplam_gider = df_f[df_f["Tür"] == "Gider"]["Tutar (TL)"].sum() if not df_f.empty else 0.0
    net_bakiye = toplam_gelir - toplam_gider
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Toplam Gelir", f"{toplam_gelir:,.2f} TL", delta_color="normal")
    col_m2.metric("Toplam Gider", f"{toplam_gider:,.2f} TL", delta_color="inverse")
    col_m3.metric("Net Bakiye (Kâr/Zarar)", f"{net_bakiye:,.2f} TL")
    
    st.divider()
    
    # Ekstra Gelir / Gider Ekleme Formu
    st.subheader("➕ Yeni Gelir / Gider Ekle")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        f_tur = st.selectbox("İşlem Türü", ["Gelir", "Gider"])
    with col_f2:
        f_kategori = st.selectbox("Kategori", ["Oda Konaklama", "Restoran/Kafe", "Personel Maaşı", "Fatura/Aidat", "Tedarik/Malzeme", "Diğer"])
    with col_f3:
        f_tutar = st.number_input("Tutar (TL)", min_value=0.0, value=100.0, step=50.0)
    with col_f4:
        f_tarih = st.date_input("İşlem Tarihi", value=date.today())
        
    f_aciklama = st.text_input("Açıklama (Örn: Mutfak alışverişi, Elektrik faturası vb.)")
    
    if st.button("Finans Kaydını Ekle", type="primary"):
        f_id = 1 if df_f.empty else int(df_f["ID"].max()) + 1
        yeni_finans_kaydi = pd.DataFrame([{
            "ID": f_id,
            "Tarih": f_tarih,
            "Tür": f_tur,
            "Kategori": f_kategori,
            "Açıklama": f_aciklama,
            "Tutar (TL)": f_tutar
        }])
        st.session_state["finans"] = pd.concat([df_f, yeni_finans_kaydi], ignore_index=True)
        st.success(f"✅ {f_tur} kaydı başarıyla eklendi!")
        st.rerun()

    st.divider()
    st.subheader("📊 Finans Hareketleri Listesi")
    if not df_f.empty:
        st.dataframe(df_f, use_container_width=True)
        
        # Finans Kaydı Silme
        st.subheader("🗑️ Finans Kaydı Sil")
        silinecek_f_id = st.selectbox(
            "Silmek istediğiniz finans kaydını seçin:",
            options=df_f["ID"].tolist(),
            format_func=lambda x: f"ID: {x} - {df_f[df_f['ID'] == x]['Tür'].values[0]}: {df_f[df_f['ID'] == x]['Açıklama'].values[0]} ({df_f[df_f['ID'] == x]['Tutar (TL)'].values[0]} TL)"
        )
        if st.button("Seçilen Finans Kaydını Sil"):
            st.session_state["finans"] = df_f[df_f["ID"] != silinecek_f_id].reset_index(drop=True)
            st.success(f"ID: {silinecek_f_id} numaralı işlem silindi!")
            st.rerun()
    else:
        st.info("Henüz kaydedilmiş bir gelir/gider hareketi bulunmuyor.")
