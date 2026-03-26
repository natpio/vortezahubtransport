# -*- coding: utf-8 -*-
import streamlit as st
import json
import plotly.graph_objects as go
import math
import pandas as pd
import random
import base64
import os
from datetime import datetime

# ==============================================================================
# 0. KONFIGURACJA ŚCIEŻEK I ZASOBÓW
# ==============================================================================
if not os.path.exists("data"):
    os.makedirs("data")

PATH_DATA = os.path.join("data", "products.json")
PATH_BG = os.path.join("assets", "bg_vorteza.png")

LANGUAGES = {
    "PL": {
        "title": "VORTEZA STACK PRO V26", "fleet": "KONSOLA FLOTY", "unit": "JEDNOSTKA",
        "offset": "OFFSET (cm)", "cargo": "WEJŚCIE ŁADUNKU", "sku_sel": "WYBÓR SKU",
        "qty": "SZTUKI", "add": "DODAJ DO MANIFESTU", "purge": "WYCZYŚĆ DANE",
        "manifest": "MANIFEST ZAŁADUNKOWY", "edit_m": "EDYCJA MANIFESTU", "cases": "OPAKOWANIA",
        "pcs": "SZTUKI ŁĄCZNIE", "weight": "WAGA BRUTTO", "util": "UTYLIZACJA",
        "ldm_occ": "LDM ZAJĘTE", "ldm_free": "LDM WOLNE", "vol": "OBJĘTOŚĆ",
        "no_data": "STATUS: OCZEKIWANIE NA DANE", "inventory": "BAZA SKU", 
        "save_db": "ZAPISZ BAZĘ SKU", "sync": "SYNCHRONIZACJA OK", "update": "AKTUALIZUJ MANIFEST",
        "sku_ident": "IDENTYFIKATOR SKU", "mode_sel": "TRYB PRACY", 
        "mode_3d": "🛰️ WIZUALIZACJA 3D", "mode_db": "📦 EDYTOR BAZY SKU",
        "fleet_needed": "WYMAGANA FLOTA", "vehicle_num": "POJAZD #",
        "select_veh": "WYBIERZ POJAZD DO PODGLĄDU:"
    }
}

# REJESTR POJAZDÓW (Uporządkowany od najmniejszego do największego)
FLEET_MASTER_DATA = {
    "BUS Opel Movano": {"max_w": 1300, "L": 420, "W": 210, "H": 230, "axles": 2, "cab_l": 150, "total_ldm": 4.2},
    "Solo 6m Light": {"max_w": 5000, "L": 610, "W": 245, "H": 250, "axles": 2, "cab_l": 180, "total_ldm": 6.1},
    "Solo 7m Medium": {"max_w": 7000, "L": 720, "W": 245, "H": 260, "axles": 2, "cab_l": 180, "total_ldm": 7.2},
    "Solo 9m Heavy Duty": {"max_w": 9500, "L": 920, "W": 245, "H": 270, "axles": 2, "cab_l": 200, "total_ldm": 9.2},
    "TIR FTL Standard 13.6m": {"max_w": 24000, "L": 1360, "W": 248, "H": 275, "axles": 3, "cab_l": 250, "total_ldm": 13.6},
    "TIR FTL Mega 13.6m": {"max_w": 24000, "L": 1360, "W": 248, "H": 300, "axles": 3, "cab_l": 250, "total_ldm": 13.6}
}

