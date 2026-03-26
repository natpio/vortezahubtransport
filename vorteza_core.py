# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json
import os
import base64
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import gspread

# ==============================================================================
# 1. KONFIGURACJA I ZASOBY
# ==============================================================================
PATH_CONFIG = os.path.join("data", "config.json")
PATH_PRODUCTS = os.path.join("data", "products.json")
PATH_BG = os.path.join("assets", "tlo_hub_2.jpg")
UPLOAD_DIR = os.path.join("data", "uploads")

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# NOWE ID ARKUSZA
SHEET_ID = "1Arq4WTFcvbvH7JkMEMWpWkGjaN44J4UpgJ2T9lKQLn8"

def load_vorteza_asset_b64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f: return base64.b64encode(f.read()).decode()
        return ""
    except: return ""

def load_local_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

# ==============================================================================
# 2. GOOGLE SHEETS ENGINE (SPEDYCJA)
# ==============================================================================
def get_gspread_client():
    creds_info = st.secrets["GCP_SERVICE_ACCOUNT"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(credentials)

def load_orders():
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Zlecenia")
        return pd.DataFrame(sheet.get_all_records())
    except Exception as e:
        st.error(f"Błąd bazy danych: {e}")
        return pd.DataFrame()

def save_new_order(row_data):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Zlecenia")
        sheet.append_row(row_data)
        return True
    except: return False

def update_order_status(order_id, new_status):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Zlecenia")
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('ID')) == str(order_id):
                sheet.update_cell(i + 2, 2, new_status)
                return True
        return False
    except: return False

def assign_transport(order_id, trakcja, przewoznik, auto_kierowca):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Zlecenia")
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('ID')) == str(order_id):
                row_idx = i + 2
                sheet.update_cell(row_idx, 2, "ZAPLANOWANE") # Zmiana statusu
                sheet.update_cell(row_idx, 9, str(trakcja))  # Trakcja
                sheet.update_cell(row_idx, 10, str(przewoznik)) # Przewoznik
                sheet.update_cell(row_idx, 11, str(auto_kierowca)) # Auto
                return True
        return False
    except: return False

def update_order_billing(order_id, inv_num, inv_date, term_days, is_paid, file_name=""):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Zlecenia")
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('ID')) == str(order_id):
                row_idx = i + 2
                sheet.update_cell(row_idx, 16, str(inv_num))   
                sheet.update_cell(row_idx, 17, str(inv_date))  
                sheet.update_cell(row_idx, 18, int(term_days)) 
                sheet.update_cell(row_idx, 19, str(is_paid))
                if file_name: sheet.update_cell(row_idx, 20, str(file_name)) # T: Zalacznik
                return True
        return False
    except: return False

def update_full_order(order_id, klient, spedytor, start, koniec, data_z, data_r, trakcja, przewoznik, auto_kierowca, f_sprzedaz, f_kupno, ladunek_json, uwagi):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Zlecenia")
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('ID')) == str(order_id):
                row_idx = i + 2
                cell_list = sheet.range(f'C{row_idx}:O{row_idx}')
                values = [str(klient), str(spedytor), str(start), str(koniec), str(data_z), str(data_r), str(trakcja), str(przewoznik), str(auto_kierowca), str(f_sprzedaz), str(f_kupno), str(ladunek_json), str(uwagi)]
                for j, val in enumerate(values): cell_list[j].value = val
                sheet.update_cells(cell_list)
                return True
        return False
    except: return False

