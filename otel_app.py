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

ODALAR = ["101 - Delüks Oda", "102 - Manzaralı Suit", "103 - Standart Oda", "104 - Aile Odası"]
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
                st.error(f"⛔ **{secilen_oda}** seçtiğiniz **{giris_tarihi.strftime('%d.%m.%Y')} - {cikis_tarihi.strftime('%d.%m.%Y')}** tarihleri arasında ZATEN DOLU!")
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
# TAB 4: NAKİT AKIŞI & GRUPLAR TOPLAMI (HER DURUMDA ÇALIŞIR)
# ---------------------------------------------------------
with tab4:
    st.subheader("💰 Nakit Akışı & Sınıf/Kategori Grupları")
    
    df_f = st.session_state["finans"]
    
    # Genel Metrik Hesaplamaları
    if not df_f.empty:
        toplam_gelir = float(df_f[df_f["Tür"] == "Gelir"]["Tutar (TL)"].sum())
        toplam_gider = float(df_f[df_f["Tür"] == "Gider"]["Tutar (TL)"].sum())
    else:
        toplam_gelir = 0.0
        toplam_gider = 0.0
        
    net_bakiye = toplam_gelir - toplam_gider
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Toplam Gelir", f"{toplam_gelir:,.2f} TL")
    col_m2.metric("Toplam Gider", f"{toplam_gider:,.2f} TL")
    col_m3.metric("Net Bakiye (Kâr / Zarar)", f"{net_bakiye:,.2f} TL")
    
    st.divider()
    
    # Kategori Grupları Gösterimi
    st.subheader("📊 Sınıf / Kategori Bazında Toplamlar")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("#### 🟢 Gelir Grupları")
        if not df_f.empty and not df_f[df_f["Tür"] == "Gelir"].empty:
            gelir_ozet = df_f[df_f["Tür"] == "Gelir"].groupby("Kategori")["Tutar (TL)"].sum().reset_index()
            st.dataframe(gelir_ozet, use_container_width=True)
        else:
            st.info("Henüz kaydedilmiş gelir bulunmuyor.")
            
    with col_g2:
        st.markdown("#### 🔴 Gider Grupları (Maaş, Fatura vb.)")
        if not df_f.empty and not df_f[df_f["Tür"] == "Gider"].empty:
            gider_ozet = df_f[df_f["Tür"] == "Gider"].groupby("Kategori")["Tutar (TL)"].sum().reset_index()
            st.dataframe(gider_ozet, use_container_width=True)
        else:
            st.info("Henüz kaydedilmiş gider bulunmuyor.")

    st.divider()
    
    # Manuel Gelir / Gider Ekleme Formu
    st.subheader("➕ Yeni Gelir / Gider Ekle")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        f_tur = st.selectbox("İşlem Türü", ["Gelir", "Gider"], key="f_tur_input")
    with col_f2:
        f_kategori = st.selectbox("Kategori", KATEGORILER, key="f_kat_input")
    with col_f3:
        f_tutar = st.number_input("Tutar (TL)", min_value=0.0, value=500.0, step=100.0, key="f_tut_input")
    with col_f4:
        f_tarih = st.date_input("İşlem Tarihi", value=date.today(), key="f_tar_input")
        
    f_aciklama = st.text_input("Açıklama (Örn: Personel maaşı, Elektrik faturası vb.)", key="f_ack_input")
    
    if st.button("Finans Kaydını Ekle", type="primary"):
        f_id = 1 if df_f.empty else int(df_f["ID"].max()) + 1
        yeni_finans_kaydi = pd.DataFrame([{
            "ID": f_id,
            "Tarih": f_tarih,
            "Tür": f_tur,
            "Kategori": f_kategori,
            "Açıklama": f_aciklama if f_aciklama.strip() else f_kategori,
            "Tutar (TL)": f_tutar
        }])
        st.session_state["finans"] = pd.concat([df_f, yeni_finans_kaydi], ignore_index=True)
        st.success(f"✅ {f_tur} kaydı eklendi!")
        st.rerun()

    st.divider()
    st.subheader("📋 Tüm Finans Hareketleri")
    if not df_f.empty:
        st.dataframe(df_f, use_container_width=True)
        
        silinecek_f_id = st.selectbox(
            "Silinecek İşlemi Seçin:",
            options=df_f["ID"].tolist(),
            format_func=lambda x: f"ID: {x} - {df_f[df_f['ID'] == x]['Tür'].values[0]}: {df_f[df_f['ID'] == x]['Açıklama'].values[0]} ({df_f[df_f['ID'] == x]['Tutar (TL)'].values[0]} TL)"
        )
        if st.button("Seçilen Finans Kaydını Sil"):
            st.session_state["finans"] = df_f[df_f["ID"] != silinecek_f_id].reset_index(drop=True)
            st.success("İşlem silindi!")
            st.rerun()

