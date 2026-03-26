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

@st.cache_data(ttl=60) # Cache na 60 sekund
def load_sheet_data(worksheet_name):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(worksheet_name)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame()

def save_to_sheet(worksheet_name, row_data):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(worksheet_name)
        sheet.append_row(row_data)
        return True
    except: return False

def update_user_status(login, new_status):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Uzytkownicy")
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('Login')) == str(login):
                sheet.update_cell(i + 2, 4, new_status) # Kolumna D (4) to Status
                return True
        return False
    except: return False

def delete_user(login):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Uzytkownicy")
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('Login')) == str(login):
                sheet.delete_rows(i + 2) 
                return True
        return False
    except Exception as e:
        st.error(f"Błąd usuwania z bazy: {e}")
        return False

# =========================================================
# 2. INTERFEJS I STYLIZACJA (EXECUTIVE)
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
        h2, h3, h4 {{ color: #B58863 !important; text-transform: uppercase; letter-spacing: 3px !important; font-weight: 700 !important; }}
        .kpi-box {{
            background: rgba(20, 20, 20, 0.8); border: 1px solid rgba(181, 136, 99, 0.3);
            border-top: 4px solid #B58863; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 20px;
        }}
        .kpi-title {{ color: #B58863; font-size: 0.8rem; letter-spacing: 2px; font-weight: bold; margin-bottom: 10px; }}
        .kpi-value {{ color: #FFF; font-size: 2rem; font-family: 'JetBrains Mono', monospace; font-weight: bold; text-shadow: 0px 0px 10px rgba(181, 136, 99, 0.4); }}
        .kpi-sub {{ color: #AAA; font-size: 0.9rem; margin-top: 5px; }}
        .alert-value {{ color: #FF4B4B !important; text-shadow: 0px 0px 10px rgba(255,75,75,0.4); }}
        .user-card {{ background: rgba(30, 30, 30, 0.9); border: 1px solid #444; border-left: 4px solid #2980B9; padding: 15px; margin-bottom: 10px; border-radius: 6px; }}
        .user-blocked {{ border-left-color: #FF4B4B !important; opacity: 0.6; }}
        
        /* Przyciski usuwania */
        .btn-delete div[data-testid="stButton"] button {{
            border-color: #FF4B4B !important; color: #FF4B4B !important; background: transparent !important;
        }}
        .btn-delete div[data-testid="stButton"] button:hover {{
            background: #FF4B4B !important; color: #FFF !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 3. GŁÓWNA LOGIKA MODUŁU ADMINA
# =========================================================
def run_admin():
    apply_admin_theme()
    st.markdown("<h2>📈 VORTEZA EXECUTIVE | ANALITYKA BIZNESOWA</h2>", unsafe_allow_html=True)
    
    current_user = st.session_state.get("username", "OPERATOR")

    # --- NAWIGACJA WEWNĘTRZNA SZEFA ---
    admin_mode = st.radio("WYBIERZ SEKCJE:", ["📊 ANALITYKA BIZNESOWA", "👥 ZARZĄDZANIE PERSONELEM (Konta)"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    if admin_mode == "📊 ANALITYKA BIZNESOWA":
        with st.spinner("Pobieranie i analizowanie danych z centrali..."):
            df_zlecenia = load_sheet_data("Zlecenia")
            df_flota = load_sheet_data("Flota")
            df_przew = load_sheet_data("Przewoznicy")

        if df_zlecenia.empty:
            st.warning("Brak danych o zleceniach do analizy.")
            return

        df_zlecenia['Fracht_Sprzedaz'] = pd.to_numeric(df_zlecenia['Fracht_Sprzedaz'].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)
        df_zlecenia['Fracht_Kupno'] = pd.to_numeric(df_zlecenia['Fracht_Kupno'].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)
        df_zlecenia['Marza'] = df_zlecenia['Fracht_Sprzedaz'] - df_zlecenia['Fracht_Kupno']

        zlecenia_zakonczone = df_zlecenia[df_zlecenia['Status'].isin(['ZAKOŃCZONE', 'ZAMKNIĘTE'])]
        total_obrot = zlecenia_zakonczone['Fracht_Sprzedaz'].sum()
        total_marza = zlecenia_zakonczone['Marza'].sum()
        
        nieoplacone = zlecenia_zakonczone[zlecenia_zakonczone['StatusPlatnosci'].astype(str).str.strip().str.upper() == 'NIE']
        zamrozone_srodki = nieoplacone['Fracht_Sprzedaz'].sum()
        srednia_marza_pct = (total_marza / total_obrot * 100) if total_obrot > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='kpi-box'><div class='kpi-title'>CAŁKOWITY PRZYCHÓD</div><div class='kpi-value'>{total_obrot:,.2f}</div><div class='kpi-sub'>Zrealizowane i Zamknięte</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='kpi-box'><div class='kpi-title'>CZYSTY ZYSK (MARŻA)</div><div class='kpi-value' style='color:#00FF41;'>{total_marza:,.2f}</div><div class='kpi-sub'>Średnia rentowność: {srednia_marza_pct:.1f}%</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='kpi-box'><div class='kpi-title'>ZAMROŻONA GOTÓWKA</div><div class='kpi-value alert-value'>{zamrozone_srodki:,.2f}</div><div class='kpi-sub'>Z {len(nieoplacone)} nieopłaconych zleceń</div></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='kpi-box'><div class='kpi-title'>AKTYWNE ZLECENIA</div><div class='kpi-value' style='color:#3498DB;'>{len(df_zlecenia[df_zlecenia['Status'].isin(['ZAAKCEPTOWANE', 'ZAPLANOWANE', 'W TRASIE'])])}</div><div class='kpi-sub'>Obecnie procesowane</div></div>", unsafe_allow_html=True)

        st.markdown("---")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### 🥇 WYNIKI SPEDYTORÓW")
            if not zlecenia_zakonczone.empty:
                df_sped = zlecenia_zakonczone.groupby('Spedytor')['Marza'].sum().reset_index().sort_values(by='Marza', ascending=False)
                fig_sped = px.bar(df_sped, x='Spedytor', y='Marza', text='Marza', template="plotly_dark", color_discrete_sequence=['#B58863'])
                fig_sped.update_traces(texttemplate='%{text:,.2f}', textposition='outside')
                fig_sped.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_sped, use_container_width=True)

        with col_b:
            st.markdown("### 💼 TOP KLIENCI")
            if not zlecenia_zakonczone.empty:
                df_klienci = zlecenia_zakonczone.groupby('Klient')[['Fracht_Sprzedaz', 'Marza']].sum().reset_index().sort_values(by='Fracht_Sprzedaz', ascending=False).head(5)
                fig_klienci = px.bar(df_klienci, x='Klient', y=['Fracht_Sprzedaz', 'Marza'], barmode='group', template="plotly_dark", color_discrete_sequence=['#3498DB', '#00FF41'])
                fig_klienci.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', legend_title_text='Parametr')
                st.plotly_chart(fig_klienci, use_container_width=True)

        st.markdown("---")

        col_c, col_d = st.columns(2)
        with col_c:
            st.markdown("### 🚚 RENTOWNOŚĆ TRAKCJI")
            if not zlecenia_zakonczone.empty:
                df_trakcja = zlecenia_zakonczone.groupby('Trakcja')['Marza'].sum().reset_index()
                fig_trakcja = px.pie(df_trakcja, names='Trakcja', values='Marza', hole=0.4, template="plotly_dark", color_discrete_sequence=['#B58863', '#3498DB'])
                fig_trakcja.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_trakcja, use_container_width=True)

        with col_d:
            st.markdown("### 🛣️ ZŁOTE TRASY")
            if not zlecenia_zakonczone.empty:
                df_trasy = zlecenia_zakonczone.copy()
                df_trasy['Relacja'] = df_trasy['Start'] + " ➔ " + df_trasy['Koniec']
                df_trasy_grp = df_trasy.groupby('Relacja')['Marza'].sum().reset_index().sort_values(by='Marza', ascending=False).head(5)
                fig_trasy = px.bar(df_trasy_grp, y='Relacja', x='Marza', orientation='h', text='Marza', template="plotly_dark", color_discrete_sequence=['#27AE60'])
                fig_trasy.update_traces(texttemplate='%{text:,.2f}', textposition='inside')
                fig_trasy.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_trasy, use_container_width=True)

        st.markdown("---")
        col_e, col_f = st.columns(2)
        with col_e:
            st.markdown("### 💸 RANKING PRZEWOŹNIKÓW")
            df_obcy = zlecenia_zakonczone[zlecenia_zakonczone['Trakcja'] == 'PODWYKONAWCA (PRZEWOŹNIK)']
            if not df_obcy.empty:
                df_przew_grp = df_obcy.groupby('Przewoznik').agg(Ilosc_Zlecen=('ID', 'count'), Suma_Kosztow=('Fracht_Kupno', 'sum')).reset_index().sort_values(by='Suma_Kosztow', ascending=False)
                st.dataframe(df_przew_grp, hide_index=True, use_container_width=True)

        with col_f:
            st.markdown("### 🔧 STATYSTYKI FLOTY WŁASNEJ")
            if not df_flota.empty:
                df_flota['Przebieg'] = pd.to_numeric(df_flota['Przebieg'], errors='coerce').fillna(0)
                df_flota_grp = df_flota.groupby('Pojazd').agg(Inspekcje=('Data', 'count'), Max_Przebieg_KM=('Przebieg', 'max')).reset_index().sort_values(by='Max_Przebieg_KM', ascending=False)
                st.dataframe(df_flota_grp, hide_index=True, use_container_width=True)

    # --------------------------------------------------------------------------------
    # ZAKŁADKA 2: ZARZĄDZANIE UŻYTKOWNIKAMI
    # --------------------------------------------------------------------------------
    elif admin_mode == "👥 ZARZĄDZANIE PERSONELEM (Konta)":
        st.markdown("### 🔐 KREATOR KONT I DOSTĘPÓW")
        
        with st.form("new_user_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            new_login = col1.text_input("NAZWA UŻYTKOWNIKA (Login)")
            new_haslo = col2.text_input("HASŁO", type="password")
            new_rola = col3.selectbox("ROLA W SYSTEMIE", ["SPEDYTOR / LOGISTYKA", "KIEROWCA", "ADMINISTRATOR / SZEF"])
            
            if st.form_submit_button("➕ UTWÓRZ KONTO", use_container_width=True):
                if new_login and new_haslo:
                    df_check = load_sheet_data("Uzytkownicy")
                    if not df_check.empty and new_login.lower() in df_check['Login'].astype(str).str.lower().values:
                        st.error("Użytkownik o takim loginie już istnieje!")
                    elif save_to_sheet("Uzytkownicy", [new_login, new_haslo, new_rola, "AKTYWNY"]):
                        st.success(f"Konto dla {new_login} zostało utworzone!"); st.rerun()
                    else: st.error("Błąd zapisu w bazie danych.")
                else: st.error("Wypełnij Login i Hasło!")

        st.markdown("---")
        st.markdown("### 📋 LISTA AKTYWNYCH KONT")
        df_users = load_sheet_data("Uzytkownicy")
        
        if df_users.empty:
            st.info("Brak użytkowników w bazie. Utwórz pierwsze konto powyżej.")
        else:
            for _, row in df_users.iterrows():
                login = str(row.get('Login', ''))
                rola = str(row.get('Rola', ''))
                status = str(row.get('Status', 'AKTYWNY'))
                
                css_class = "user-card" if status == "AKTYWNY" else "user-card user-blocked"
                status_color = "#00FF41" if status == "AKTYWNY" else "#FF4B4B"
                
                st.markdown(f"""
                    <div class="{css_class}">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span style="color:#FFF; font-size:1.2rem; font-weight:bold;">{login}</span><br>
                                <span style="color:#B58863; font-size:0.9rem;">{rola}</span>
                            </div>
                            <div style="text-align:right;">
                                <span style="color:{status_color}; font-weight:bold; font-family:'JetBrains Mono';">STATUS: {status}</span>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # --- ZMIANA UKŁADU PRZYCISKÓW ---
                # Używamy proporcji 2:5:2, co daje szeroki środek, spychając "Usuń" do prawej
                col_btn_blk, _, col_btn_del = st.columns([2, 5, 2])
                
                with col_btn_blk:
                    if status == "AKTYWNY":
                        if login.lower() != "piotr" and login.lower() != current_user.lower():
                            if st.button("🚫 ZABLOKUJ", key=f"blk_{login}", use_container_width=True):
                                update_user_status(login, "ZABLOKOWANY"); st.rerun()
                    else:
                        if st.button("✅ ODBLOKUJ", key=f"unb_{login}", use_container_width=True):
                            update_user_status(login, "AKTYWNY"); st.rerun()
                
                with col_btn_del:
                    if login.lower() != "piotr" and login.lower() != current_user.lower():
                        st.markdown("<div class='btn-delete'>", unsafe_allow_html=True)
                        if st.button("🗑️ USUŃ", key=f"del_{login}", use_container_width=True):
                            if delete_user(login):
                                st.success("Konto usunięte!"); st.rerun()
                            else:
                                st.error("Błąd usuwania.")
                        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    run_admin()
