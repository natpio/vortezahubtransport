# -*- coding: utf-8 -*-
import streamlit as st
import json
import base64
import gspread
import pandas as pd
import os
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================================================
# 1. KONFIGURACJA ŚCIEŻEK I ZASOBÓW
# =========================================================
PATH_CHECKLIST = os.path.join("data", "lista_kontrolna.json")
PATH_BG = os.path.join("assets", "bg_vorteza.png")
PATH_LOGO = os.path.join("assets", "logo_vorteza.png")
SHEET_ID = "1JV-vXpwAbvvboQd7eijashVmS3kkOqTf_LJrbrsWSxo"

def load_vorteza_asset_b64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        return ""
    except: return ""

def load_checklist_local():
    """Wczytuje listę kontrolną z lokalnego folderu data/."""
    if os.path.exists(PATH_CHECKLIST):
        with open(PATH_CHECKLIST, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# =========================================================
# 2. SILNIK GOOGLE SHEETS
# =========================================================
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = st.secrets["GCP_SERVICE_ACCOUNT"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(credentials)

def load_from_google_sheets():
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Błąd połączenia z bazą danych: {e}")
        return pd.DataFrame()

def save_to_google_sheets(row_data):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).sheet1
        sheet.append_row(row_data)
        return True
    except: return False

# =========================================================
# 3. INTERFEJS I STYLIZACJA
# =========================================================
def apply_base_theme():
    bg_data = load_vorteza_asset_b64(PATH_BG)
    bg_style = f"""
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.92), rgba(0,0,0,0.92)), 
                        url("data:image/png;base64,{bg_data}") !important;
            background-size: cover !important;
            background-attachment: fixed !important;
        }}
    """ if bg_data else ".stApp { background-color: #050505 !important; }"

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Michroma&family=Montserrat:wght@400;700&display=swap');
        {bg_style}
        .vorteza-header {{ font-family: 'Michroma', sans-serif !important; color: #B58863 !important; text-align: center; letter-spacing: 4px; padding: 20px; text-transform: uppercase; }}
        .log-entry {{ background-color: rgba(12, 12, 12, 0.95) !important; border-left: 8px solid #B58863 !important; padding: 20px; margin-bottom: 15px; border-radius: 4px; }}
        .log-entry-alert {{ border-left: 8px solid #FF4B4B !important; }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 4. GŁÓWNA FUNKCJA MODUŁU (DLA HUB)
# =========================================================
def run_base():
    apply_base_theme()
    
    # Ustalenie użytkownika z sesji Hub-a
    current_user = st.session_state.get("username", "OPERATOR")
    is_dispatcher = any(x in current_user.lower() for x in ["dyspozytor", "admin"])
    
    st.markdown("<h2 class='vorteza-header'>VORTEZA BASE | LOGISTICS CONTROL</h2>", unsafe_allow_html=True)

    if is_dispatcher:
        # --- WIDOK DYSPOZYTORA (MONITORING) ---
        df = load_from_google_sheets()
        if not df.empty:
            st.subheader("Ostatnie Raporty Floty")
            for idx, row in df.iloc[::-1].iterrows(): # Od najnowszych
                is_alert = "ALERT" in str(row.get('Wynik Kontroli', ''))
                entry_class = "log-entry log-entry-alert" if is_alert else "log-entry"
                
                st.markdown(f"""
                <div class="{entry_class}">
                    <b style="color:#B58863; font-size:1.2rem;">{row.get('Numer Rejestracyjny', 'N/A')}</b> | 
                    Data: {row.get('Data i Godzina', 'N/A')} | OP: {row.get('Operator ID', 'N/A')}<br>
                    <span style="color:{'#FF4B4B' if is_alert else '#00FF41'}">STATUS: {row.get('Wynik Kontroli', 'NOMINAL')}</span><br>
                    <small>Przebieg: {row.get('Przebieg (km)', 0)} km | Uwagi: {row.get('Uwagi i Obserwacje', '-')}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Brak aktywnych logów w bazie Google Sheets.")

    else:
        # --- WIDOK KIEROWCY (PROTOKÓŁ) ---
        data_gh = load_checklist_local()
        
        with st.form("driver_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                r_plate = st.text_input("NUMER REJESTRACYJNY").upper()
            with col2:
                k_odo = st.number_input("AKTUALNY PRZEBIEG (KM)", step=1)
            
            check_results = {}
            if data_gh and "lista_kontrolna" in data_gh:
                for kat, punkty in data_gh["lista_kontrolna"].items():
                    with st.expander(kat.upper()):
                        for pt in punkty:
                            res = st.checkbox(pt, key=f"f_{pt}")
                            check_results[pt] = "OK" if res else "BRAK"
            
            u_notes = st.text_area("DODATKOWE UWAGI / OBSERWACJE")
            
            if st.form_submit_button("WYŚLIJ PROTOKÓŁ DO SYSTEMU"):
                if not r_plate:
                    st.error("Błąd: Numer rejestracyjny jest wymagany!")
                else:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                    errs = [pt for pt, v in check_results.items() if v == "BRAK"]
                    status = "NOMINAL" if not errs else f"ALERT: {', '.join(errs)}"
                    
                    if save_to_google_sheets([ts, current_user, r_plate, k_odo, status, u_notes]):
                        st.success("Protokół został pomyślnie wysłany do bazy.")
                        st.balloons()
                    else:
                        st.error("Błąd zapisu w Google Sheets. Sprawdź połączenie.")

if __name__ == "__main__":
    run_base()
