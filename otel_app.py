import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import os

st.set_page_config(page_title="Butik Otel Paneli", layout="wide")

# --- KALICI VERİ DEPOLAMA (CSV) FONKSİYONLARI ---
REZ_FILE = "rezervasyonlar.csv"
FINANS_FILE = "finans.csv"
BUTCE_FILE = "butce.csv"

def load_data(file_path, columns):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            # Tarih kolonlarını doğru veri tipine dönüştür
            for col in df.columns:
                if "Tarih" in col:
                    df[col] = pd.to_datetime(df[col]).dt.date
            return df
        except Exception:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# --- TUTAR FORMATLAMA FONKSİYONU ---
def format_tl(val, kurus=False):
    try:
        val = float(val)
        if kurus:
            return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return f"{val:,.0f}".replace(",", ".")
    except:
        return str(val)

# --- KULLANICI GİRİŞ KONTROLÜ ---
USERS = {
    "admin": "yigido58"
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Butik Otel Paneli Girişi")
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap", type="primary"):
        if username in USERS and USERS[username] == password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Hatalı kullanıcı adı veya şifre!")
    st.stop()

# --- HEADER & ÇIKIŞ BUTONU ---
col_head1, col_head2 = st.columns([8, 2])
with col_head1:
    st.title("🏨 Butik Otel Yönetim Paneli")
with col_head2:
    st.write("") 
    if st.button("🔴 Oturumu Kapat", type="secondary"):
        st.session_state["authenticated"] = False
        st.rerun()

st.divider()

# --- KALICI VERİLERİ YÜKLEME ---
REZ_COLS = ["ID", "Müşteri Adı", "Oda No", "Giriş Tarihi", "Çıkış Tarihi", "Ücret (TL)"]
FINANS_COLS = ["ID", "Tarih", "Tür", "Kategori", "Açıklama", "Tutar (TL)"]
BUTCE_COLS = ["ID", "Tür", "Kategori", "Hedef Bütçe (TL)"]

if "rezervasyonlar" not in st.session_state:
    st.session_state["rezervasyonlar"] = load_data(REZ_FILE, REZ_COLS)

if "finans" not in st.session_state:
    st.session_state["finans"] = load_data(FINANS_FILE, FINANS_COLS)

if "butce" not in st.session_state:
    st.session_state["butce"] = load_data(BUTCE_FILE, BUTCE_COLS)

ODALAR = ["111", "222", "333", "444", "555", "666", "777", "888"]
KATEGORILER = ["Oda Konaklama", "Restoran/Kafe", "Personel Maaşı", "Kira", "Fatura/Aidat", "Tedarik/Malzeme", "Diğer"]

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
        ucret = st.number_input("Konaklama Ücreti (TL)", min_value=0, value=20000, step=500, format="%d")
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
                save_data(st.session_state["rezervasyonlar"], REZ_FILE)
                
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
                save_data(st.session_state["finans"], FINANS_FILE)
                
                st.success(f"✅ Oda {secilen_oda} için {musteri} adına rezervasyon ve {format_tl(ucret)} TL gelir başarıyla kaydedildi!")

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
        gosterim_df = df.copy()
        gosterim_df["Ücret (TL)"] = gosterim_df["Ücret (TL)"].apply(lambda x: format_tl(x))
        st.dataframe(gosterim_df, use_container_width=True)
        st.divider()
        st.subheader("🗑️ Rezervasyon Sil")
        
        silinecek_id = st.selectbox(
            "Silmek istediğiniz rezervasyon kaydını seçin:",
            options=df["ID"].tolist(),
            format_func=lambda x: f"ID: {x} - Müşteri: {df[df['ID'] == x]['Müşteri Adı'].values[0]} (Oda: {df[df['ID'] == x]['Oda No'].values[0]})"
        )
        
        if st.button("Seçilen Rezervasyonu Sil", type="secondary"):
            st.session_state["rezervasyonlar"] = df[df["ID"] != silinecek_id].reset_index(drop=True)
            save_data(st.session_state["rezervasyonlar"], REZ_FILE)
            st.success(f"ID: {silinecek_id} numaralı rezervasyon başarıyla silindi!")
            st.rerun()
    else:
        st.info("Sistemde henüz kayıtlı bir rezervasyon bulunmuyor.")

# ---------------------------------------------------------
# TAB 4: NAKİT AKIŞI & GRUPLAR TOPLAMI
# ---------------------------------------------------------
with tab4:
    st.subheader("💰 Nakit Akışı & Sınıf/Kategori Grupları")
    
    df_f = st.session_state["finans"]
    
    toplam_gelir = float(df_f[df_f["Tür"] == "Gelir"]["Tutar (TL)"].sum()) if not df_f.empty else 0.0
    toplam_gider = float(df_f[df_f["Tür"] == "Gider"]["Tutar (TL)"].sum()) if not df_f.empty else 0.0
    net_bakiye = toplam_gelir - toplam_gider
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Toplam Gelir", f"{format_tl(toplam_gelir)} TL")
    col_m2.metric("Toplam Gider", f"{format_tl(toplam_gider)} TL")
    col_m3.metric("Net Bakiye (Kâr / Zarar)", f"{format_tl(net_bakiye)} TL")
    
    st.divider()
    
    st.subheader("📊 Sınıf / Kategori Bazında Toplamlar")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("#### 🟢 Gelir Grupları")
        if not df_f.empty and not df_f[df_f["Tür"] == "Gelir"].empty:
            gelir_ozet = df_f[df_f["Tür"] == "Gelir"].groupby("Kategori")["Tutar (TL)"].sum().reset_index()
            toplam_row = pd.DataFrame([{"Kategori": "📌 GENEL TOPLAM", "Tutar (TL)": gelir_ozet["Tutar (TL)"].sum()}])
            gelir_ozet = pd.concat([gelir_ozet, toplam_row], ignore_index=True)
            gelir_ozet["Tutar (TL)"] = gelir_ozet["Tutar (TL)"].apply(lambda x: format_tl(x))
            st.dataframe(gelir_ozet, use_container_width=True)
        else:
            st.info("Henüz kaydedilmiş gelir bulunmuyor.")
            
    with col_g2:
        st.markdown("#### 🔴 Gider Grupları")
        if not df_f.empty and not df_f[df_f["Tür"] == "Gider"].empty:
            gider_ozet = df_f[df_f["Tür"] == "Gider"].groupby("Kategori")["Tutar (TL)"].sum().reset_index()
            toplam_row = pd.DataFrame([{"Kategori": "📌 GENEL TOPLAM", "Tutar (TL)": gider_ozet["Tutar (TL)"].sum()}])
            gider_ozet = pd.concat([gider_ozet, toplam_row], ignore_index=True)
            gider_ozet["Tutar (TL)"] = gider_ozet["Tutar (TL)"].apply(lambda x: format_tl(x))
            st.dataframe(gider_ozet, use_container_width=True)
        else:
            st.info("Henüz kaydedilmiş gider bulunmuyor.")

    st.divider()
    
    st.subheader("➕ Yeni Gelir / Gider Ekle")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        f_tur = st.selectbox("İşlem Türü", ["Gelir", "Gider"], key="f_tur_input")
    with col_f2:
        f_kategori = st.selectbox("Kategori", KATEGORILER, key="f_kat_input")
    with col_f3:
        f_tutar = st.number_input("Tutar (TL)", min_value=0, value=5000, step=500, format="%d", key="f_tut_input")
    with col_f4:
        f_tarih = st.date_input("İşlem Tarihi", value=date.today(), key="f_tar_input")
        
    f_aciklama = st.text_input("Açıklama (Örn: Kira ödemesi, Elektrik faturası vb.)", key="f_ack_input")
    
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
        save_data(st.session_state["finans"], FINANS_FILE)
        st.success(f"✅ {f_tur} kaydı eklendi!")
        st.rerun()

    st.divider()
    st.subheader("📋 Tüm Finans Hareketleri")
    if not df_f.empty:
        gosterim_finans = df_f.copy()
        gosterim_finans["Tutar (TL)"] = gosterim_finans["Tutar (TL)"].apply(lambda x: format_tl(x))
        st.dataframe(gosterim_finans, use_container_width=True)
        
        silinecek_f_id = st.selectbox(
            "Silinecek İşlemi Seçin:",
            options=df_f["ID"].tolist(),
            format_func=lambda x: f"ID: {x} - {df_f[df_f['ID'] == x]['Tür'].values[0]}: {df_f[df_f['ID'] == x]['Açıklama'].values[0]} ({format_tl(df_f[df_f['ID'] == x]['Tutar (TL)'].values[0])} TL)"
        )
        if st.button("Seçilen Finans Kaydını Sil"):
            st.session_state["finans"] = df_f[df_f["ID"] != silinecek_f_id].reset_index(drop=True)
            save_data(st.session_state["finans"], FINANS_FILE)
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
    
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        b_tur = st.selectbox("Bütçe Türü", ["Gelir", "Gider"], key="b_tur_select")
    with col_b2:
        b_kategori = st.selectbox("Kategori Seçin", KATEGORILER, key="b_kat_select")
    with col_b3:
        b_hedef = st.number_input("Hedef / Limit Tutar (TL)", min_value=0, value=20000, step=1000, format="%d", key="b_hed_select")
        
    if st.button("Hedef Bütçe Ekle / Güncelle", type="primary"):
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
        save_data(st.session_state["butce"], BUTCE_FILE)
        st.success(f"✅ {b_kategori} kategorisi için bütçe hedefi güncellendi!")
        st.rerun()

    st.divider()
    st.subheader("📊 Bütçe vs. Gerçekleşen Durum Tablosu")
    
    if not df_b.empty:
        karsilastirma = []
        tot_hedef = 0.0
        tot_gercekleseni = 0.0
        
        for _, row in df_b.iterrows():
            kat = row["Kategori"]
            tur = row["Tür"]
            hedef = float(row["Hedef Bütçe (TL)"])
            
            if not df_f.empty:
                f_filtrelenmis = df_f[(df_f["Kategori"] == kat) & (df_f["Tür"] == tur)]
                gercekleseni = float(f_filtrelenmis["Tutar (TL)"].sum()) if not f_filtrelenmis.empty else 0.0
            else:
                gercekleseni = 0.0
                
            fark = gercekleseni - hedef if tur == "Gelir" else hedef - gercekleseni
            
            tot_hedef += hedef
            tot_gercekleseni += gercekleseni
            
            karsilastirma.append({
                "ID": row["ID"],
                "Tür": tur,
                "Kategori": kat,
                "Hedef Bütçe (TL)": format_tl(hedef),
                "Gerçekleşen (TL)": format_tl(gercekleseni),
                "Fark / Kalan (TL)": format_tl(fark),
                "Durum": "✅ Hedef İçi / Başarılı" if fark >= 0 else "⚠️ Limit Aşıldı / Hedef Altı"
            })
            
        karsilastirma_df = pd.DataFrame(karsilastirma)
        tot_fark = tot_gercekleseni - tot_hedef
        toplam_satir = pd.DataFrame([{
            "ID": "-",
            "Tür": "-",
            "Kategori": "📌 GENEL TOPLAM",
            "Hedef Bütçe (TL)": format_tl(tot_hedef),
            "Gerçekleşen (TL)": format_tl(tot_gercekleseni),
            "Fark / Kalan (TL)": format_tl(tot_fark),
            "Durum": "📊 Genel Özet"
        }])
        
        karsilastirma_df = pd.concat([karsilastirma_df, toplam_satir], ignore_index=True)
        st.dataframe(karsilastirma_df, use_container_width=True)
        
        st.divider()
        st.subheader("🗑️ Hatalı Bütçe Hedefini Sil")
        silinecek_b_id = st.selectbox(
            "Silmek istediğiniz bütçe kalemini seçin:",
            options=df_b["ID"].tolist(),
            format_func=lambda x: f"ID: {x} - {df_b[df_b['ID'] == x]['Tür'].values[0]}: {df_b[df_b['ID'] == x]['Kategori'].values[0]} ({format_tl(df_b[df_b['ID'] == x]['Hedef Bütçe (TL)'].values[0])} TL)"
        )
        if st.button("Seçilen Bütçe Kalemini Sil"):
            st.session_state["butce"] = df_b[df_b["ID"] != silinecek_b_id].reset_index(drop=True)
            save_data(st.session_state["butce"], BUTCE_FILE)
            st.success("Bütçe kalemi başarıyla silindi!")
            st.rerun()
    else:
        st.info("Henüz bütçe hedefi eklenmedi. Yukarıdaki formdan kategorileriniz için bütçe hedefleri tanımlayabilirsiniz.")