# ==============================================================================
# 1. UI ENGINE: APEX DARK & COLOR FIX
# ==============================================================================
def inject_vorteza_stack_ui():
    bg_data = ""
    if os.path.exists(PATH_BG):
        with open(PATH_BG, 'rb') as f: bg_data = base64.b64encode(f.read()).decode()
    
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;700&family=JetBrains+Mono&display=swap');
            .stApp {{ 
                background-image: url("data:image/png;base64,{bg_data}"); 
                background-size: cover; background-attachment: fixed; 
            }}
            
            /* NAPRAWA CZYTELNOŚCI - MIEDZIANE CZCIONKI DLA WIDGETÓW */
            div[data-testid="stWidgetLabel"] p {{
                color: #B58863 !important;
                font-weight: 700 !important;
                letter-spacing: 1px;
            }}
            div[data-testid="stRadio"] label p {{
                color: #B58863 !important;
                font-size: 1rem !important;
            }}
            .stSlider [data-testid="stWidgetLabel"] p {{
                color: #B58863 !important;
            }}
            
            /* Kafelki KPI PRO */
            .v-kpi-card {{
                background: rgba(10, 10, 10, 0.9); border: 1px solid rgba(181, 136, 99, 0.3);
                border-top: 4px solid #B58863; padding: 12px; text-align: center; backdrop-filter: blur(10px);
            }}
            .v-kpi-label {{ color: #B58863; font-size: 0.65rem; letter-spacing: 2px; text-transform: uppercase; font-weight: 700; }}
            .v-kpi-value {{ color: #FFFFFF; font-size: 1.4rem; font-family: 'JetBrains Mono', monospace; font-weight: 500; }}
            
            .v-table-pro {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: rgba(0,0,0,0.7); border: 1px solid #333; }}
            .v-table-pro th {{ background: #B58863; color: black; padding: 12px; text-align: left; text-transform: uppercase; font-size: 0.7rem; }}
            .v-table-pro td {{ padding: 10px 12px; border-bottom: 1px solid #222; color: #DDD; font-family: 'JetBrains Mono', monospace; }}
            .v-badge-unit {{ background: rgba(181,136,99,0.1); border: 1px solid #B58863; padding: 10px; color: #B58863; font-size: 0.8rem; margin-bottom: 10px; }}
            .js-plotly-plot .plotly .main-svg {{ background: transparent !important; }}
        </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. V-COLOR ENGINE
# ==============================================================================
def get_vorteza_sku_hex(sku_name):
    palette = ["#B58863", "#D4AF37", "#16A085", "#27AE60", "#2980B9", "#E67E22", "#C0392B", "#8E44AD", "#F1C40F", "#34495E"]
    random.seed(sum(ord(c) for c in str(sku_name)))
    return random.choice(palette)

# ==============================================================================
# 3. SILNIK GRAFICZNY PRO (V26)
# ==============================================================================
def build_mesh(vx, vy, vz, color, name, op=1.0):
    return go.Mesh3d(x=vx, y=vy, z=vz, i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6], color=color, opacity=op, name=name, flatshading=True)

def render_vorteza_pro_3d(veh, stacks):
    fig = go.Figure()
    L, W, H, cab = veh['L'], veh['W'], veh['H'], veh['cab_l']
    
    # Rama i Podwozie
    fig.add_trace(build_mesh([0, L, L, 0, 0, L, L, 0], [0, 0, W, W, 0, 0, W, W], [-10, -10, -10, -10, -2, -2, -2, -2], "#B58863", "RAMA"))
    for ax in range(veh['axles']):
        pos_x = L - 380 + (ax * 135) if L > 500 else L - 150 + (ax * 100)
        for side in [-35, W+15]:
            fig.add_trace(build_mesh([pos_x-50, pos_x+50, pos_x+50, pos_x-50, pos_x-50, pos_x+50, pos_x+50, pos_x-50], [side, side, side+20, side+20, side, side, side+20, side+20], [-80, -80, -80, -80, -5, -5, -5, -5], "#000", "KOŁO"))
    
    # Kabina
    fig.add_trace(build_mesh([-cab, 0, 0, -cab, -cab, 0, 0, -cab], [-15, -15, W+15, W+15, -15, -15, W+15, W+15], [0, 0, 0, 0, H*0.95, H*0.95, H*0.95, H*0.95], "#050505", "KABINA"))
    
    # Kontury Naczepy
    skel_lines = [
        ([0, L], [0, 0], [0, 0]), ([0, L], [W, W], [0, 0]), ([0, 0], [0, W], [0, 0]), ([L, L], [0, W], [0, 0]),
        ([0, L], [0, 0], [H, H]), ([0, L], [W, W], [H, H]), ([0, 0], [0, W], [H, H]), ([L, L], [0, W], [H, H]),
        ([0, 0], [0, 0], [0, H]), ([0, 0], [W, W], [0, H]), ([L, L], [0, 0], [0, H]), ([L, L], [W, W], [0, H])
    ]
    for lx, ly, lz in skel_lines:
        fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='#B58863', width=5), hoverinfo='skip'))
    
    # Ładunek Solidny
    for s in stacks:
        for u in s['items']:
            clr = get_vorteza_sku_hex(u['name'])
            vx, vy, vz = [s['x'], s['x']+u['w_fit'], s['x']+u['w_fit'], s['x'], s['x'], s['x']+u['w_fit'], s['x']+u['w_fit'], s['x']], [s['y'], s['y'], s['y']+u['l_fit'], s['y']+u['l_fit'], s['y'], s['y'], s['y']+u['l_fit'], s['y']+u['l_fit']], [u['z'], u['z'], u['z'], u['z'], u['z']+u['height'], u['z']+u['height'], u['z']+u['height'], u['z']+u['height']]
            fig.add_trace(go.Mesh3d(x=vx, y=vy, z=vz, i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6], color=clr, opacity=1.0, name=u['name']))
            
            lx_p = [vx[0], vx[1], vx[2], vx[3], vx[0], vx[4], vx[5], vx[1], vx[5], vx[6], vx[2], vx[6], vx[7], vx[3], vx[7], vx[4]]
            ly_p = [vy[0], vy[1], vy[2], vy[3], vy[0], vy[4], vy[5], vy[1], vy[5], vy[6], vy[2], vy[6], vy[7], vy[3], vy[7], vy[4]]
            lz_p = [vz[0], vz[1], vz[2], vz[3], vz[0], vz[4], vz[5], vz[1], vz[5], vz[6], vz[2], vz[6], vz[7], vz[3], vz[7], vz[4]]
            fig.add_trace(go.Scatter3d(x=lx_p, y=ly_p, z=lz_p, mode='lines', line=dict(color='black', width=2), hoverinfo='skip'))

    fig.update_layout(scene=dict(aspectmode='data', xaxis_visible=False, yaxis_visible=False, zaxis_visible=False, bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, b=0, t=0), showlegend=False)
    return fig

# ==============================================================================
# 4. SILNIK DYNAMICZNEJ FLOTY V26 (DYNAMIC-FLEET OPTIMIZER)
# ==============================================================================
class V26FleetOptimizer:
    @staticmethod
    def pack_single(cargo, veh, x_off=0):
        stacks, weight, volume, packed_indices = [], 0, 0, []
        for i, u in enumerate(cargo):
            if weight + u['weight'] > veh['max_w']: continue
            placed = False
            for s in stacks:
                if u.get('canStack', True) and u['width'] <= s['w'] and u['length'] <= s['l'] and (s['curH'] + u['height'] <= veh['H']):
                    u_c = u.copy(); u_c['z'], u_c['w_fit'], u_c['l_fit'] = s['curH'], s['w'], s['l']
                    s['items'].append(u_c); s['curH'] += u['height']; weight += u['weight']
                    volume += (u['width']*u['length']*u['height'])/1e6; packed_indices.append(i); placed = True; break
            if placed: continue
            for x in range(x_off, veh['L'] - u['width'] + 1, 10):
                for y in range(0, veh['W'] - u['length'] + 1, 10):
                    collision = False
                    for s in stacks:
                        if not (x + u['width'] <= s['x'] or x >= s['x'] + s['w'] or y + u['length'] <= s['y'] or y >= s['y'] + s['l']):
                            collision = True; break
                    if not collision:
                        u_c = u.copy(); u_c['z'], u_c['w_fit'], u_c['l_fit'] = 0, u['width'], u['length']
                        stacks.append({'x':x, 'y':y, 'w':u['width'], 'l':u['length'], 'curH':u['height'], 'items':[u_c]})
                        weight += u['weight']; volume += (u['width']*u['length']*u['height'])/1e6; packed_indices.append(i); placed = True; break
                if placed: break
        return stacks, weight, volume, packed_indices

    @staticmethod
    def solve_multi(cargo_full, x_off=0):
        cargo_working = sorted(cargo_full, key=lambda x: (not x.get('canStack', True), x['width']*x['length']*x['height']), reverse=True)
        fleet_results = []
        while cargo_working:
            best_veh_name, best_result = None, None
            for v_name, v_spec in FLEET_MASTER_DATA.items():
                stacks, weight, vol, indices = V26FleetOptimizer.pack_single(cargo_working, v_spec, x_off)
                if len(indices) == len(cargo_working):
                    best_veh_name, best_result = v_name, (stacks, weight, vol, indices)
                    break
                if v_name == list(FLEET_MASTER_DATA.keys())[-1]:
                    best_veh_name, best_result = v_name, (stacks, weight, vol, indices)
            if not best_result or not best_result[3]: break
            stacks, weight, vol, indices = best_result
            fleet_results.append({"v_name": best_veh_name, "v_spec": FLEET_MASTER_DATA[best_veh_name], "stacks": stacks, "weight": weight, "volume": vol, "packed_items": [cargo_working[i] for i in indices]})
            cargo_working = [item for i, item in enumerate(cargo_working) if i not in indices]
        return fleet_results

# ==============================================================================
# 5. GŁÓWNA FUNKCJA URUCHOMIENIOWA
# ==============================================================================
def db_core_load():
    if os.path.exists(PATH_DATA):
        try:
            with open(PATH_DATA, 'r', encoding='utf-8') as f: return json.load(f)
        except: return []
    return []

def db_core_save(data):
    with open(PATH_DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def run_stack():
    inject_vorteza_stack_ui()
    L = LANGUAGES["PL"]
    if 'v_manifest' not in st.session_state: st.session_state.v_manifest = []
    inventory = db_core_load()

    with st.sidebar:
        st.markdown(f"### ⚙️ {L['mode_sel']}")
        app_mode = st.radio("PANEL", [L['mode_3d'], L['mode_db']], label_visibility="collapsed")
        st.divider()

        if app_mode == L['mode_3d']:
            st.markdown(f"### 🛰️ KONFIGURACJA")
            x_shift = st.slider(L['offset'], 0, 200, 0)
            st.divider()
            st.markdown(f"### 📥 {L['cargo']}")
            sel_sku = st.selectbox(L['sku_sel'], [p['name'] for p in inventory], index=None)
            if sel_sku:
                p_ref = next(p for p in inventory if p['name'] == sel_sku)
                ipc = int(p_ref.get('itemsPerCase', 1)) if p_ref.get('itemsPerCase') else 1
                p_qty = st.number_input(L['qty'], min_value=1, value=ipc)
                if st.button(L['add']):
                    found = False
                    for it in st.session_state.v_manifest:
                        if it['name'] == sel_sku: it['p_act'] += p_qty; found = True; break
                    if not found:
                        u_e = p_ref.copy(); u_e['p_act'] = p_qty; st.session_state.v_manifest.append(u_e)
                    st.rerun()

            if st.session_state.v_manifest:
                st.divider()
                st.markdown(f"### 📝 {L['edit_m']}")
                df_m = pd.DataFrame(st.session_state.v_manifest)
                res_edit = st.data_editor(df_m[['name', 'p_act']], use_container_width=True, key="man_edit")
                if st.button(L['update']):
                    st.session_state.v_manifest = [it for it in [next((orig.copy() for orig in inventory if orig['name'] == r['name']), None) for _, r in res_edit.iterrows()] if it and it.update({'p_act': r['p_act']}) is None and it['p_act'] > 0]
                    st.rerun()
            if st.button(L['purge']): st.session_state.v_manifest = []; st.rerun()

    st.markdown(f"<h2 style='color:#B58863; letter-spacing:10px;'>{L['title']}</h2>", unsafe_allow_html=True)

    if app_mode == L['mode_3d']:
        if st.session_state.v_manifest:
            full_cargo_list = []
            for e in st.session_state.v_manifest:
                safe_ipc = int(e.get('itemsPerCase', 1)) if e.get('itemsPerCase') else 1
                for _ in range(math.ceil(e['p_act'] / safe_ipc)): full_cargo_list.append(e.copy())
            
            planned_fleet = V26FleetOptimizer.solve_multi(full_cargo_list, x_shift)
            st.markdown(f"### 🚛 {L['fleet_needed']}: {len(planned_fleet)}")
            
            veh_idx = 0
            if len(planned_fleet) > 1:
                veh_idx = st.radio(L['select_veh'], range(len(planned_fleet)), format_func=lambda x: f"{L['vehicle_num']}{x+1} - {planned_fleet[x]['v_name']}", horizontal=True)
            
            active_veh = planned_fleet[veh_idx]
            
            # --- ZAPISZ WYBRANY POJAZD DLA MODUŁU FLOW ---
            st.session_state.stack_selected_veh = active_veh['v_name']
            
            ldm_occ = (max([s['x'] + s['w'] for s in active_veh['stacks']]) / 100) if active_veh['stacks'] else 0
            
            c1, c2, c3, c4, c5 = st.columns(5)
            stats = [(L['pcs'], len(active_veh['packed_items'])), (L['weight'], f"{active_veh['weight']} KG"), (L['vol'], f"{active_veh['volume']:.1f} m³"), (L['ldm_occ'], f"{ldm_occ:.2f}"), (L['util'], f"{(active_veh['weight']/active_veh['v_spec']['max_w'])*100:.1f}%")]
            for i, (label, val) in enumerate(stats):
                with [c1, c2, c3, c4, c5][i]: st.markdown(f'<div class="v-kpi-card"><div class="v-kpi-label">{label}</div><div class="v-kpi-value">{val}</div></div>', unsafe_allow_html=True)

            st.plotly_chart(render_vorteza_pro_3d(active_veh['v_spec'], active_veh['stacks']), use_container_width=True)
            
            st.markdown(f"### 📋 {L['manifest']} - {active_veh['v_name']}")
            sku_counts = pd.Series([it['name'] for it in active_veh['packed_items']]).value_counts().reset_index()
            sku_counts.columns = ['SKU', 'OPAKOWANIA']
            html_table = f'<table class="v-table-pro"><tr><th>KOLOR</th><th>SKU</th><th>OPAKOWANIA</th></tr>'
            for _, row in sku_counts.iterrows():
                clr = get_vorteza_sku_hex(row['SKU'])
                html_table += f'<tr><td style="text-align:center;"><span style="color:{clr}; font-size:20px;">■</span></td><td>{row["SKU"]}</td><td>{row["OPAKOWANIA"]}</td></tr>'
            st.markdown(html_table + '</table>', unsafe_allow_html=True)
        else: st.info(L['no_data'])

    elif app_mode == L['mode_db']:
        st.markdown(f"### 📦 {L['inventory']}")
        new_db = st.data_editor(pd.DataFrame(inventory), use_container_width=True, num_rows="dynamic", key="db_edit")
        if st.button(L['save_db']):
            db_core_save(new_db.to_dict('records'))
            st.success(L['sync']); st.rerun()

if __name__ == "__main__":
    run_stack()
