# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import base64
from google.oauth2.service_account import Credentials
import gspread

# =========================================================
# 1. KONFIGURACJA ŚCIEŻEK I BAZY DANYCH
# =========================================================
PATH_BG = os.path.join("assets", "tlo_hub_2.jpg")
SHEET_ID = "1Arq4WTFcvbvH7JkMEMWpWkGjaN44J4UpgJ2T9lKQLn8"

def load_vorteza_asset_b64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        return ""
    except: return ""

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_info = st.secrets["GCP_SERVICE_ACCOUNT"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(credentials)

@st.cache_data(ttl=60) # Cache na 60 sekund, żeby nie zajechać API Google
def load_sheet_data(worksheet_name):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(worksheet_name)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame()

# =========================================================
# 2. INTERFEJS I STYLIZACJA (GOD MODE)
# =========================================================
def apply_admin_theme():
    bg_data = load_vorteza_asset_b64(PATH_BG)
    bg_style = f"""
        .stApp {{
            background: linear-gradient(rgba(6, 6, 6, 0.95), rgba(6, 6, 6, 0.95)), 
                        url("data:image/jpeg;base64,{bg_data}") !important;
            background-size: cover !important; background-attachment: fixed !important;
        }}
    """ if bg_data else ".stApp { background-color: #060606 !important; }"

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;700&family=JetBrains+Mono&display=swap');
        {bg_style}
        h2, h3, h4 {{ color: #D4AF37 !important; text-transform: uppercase; letter-spacing: 3px !important; font-weight: 700 !important; }}
        .kpi-box {{
            background: rgba(20, 20, 20, 0.8); border: 1px solid rgba(212, 175, 55, 0.3);
            border-top: 4px solid #D4AF37; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 20px;
        }}
        .kpi-title {{ color: #D4AF37; font-size: 0.8rem; letter-spacing: 2px; font-weight: bold; margin-bottom: 10px; }}
        .kpi-value {{ color: #FFF; font-size: 2rem; font-family: 'JetBrains Mono', monospace; font-weight: bold; text-shadow: 0px 0px 10px rgba(212,175,55,0.4); }}
        .kpi-sub {{ color: #AAA; font-size: 0.9rem; margin-top: 5px; }}
        .alert-value {{ color: #FF4B4B !important; text-shadow: 0px 0px 10px rgba(255,75,75,0.4); }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 3. GŁÓWNA LOGIKA MODUŁU ADMINA
# =========================================================
def run_admin():
    apply_admin_theme()
    st.markdown("<h2>👑 GOD MODE | CENTRUM DOWODZENIA SZEFA</h2>", unsafe_allow_html=True)

    with st.spinner("Pobieranie i mielenie danych z centrali..."):
        df_zlecenia = load_sheet_data("Zlecenia")
        df_flota = load_sheet_data("Flota")
        df_przew = load_sheet_data("Przewoznicy")

    if df_zlecenia.empty:
        st.warning("Brak danych o zleceniach do analizy.")
        return

    # --- CZYSZCZENIE DANYCH (Mielenie stringów na liczby) ---
    df_zlecenia['Fracht_Sprzedaz'] = pd.to_numeric(df_zlecenia['Fracht_Sprzedaz'].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)
    df_zlecenia['Fracht_Kupno'] = pd.to_numeric(df_zlecenia['Fracht_Kupno'].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)
    df_zlecenia['Marza'] = df_zlecenia['Fracht_Sprzedaz'] - df_zlecenia['Fracht_Kupno']

    # --- KPI: GŁÓWNE LICZBY ---
    zlecenia_zakonczone = df_zlecenia[df_zlecenia['Status'].isin(['ZAKOŃCZONE', 'ZAMKNIĘTE'])]
    total_obrot = zlecenia_zakonczone['Fracht_Sprzedaz'].sum()
    total_marza = zlecenia_zakonczone['Marza'].sum()
    
    # Obliczanie zamrożonej gotówki (Kasa na fakturach nieopłaconych)
    nieoplacone = zlecenia_zakonczone[zlecenia_zakonczone['StatusPlatnosci'].astype(str).str.strip().str.upper() == 'NIE']
    zamrozone_srodki = nieoplacone['Fracht_Sprzedaz'].sum()
    
    # Skuteczność spedycyjna (Średnia marża %)
    srednia_marza_pct = (total_marza / total_obrot * 100) if total_obrot > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='kpi-box'><div class='kpi-title'>CAŁKOWITY PRZYCHÓD</div><div class='kpi-value'>{total_obrot:,.2f}</div><div class='kpi-sub'>Zrealizowane i Zamknięte</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='kpi-box'><div class='kpi-title'>CZYSTY ZYSK (MARŻA)</div><div class='kpi-value' style='color:#00FF41;'>{total_marza:,.2f}</div><div class='kpi-sub'>Średnia rentowność: {srednia_marza_pct:.1f}%</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='kpi-box'><div class='kpi-title'>ZAMROŻONA GOTÓWKA</div><div class='kpi-value alert-value'>{zamrozone_srodki:,.2f}</div><div class='kpi-sub'>Z {len(nieoplacone)} nieopłaconych zleceń</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='kpi-box'><div class='kpi-title'>AKTYWNE ZLECENIA</div><div class='kpi-value' style='color:#3498DB;'>{len(df_zlecenia[df_zlecenia['Status'].isin(['ZAAKCEPTOWANE', 'ZAPLANOWANE', 'W TRASIE'])])}</div><div class='kpi-sub'>Obecnie procesowane</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- WERS OPIERAJĄCY SIĘ NA SPEDYTORACH I KLIENTACH ---
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("### 🥇 WYNIKI SPEDYTORÓW (GENEROWANA MARŻA)")
        if not zlecenia_zakonczone.empty:
            df_sped = zlecenia_zakonczone.groupby('Spedytor')['Marza'].sum().reset_index().sort_values(by='Marza', ascending=False)
            fig_sped = px.bar(df_sped, x='Spedytor', y='Marza', text='Marza', template="plotly_dark", color_discrete_sequence=['#D4AF37'])
            fig_sped.update_traces(texttemplate='%{text:,.2f}', textposition='outside')
            fig_sped.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_sped, use_container_width=True)
        else: st.info("Brak zamkniętych zleceń do oceny spedytorów.")

    with col_b:
        st.markdown("### 💼 TOP KLIENCI (PRZYCHÓD VS ZYSK)")
        if not zlecenia_zakonczone.empty:
            df_klienci = zlecenia_zakonczone.groupby('Klient')[['Fracht_Sprzedaz', 'Marza']].sum().reset_index().sort_values(by='Fracht_Sprzedaz', ascending=False).head(5)
            fig_klienci = px.bar(df_klienci, x='Klient', y=['Fracht_Sprzedaz', 'Marza'], barmode='group', template="plotly_dark", color_discrete_sequence=['#3498DB', '#00FF41'])
            fig_klienci.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', legend_title_text='Parametr')
            st.plotly_chart(fig_klienci, use_container_width=True)
        else: st.info("Brak zamkniętych zleceń.")

    st.markdown("---")

    # --- WERS OPIERAJĄCY SIĘ NA KOSZTACH FLOTY I TRASACH ---
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("### 🚚 RENTOWNOŚĆ TRAKCJI (WŁASNA VS OBCY)")
        if not zlecenia_zakonczone.empty:
            df_trakcja = zlecenia_zakonczone.groupby('Trakcja')['Marza'].sum().reset_index()
            fig_trakcja = px.pie(df_trakcja, names='Trakcja', values='Marza', hole=0.4, template="plotly_dark", color_discrete_sequence=['#E67E22', '#8E44AD'])
            fig_trakcja.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_trakcja, use_container_width=True)

    with col_d:
        st.markdown("### 🛣️ ZŁOTE TRASY (TOP MARŻA)")
        if not zlecenia_zakonczone.empty:
            df_trasy = zlecenia_zakonczone.copy()
            df_trasy['Relacja'] = df_trasy['Start'] + " ➔ " + df_trasy['Koniec']
            df_trasy_grp = df_trasy.groupby('Relacja')['Marza'].sum().reset_index().sort_values(by='Marza', ascending=False).head(5)
            fig_trasy = px.bar(df_trasy_grp, y='Relacja', x='Marza', orientation='h', text='Marza', template="plotly_dark", color_discrete_sequence=['#27AE60'])
            fig_trasy.update_traces(texttemplate='%{text:,.2f}', textposition='inside')
            fig_trasy.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_trasy, use_container_width=True)

    st.markdown("---")

    # --- TABELE SZCZEGÓŁOWE ---
    col_e, col_f = st.columns(2)

    with col_e:
        st.markdown("### 💸 RANKING PRZEWOŹNIKÓW (KOSZTY)")
        st.caption("Komu zlecamy najwięcej i ile im płacimy?")
        df_obcy = zlecenia_zakonczone[zlecenia_zakonczone['Trakcja'] == 'PODWYKONAWCA (PRZEWOŹNIK)']
        if not df_obcy.empty:
            df_przew_grp = df_obcy.groupby('Przewoznik').agg(Ilosc_Zlecen=('ID', 'count'), Suma_Kosztow=('Fracht_Kupno', 'sum')).reset_index().sort_values(by='Suma_Kosztow', ascending=False)
            st.dataframe(df_przew_grp, hide_index=True, use_container_width=True)
        else: st.info("Brak zleceń zewnętrznych.")

    with col_f:
        st.markdown("### 🔧 STATYSTYKI FLOTY WŁASNEJ")
        st.caption("Ilość zgłoszonych inspekcji i ostatnio odnotowane przebiegi.")
        if not df_flota.empty:
            # Grupujemy po pojeździe i wyciągamy max przebieg oraz ilość zgłoszeń
            df_flota['Przebieg'] = pd.to_numeric(df_flota['Przebieg'], errors='coerce').fillna(0)
            df_flota_grp = df_flota.groupby('Pojazd').agg(Inspekcje=('Data', 'count'), Max_Przebieg_KM=('Przebieg', 'max')).reset_index().sort_values(by='Max_Przebieg_KM', ascending=False)
            st.dataframe(df_flota_grp, hide_index=True, use_container_width=True)
        else: st.info("Brak logów floty.")

if __name__ == "__main__":
    run_admin()