# ---------------------------------------------------------
# TAB 5: BÜTÇE & HEDEF PLANLAMA TABI
# ---------------------------------------------------------
with tab5:
    st.subheader("🎯 Bütçe & Hedef Nakit Akışı Planlama")
    st.caption("Kategoriler bazında hedef bütçenizi belirleyin ve gerçekleşen durumla karşılaştırın.")
    
    df_b = st.session_state["butce"]
    df_f = st.session_state["finans"]
    
    # Bütçe Tanımlama Formu
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        b_tur = st.selectbox("Bütçe Türü", ["Gelir", "Gider"], key="b_tur_select")
    with col_b2:
        b_kategori = st.selectbox("Kategori Seçin", KATEGORILER, key="b_kat_select")
    with col_b3:
        b_hedef = st.number_input("Hedef / Limit Tutar (TL)", min_value=0.0, value=5000.0, step=500.0, key="b_hed_select")
        
    if st.button("Hedef Bütçe Ekle / Güncelle", type="primary"):
        # Eski aynı kategori varsa temizle
        if not df_b.empty:
            df_b = df_b[~(df_b["Kategori"] == b_kategori)]
            
        b_id = 1 if df_b.empty else int(df_b["ID"].max()) + 1
        yeni_b = pd.DataFrame([{
            "ID": b_id,
            "Tür": b_tur,
            "Kategori": b_kategori,
            "Hedef Bütçe (TL)": b_hedef
        }])
        st.session_state["butce"] = pd.concat([df_b, yeni_b], ignore_index=True)
        st.success(f"✅ {b_kategori} kategorisi için bütçe hedefi güncellendi!")
        st.rerun()

    st.divider()
    st.subheader("📊 Bütçe vs. Gerçekleşen Durum Tablosu")
    
    if not df_b.empty:
        karsilastirma = []
        for _, row in df_b.iterrows():
            kat = row["Kategori"]
            tur = row["Tür"]
            hedef = row["Hedef Bütçe (TL)"]
            
            # Gerçekleşen tutarları güvenli şekilde çekme
            if not df_f.empty:
                f_filtrelenmis = df_f[(df_f["Kategori"] == kat) & (df_f["Tür"] == tur)]
                gercekleseni = float(f_filtrelenmis["Tutar (TL)"].sum()) if not f_filtrelenmis.empty else 0.0
            else:
                gercekleseni = 0.0
                
            fark = gercekleseni - hedef if tur == "Gelir" else hedef - gercekleseni
            
            karsilastirma.append({
                "Tür": tur,
                "Kategori": kat,
                "Hedef Bütçe (TL)": hedef,
                "Gerçekleşen (TL)": gercekleseni,
                "Fark / Kalan (TL)": fark,
                "Durum": "✅ Hedef İçi / Başarılı" if fark >= 0 else "⚠️ Limit Aşıldı / Hedef Altı"
            })
            
        st.dataframe(pd.DataFrame(karsilastirma), use_container_width=True)
    else:
        st.info("Henüz bütçe hedefi eklenmedi. Yukarıdaki formdan kategorileriniz için bütçe hedefleri tanımlayabilirsiniz.")