# ==============================================================================
# 3. INTERFEJS
# ==============================================================================
def inject_core_theme():
    bg_data = load_vorteza_asset_b64(PATH_BG)
    bg_style = f"""
        .stApp {{ background: linear-gradient(rgba(6, 6, 6, 0.90), rgba(6, 6, 6, 0.90)), url("data:image/jpeg;base64,{bg_data}") !important; background-size: cover !important; background-attachment: fixed !important; }}
    """ if bg_data else ".stApp { background-color: #060606 !important; }"

    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;700&family=JetBrains+Mono&display=swap');
            {bg_style}
            h1, h2, h3, h4 {{ color: #B58863 !important; text-transform: uppercase; letter-spacing: 4px !important; font-weight: 700 !important; }}
            .order-card {{ background: rgba(15, 15, 15, 0.85); border: 1px solid rgba(181, 136, 99, 0.3); border-left: 4px solid #B58863; padding: 15px; margin-bottom: 15px; border-radius: 4px; }}
            .order-card-title {{ color: #FFFFFF; font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; }}
            .status-draft {{ border-left-color: #AAAAAA !important; }}
            .status-akcept {{ border-left-color: #2980B9 !important; }}
            .status-plan {{ border-left-color: #F1C40F !important; }}
            .status-trasa {{ border-left-color: #E67E22 !important; }}
            .billing-card {{ background: rgba(20, 20, 20, 0.9); border: 1px solid #333; border-left: 4px solid #E67E22; padding: 15px; margin-bottom: 15px; border-radius: 6px; }}
            div[data-testid="stButton"] button {{ width: 100%; border-color: #B58863 !important; color: #B58863 !important; background: transparent !important; margin-bottom: 5px; }}
            div[data-testid="stButton"] button:hover {{ background: #B58863 !important; color: #000 !important; }}
        </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 4. GŁÓWNA LOGIKA MODUŁU CORE
# ==============================================================================
def run_core():
    inject_core_theme()
    st.markdown("<h2>VORTEZA TMS | ZARZĄDZANIE SPEDYCJĄ</h2>", unsafe_allow_html=True)
    
    current_user = st.session_state.get("username", "OPERATOR")
    config_data = load_local_json(PATH_CONFIG)
    products_data = load_local_json(PATH_PRODUCTS)
    
    if "core_cart" not in st.session_state: st.session_state.core_cart = []
    if "edit_cart" not in st.session_state: st.session_state.edit_cart = []

    with st.sidebar:
        st.markdown("### 🎛️ PANEL STEROWANIA")
        mode = st.radio("TRYB PRACY:", [
            "📊 TABLICA (KANBAN)", 
            "🗺️ SHIPPING LIST", 
            "➕ NOWE ZLECENIE", 
            "✏️ EDYCJA ZLECENIA",
            "💰 ROZLICZENIA (BILLING)",
            "🗄️ ARCHIWUM"
        ], label_visibility="collapsed")
        st.divider()

    df = load_orders()

    # --------------------------------------------------------------------------
    # WIDOK 1: KANBAN
    # --------------------------------------------------------------------------
    if mode == "📊 TABLICA (KANBAN)":
        if df.empty:
            st.info("Brak zleceń w systemie.")
            return
            
        c1, c2, c3, c4 = st.columns(4)
        columns = {"DRAFT (NOWE)": c1, "ZAAKCEPTOWANE": c2, "ZAPLANOWANE": c3, "W TRASIE": c4}
        
        for title, col in columns.items():
            with col:
                st.markdown(f"<h4 style='text-align:center; font-size:0.9rem; border-bottom:1px solid #B58863; padding-bottom:10px;'>{title}</h4>", unsafe_allow_html=True)
                df_filtered = df[df['Status'].astype(str) == title]
                
                for _, row in df_filtered.iterrows():
                    o_id = row.get('ID', 'N/A')
                    css = "order-card status-draft" if title == "DRAFT (NOWE)" else "order-card status-akcept" if title == "ZAAKCEPTOWANE" else "order-card status-plan" if title == "ZAPLANOWANE" else "order-card status-trasa"
                    
                    st.markdown(f"""
                        <div class="{css}">
                            <div class="order-card-title">{o_id} | {row.get('Klient', '-')}</div>
                            <div style="color:#B58863; font-family:'JetBrains Mono'; font-size:0.8rem; margin-bottom:5px;">📍 {row.get('Start', '-')} ➔ {row.get('Koniec', '-')}</div>
                            <div style="color:#AAA; font-size:0.8rem; line-height:1.4;">
                                <b>Przewoźnik:</b> {row.get('Przewoznik', 'BRAK')}<br>
                                <b>Auto:</b> {row.get('Pojazd_Kierowca', 'BRAK')}<br>
                                <b>Data Zał:</b> {row.get('DataZal', '-')}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if title == "DRAFT (NOWE)":
                        if st.button("✅ AKCEPT (DO PLANU)", key=f"akc_{o_id}"): update_order_status(o_id, "ZAAKCEPTOWANE"); st.rerun()
                    elif title == "ZAAKCEPTOWANE":
                        st.info("Przejdź do SHIPPING LIST, aby zaplanować.")
                        if st.button("↩️ COFNIJ", key=f"cof1_{o_id}"): update_order_status(o_id, "DRAFT (NOWE)"); st.rerun()
                    elif title == "ZAPLANOWANE":
                        if st.button("🚚 WYDAJ (W TRASĘ)", key=f"drg_{o_id}"): update_order_status(o_id, "W TRASIE"); st.rerun()
                        if st.button("↩️ COFNIJ", key=f"cof2_{o_id}"): update_order_status(o_id, "ZAAKCEPTOWANE"); st.rerun()
                    elif title == "W TRASIE":
                        if st.button("🏁 ZAKOŃCZ ZLECENIE", key=f"kon_{o_id}"): update_order_status(o_id, "ZAKOŃCZONE"); st.rerun()

    # --------------------------------------------------------------------------
    # WIDOK 2: SHIPPING LIST (NOWOŚĆ)
    # --------------------------------------------------------------------------
    elif mode == "🗺️ SHIPPING LIST":
        st.markdown("### 🗺️ SHIPPING LIST (PLANOWANIE I DOŁADUNKI)")
        if df.empty: st.info("Brak danych."); return
        
        df_acc = df[df['Status'] == 'ZAAKCEPTOWANE']
        if df_acc.empty:
            st.success("Wszystkie zlecenia są już zaplanowane! Brak ładunków oczekujących.")
        else:
            st.write("Wybierz zlecenia z listy (możesz łączyć bliskie kierunki), aby przypisać je do jednego pojazdu.")
            
            # Tabela podglądowa dla spedytora
            disp_df = df_acc[['ID', 'Start', 'Koniec', 'DataZal', 'DataRozl', 'Klient']].copy()
            st.dataframe(disp_df, use_container_width=True, hide_index=True)
            
            selected_ids = st.multiselect("WYBIERZ ZLECENIA DO POŁĄCZENIA:", df_acc['ID'].tolist())
            
            if selected_ids:
                total_weight = 0
                total_items = 0
                for s_id in selected_ids:
                    row_data = df_acc[df_acc['ID'] == s_id].iloc[0]
                    try: 
                        ladunek = json.loads(row_data.get('Ladunek', '[]'))
                        for item in ladunek:
                            qty = int(item['ILOSC'])
                            total_items += qty
                            # Szukanie wagi w products.json
                            for p in products_data:
                                if p['name'] == item['SKU']:
                                    total_weight += (p.get('weight', 0) * qty)
                    except: pass
                
                st.info(f"**PODSUMOWANIE WYBRANYCH:** Łącznie jednostek: {total_items} szt. | Szacowana waga: {total_weight} KG")
                
                with st.container(border=True):
                    st.markdown("#### 🚚 PRZYPISZ TRANSPORT")
                    col1, col2, col3 = st.columns(3)
                    trakcja = col1.radio("TYP TRAKCJI", ["WŁASNY TABOR", "PODWYKONAWCA (PRZEWOŹNIK)"])
                    przewoznik = col2.text_input("NAZWA PRZEWOŹNIKA", value="VORTEZA FLEET" if trakcja=="WŁASNY TABOR" else "")
                    auto_kierowca = col3.text_input("NUMER REJESTRACYJNY (Ważne dla Kierowcy!)")
                    
                    if st.button("💾 ZAPLANUJ TRASĘ I ZAPISZ", use_container_width=True):
                        if not auto_kierowca: st.error("Podaj numer rejestracyjny!")
                        else:
                            success = True
                            for s_id in selected_ids:
                                if not assign_transport(s_id, trakcja, przewoznik, auto_kierowca.upper()): success = False
                            if success:
                                st.success("Pomyślnie przypisano transport i zaplanowano trasę!")
                                st.rerun()
                            else: st.error("Błąd podczas przypisywania!")

    # --------------------------------------------------------------------------
    # WIDOK 3: KREATOR ZLECENIA
    # --------------------------------------------------------------------------
    elif mode == "➕ NOWE ZLECENIE":
        st.markdown("### 📝 KREATOR ZLECENIA SPEDYCYJNEGO")
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            with st.container(border=True):
                col1, col2 = st.columns(2)
                klient = col1.text_input("KLIENT / ZLECENIODAWCA")
                uwagi = col2.text_input("UWAGI (Awizacja itp.)")

                st.divider()
                col_f1, col_f2 = st.columns(2)
                fracht_sprzedaz = col_f1.text_input("FRACHT SPRZEDAŻ (Dla Klienta)", "0")
                fracht_kupno = col_f2.text_input("SZACOWANY KOSZT LUB KUPNO", "0")

                st.divider()
                miasta_start = list(config_data.get("DISTANCES_AND_MYTO", {}).keys()) if config_data else ["Poznań", "Warszawa"]
                col3, col4 = st.columns(2)
                start = col3.selectbox("MIEJSCE ZAŁADUNKU", miasta_start)
                miasta_cel = list(config_data.get("DISTANCES_AND_MYTO", {}).get(start, {}).keys()) if config_data else []
                koniec = col4.selectbox("MIEJSCE ROZŁADUNKU", miasta_cel)
                
                col5, col6 = st.columns(2)
                data_z = col5.date_input("DATA ZAŁADUNKU")
                data_r = col6.date_input("DATA ROZŁADUNKU")

        with c_right:
            with st.container(border=True):
                st.markdown("#### ŁADUNEK / PALETY")
                lista_sku = [p['name'] for p in products_data] if products_data else []
                wybrane_sku = st.selectbox("WYBIERZ JEDNOSTKĘ", lista_sku)
                ilosc_sku = st.number_input("ILOŚĆ (SZTUKI)", min_value=1, value=1)
                
                if st.button("➕ DODAJ"): st.session_state.core_cart.append({"SKU": wybrane_sku, "ILOSC": ilosc_sku})
                st.markdown("---")
                if st.session_state.core_cart:
                    for i, item in enumerate(st.session_state.core_cart): st.markdown(f"- **{item['ILOSC']}x** {item['SKU']}")
                    if st.button("🗑️ WYCZYŚĆ"): st.session_state.core_cart = []; st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 UTWÓRZ ZLECENIE (TRAFIA DO AKCEPTACJI)", use_container_width=True):
            if not klient: st.error("Podaj nazwę klienta!")
            else:
                now = datetime.now()
                order_id = f"TMS-{now.strftime('%y')}-{now.strftime('%H%M%S')}"
                ladunek_json = json.dumps(st.session_state.core_cart, ensure_ascii=False)
                
                row = [order_id, "DRAFT (NOWE)", klient, current_user, start, koniec, str(data_z), str(data_r), "", "", "", fracht_sprzedaz, fracht_kupno, ladunek_json, uwagi, "", "", 30, "NIE", ""]
                if save_new_order(row):
                    st.session_state.core_cart = [] 
                    st.success(f"Zlecenie {order_id} utworzone!"); st.balloons()
                else: st.error("Błąd zapisu w Google Sheets.")

    # --------------------------------------------------------------------------
    # WIDOK 4: EDYCJA
    # --------------------------------------------------------------------------
    elif mode == "✏️ EDYCJA ZLECENIA":
        st.info("Opcja edycji tymczasowo wyłączona z poziomu tego widoku w celu wdrożenia Shipping List. Planowanie odbywa się teraz w zakładce SHIPPING LIST.")

    # --------------------------------------------------------------------------
    # WIDOK 5: ROZLICZENIA (BILLING + PDF)
    # --------------------------------------------------------------------------
    elif mode == "💰 ROZLICZENIA (BILLING)":
        st.markdown("### 💰 PANEL ROZLICZEŃ, WINDYKACJI I DOKUMENTÓW")
        if df.empty: st.info("Brak zleceń."); return
        
        df_billing = df[df['Status'].isin(['ZAKOŃCZONE', 'ZAMKNIĘTE'])]
        if df_billing.empty:
            st.success("Brak zakończonych zleceń do rozliczenia.")
        else:
            for _, row in df_billing.iterrows():
                o_id = row.get('ID', 'N/A')
                inv_no = str(row.get('Faktura', '')).strip()
                inv_date_str = str(row.get('DataFaktury', '')).strip()
                try: term_days = int(row.get('TerminDni', 30))
                except: term_days = 30
                is_paid = (str(row.get('StatusPlatnosci', 'NIE')).strip().upper() == 'TAK')
                zalacznik = str(row.get('Zalacznik', ''))
                
                badge_html = f"<span style='color:#27AE60;'>✅ OPŁACONA ({inv_no})</span>" if is_paid else "<span style='color:#F1C40F;'>⏳ OCZEKUJE</span>"
                if zalacznik: badge_html += f" | 📄 PLIK: {zalacznik}"
                
                st.markdown(f"""
                    <div class="billing-card">
                        <div style="display:flex; justify-content:space-between;">
                            <div><span style="color:#B58863; font-weight:bold;">{o_id}</span> | {row.get('Klient', '-')} | Fracht: {row.get('Fracht_Sprzedaz', '-')}</div>
                            <div>{badge_html}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.form(f"bill_form_{o_id}"):
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
                    new_inv_no = c1.text_input("NUMER FAKTURY", value=inv_no)
                    new_term = c2.number_input("TERMIN", value=term_days, step=1)
                    new_is_paid = c3.checkbox("✅ OPŁACONA", value=is_paid)
                    
                    uploaded_file = c4.file_uploader("Wgraj CMR/Fakturę (PDF/IMG)", type=["pdf", "jpg", "png"])
                    
                    if st.form_submit_button("💾 ZAPISZ DANE I PLIK", use_container_width=True):
                        file_name_to_save = zalacznik
                        if uploaded_file is not None:
                            file_name_to_save = f"{o_id}_{uploaded_file.name}"
                            with open(os.path.join(UPLOAD_DIR, file_name_to_save), "wb") as f:
                                f.write(uploaded_file.getbuffer())
                                
                        status_val = "TAK" if new_is_paid else "NIE"
                        if update_order_billing(o_id, new_inv_no, datetime.now().strftime("%Y-%m-%d"), new_term, status_val, file_name_to_save):
                            st.success("Zaktualizowano!"); st.rerun()

    # --------------------------------------------------------------------------
    # WIDOK 6: ARCHIWUM
    # --------------------------------------------------------------------------
    elif mode == "🗄️ ARCHIWUM":
        st.dataframe(df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    run_core()
