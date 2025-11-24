import streamlit as st
import requests
import json
import os
from datetime import datetime
import pandas as pd 

# --- KONFIGURASI APLIKASI ---
# API BASE URL 
API_BASE = "https://www.thesportsdb.com/api/v1/json/3"

# File untuk menyimpan data pengguna
USER_DATA_FILE = "users.json"

# --- INITIALIZATION SESSION STATE ---
# INI ADALAH BAGIAN KRITIS YANG HARUS DIPERBAIKI/DIPASTIKAN ADA
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.selected_team = None
    # BARIS INI WAJIB DITAMBAHKAN/DIPASTIKAN ADA
    st.session_state.selected_team_name = None 
    st.session_state.search_results = []
    st.session_state.current_page = "Home"
    # Tambahkan inisialisasi untuk input pencarian juga
    st.session_state.search_query_input = ""
    st.session_state.search_country_input = ""

# --- FUNGSI AUTHENTIKASI ---

def load_users():
    """Memuat data pengguna dari file JSON."""
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_users(users):
    """Menyimpan data pengguna ke file JSON."""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def register_user(username, password):
    """Mendaftarkan pengguna baru."""
    users = load_users()
    if username in users:
        return False, "Username sudah terdaftar."
    
    if not username or not password:
        return False, "Username dan password tidak boleh kosong."
        
    users[username] = password 
    save_users(users)
    return True, "Pendaftaran berhasil! Silakan Login."

def login_user(username, password):
    """Login pengguna."""
    users = load_users()
    if username in users and users[username] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        return True, "Login berhasil!"
    return False, "Username atau password tidak valid."

def logout():
    """Logout pengguna."""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.selected_team = None
    st.session_state.selected_team_name = None
    st.session_state.search_results = []
    st.session_state.current_page = "Home"

# --- FUNGSI API (Menggunakan @st.cache_data untuk efisiensi) ---

@st.cache_data(ttl=3600)
def search_teams(query, sport="Soccer", country=None):
    """Mencari tim berdasarkan query, olahraga, dan negara."""
    url = f"{API_BASE}/search_all_teams.php?s={sport}"
    if country and country != "": 
        url += f"&c={country}"
        
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() 
        data = response.json()
        teams = data.get('teams', [])
        
        if query:
            teams = [t for t in teams if t.get('strTeam') and query.lower() in t['strTeam'].lower()]
        return teams
    except requests.exceptions.RequestException as e:
        st.error(f"Gagal mengambil data tim: Periksa koneksi atau URL. ({e})")
        return []

@st.cache_data(ttl=3600)
def get_team_details(team_id):
    """Mendapatkan detail tim berdasarkan ID."""
    url = f"{API_BASE}/lookupteam.php?id={team_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('teams', [{}])[0]
    except:
        return {}

@st.cache_data(ttl=3600)
def get_team_players(team_id):
    """Mendapatkan daftar pemain berdasarkan ID tim."""
    url = f"{API_BASE}/lookup_all_players.php?id={team_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('player', [])
    except:
        return []

@st.cache_data(ttl=3600)
def get_team_events(team_id, next=True):
    """Mendapatkan jadwal pertandingan (berikutnya/terakhir)."""
    endpoint = "eventsnext" if next else "eventslast"
    url = f"{API_BASE}/{endpoint}.php?id={team_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('events', [])
    except:
        return []

@st.cache_data(ttl=86400)
def get_all_leagues():
    """Mendapatkan daftar semua liga."""
    url = f"{API_BASE}/all_leagues.php"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('leagues', [])
    except:
        return []

@st.cache_data(ttl=86400)
def get_all_countries():
    """Mendapatkan daftar semua negara."""
    url = f"{API_BASE}/all_countries.php"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [c['name_en'] for c in data.get('countries', []) if c.get('name_en')]
    except:
        return []

# --- HALAMAN APLIKASI ---

def render_cari_tim():
    st.header("🔍 Cari tim")
    
    country_list = get_all_countries()
    
    # Input pencarian (Menggunakan nilai dari session state)
    col_input, col_country = st.columns([2, 1])
    with col_input:
        query = st.text_input(
            "Search for a team (e.g., FC Basel)", 
            value=st.session_state.search_query_input,
            key="temp_search_query"
        )
    with col_country:
        country = st.selectbox(
            "Country", 
            [""] + country_list, 
            index=([""] + country_list).index(st.session_state.search_country_input) if st.session_state.search_country_input in ([""] + country_list) else 0,
            key="temp_search_country"
        )
        
    # Fungsi yang dipanggil saat tombol Search ditekan
    def run_search():
        # Update nilai input ke state permanen
        st.session_state.search_query_input = st.session_state.temp_search_query
        st.session_state.search_country_input = st.session_state.temp_search_country
        
        # Panggil API
        st.session_state.search_results = search_teams(
            st.session_state.search_query_input, 
            country=st.session_state.search_country_input
        )
        
    if st.button("Search"):
        run_search()
        
    # Tampilkan hasil pencarian
    if st.session_state.search_results:
        st.markdown("---")
        st.subheader(f"Ditemukan {len(st.session_state.search_results)} Tim")
        
        for i, team in enumerate(st.session_state.search_results):
            col_team_name, col_select = st.columns([3, 1])
            
            with col_team_name:
                if team.get('strTeamBadge'):
                    col_badge, col_name = st.columns([0.5, 3.5])
                    with col_badge:
                        st.image(team['strTeamBadge'], width=30)
                    with col_name:
                        st.write(f"**{team['strTeam']}** ({team.get('strLeague', 'N/A')})")
                else:
                    st.write(f"**{team['strTeam']}** ({team.get('strLeague', 'N/A')})")
            
            with col_select:
                # Tombol Select, menggunakan kunci unik
                if st.button(f"Select", key=f"select_{team.get('idTeam', '')}_{i}"):
                    st.session_state.selected_team = team['idTeam']
                    st.session_state.selected_team_name = team['strTeam']
                    
                    # Navigasi otomatis ke Detail Tim
                    st.session_state.current_page = "📌 Detail tim" 
                    st.rerun()
                    
    elif st.session_state.search_query_input and 'search_results' in st.session_state and len(st.session_state.search_results) == 0:
         st.markdown("---")
         st.write("Tidak ada tim ditemukan dengan kriteria tersebut.")

def render_detail_tim():
    st.header("📌 Detail tim")
    
    if st.session_state.selected_team:
        team_id = st.session_state.selected_team
        team = get_team_details(team_id)
        
        if team and team.get('idTeam'):
            st.subheader(team.get('strTeam', 'Detail Tim'))
            
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                if team.get('strTeamBadge'):
                    st.image(team['strTeamBadge'], width=150, caption=team.get('strTeam'))
                st.write(f"**Didirikan:** {team.get('intFormedYear', 'N/A')}")
                st.write(f"**Olahraga:** {team.get('strSport', 'N/A')}")
                
            with col_info:
                st.write(f"**Liga:** {team.get('strLeague', 'N/A')}")
                st.write(f"**Negara:** {team.get('strCountry', 'N/A')}")
                st.write(f"**Situs Web:** {team.get('strWebsite', 'N/A')}")
                
            st.markdown("---")
            st.subheader("Deskripsi")
            st.markdown(team.get('strDescriptionEN', 'Tidak ada deskripsi tersedia.'))
            
        else:
            st.warning(f"Detail tim dengan ID {team_id} tidak ditemukan.")
    else:
        st.info("Pilih tim dari halaman '🔍 Cari tim' untuk melihat detail.")

def render_daftar_pemain():
    st.header("👨‍🦱 Daftar pemain")
    
    if st.session_state.selected_team and st.session_state.selected_team_name:
        st.subheader(f"Pemain Tim {st.session_state.selected_team_name}")
        players = get_team_players(st.session_state.selected_team)
        
        if players:
            st.success(f"Ditemukan {len(players)} pemain.")
            
            df_players = pd.DataFrame(players)
            
            cols_to_show = ['strPlayer', 'strPosition', 'dateBorn', 'strSigning', 'strNationality']
            filtered_cols = [col for col in cols_to_show if col in df_players.columns]
            
            df_display = df_players[filtered_cols].rename(columns={
                'strPlayer': 'Nama',
                'strPosition': 'Posisi',
                'dateBorn': 'Tgl Lahir',
                'strSigning': 'Tgl Bergabung',
                'strNationality': 'Kebangsaan'
            })
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)

        else:
            st.warning("❌ Tidak ada data pemain yang ditemukan untuk tim ini.") 
            st.caption("Data pemain seringkali terbatas pada liga-liga besar di TheSportsDB.")
    else:
        st.info("Silakan pilih tim dari '🔍 Cari tim' terlebih dahulu.")

def render_jadwal_pertandingan():
    st.header("⚽ Jadwal pertandingan")
    
    if st.session_state.selected_team and st.session_state.selected_team_name:
        st.subheader(f"Jadwal Tim {st.session_state.selected_team_name}")
        
        next_events = get_team_events(st.session_state.selected_team, next=True)
        st.markdown("### Pertandingan Berikutnya")
        
        if next_events:
            for event in next_events:
                st.write(f"**{event.get('strEvent', 'N/A')}** vs **{event.get('strAwayTeam', 'N/A')}**")
                st.caption(f"Liga: {event.get('strLeague', '')}, Tanggal: {event.get('dateEvent', 'N/A')}")
                st.markdown("---")
        else:
            st.info("Tidak ada jadwal pertandingan berikutnya.")

        last_events = get_team_events(st.session_state.selected_team, next=False)
        st.markdown("### Pertandingan Terakhir")
        
        if last_events:
            for event in last_events:
                score = f"{event.get('intHomeScore', 'N/A')} - {event.get('intAwayScore', 'N/A')}"
                st.write(f"**{event.get('strEvent', 'N/A')}** ({score})")
                st.caption(f"Liga: {event.get('strLeague', '')}, Tanggal: {event.get('dateEvent', 'N/A')}")
                st.markdown("---")
        else:
            st.info("Tidak ada data pertandingan terakhir.")
            
    else:
        st.info("Silakan pilih tim dari '🔍 Cari tim' terlebih dahulu.")

def render_liga_negara():
    st.header("🎌 Liga & negara")
    tab_leagues, tab_countries = st.tabs(["Daftar Liga", "Daftar Negara"])
    
    with tab_leagues:
        leagues = get_all_leagues()
        if leagues:
            st.subheader("Semua Liga")
            df_leagues = pd.DataFrame(leagues)
            df_display = df_leagues[['strLeague', 'strSport']].rename(columns={
                'strLeague': 'Nama Liga',
                'strSport': 'Olahraga'
            })
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.warning("Gagal mengambil data liga.")
            
    with tab_countries:
        countries = get_all_countries() 
        if countries:
            st.subheader("Semua Negara")
            df_countries = pd.DataFrame({'Negara': countries})
            st.dataframe(df_countries, use_container_width=True, hide_index=True)
        else:
            st.warning("Gagal mengambil data negara.")

def render_info_stadion():
    st.header("🏟️ Info stadion")
    
    if st.session_state.selected_team:
        team = get_team_details(st.session_state.selected_team)
        
        if team and team.get('strStadium'):
            st.subheader(f"Stadion {team.get('strTeam', 'Tim Terpilih')}")
            
            if team.get('strStadiumThumb'):
                st.image(team['strStadiumThumb'], width=300, caption=team.get('strStadium'))
                
            st.write(f"**Nama Stadion:** {team.get('strStadium', 'N/A')}")
            st.write(f"**Lokasi:** {team.get('strStadiumLocation', 'N/A')}")
            st.write(f"**Kapasitas:** {team.get('intStadiumCapacity', 'N/A')} penonton")
            
        else:
            st.warning("Informasi stadion tidak ditemukan untuk tim ini.")
    else:
        st.info("Pilih tim dari '🔍 Cari tim' terlebih dahulu untuk melihat info stadion.")

def render_home():
    st.header("Home 🏡")
    st.write("Selamat datang di **AthleteIQ**, aplikasi pencarian dan informasi olahraga menggunakan TheSportsDB API.")
    st.write("Gunakan menu navigasi di sidebar untuk mencari tim, melihat detail pemain, jadwal, dan informasi stadion.")
    if st.session_state.selected_team_name:
         st.success(f"Status: Tim aktif saat ini adalah **{st.session_state.selected_team_name}**.")
    else:
         st.info("Status: Tim belum dipilih. Silakan mulai di halaman '🔍 Cari tim'.")

# --- MAIN APP FLOW ---

def main():
    st.title("AthleteIQ") 
    
    if not st.session_state.logged_in:
        # Tampilkan Login/Register
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.header("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", key="btn_login"):
                success, message = login_user(username, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        with tab2:
            st.header("Register")
            username = st.text_input("Username", key="reg_username")
            password = st.text_input("Password", type="password", key="reg_password")
            if st.button("Register", key="btn_register"):
                success, message = register_user(username, password)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    else:
        # --- SIDEBAR (SETELAH LOGIN) ---
        st.sidebar.title(f"Welcome, {st.session_state.username}!")
        if st.sidebar.button("Logout"):
            logout()
            st.rerun()
        
        st.sidebar.markdown("### Navigate")
        
        page_options = [
            "Home", 
            "🔍 Cari tim", 
            "📌 Detail tim", 
            "👨‍🦱 Daftar pemain", 
            "⚽ Jadwal pertandingan", 
            "🎌 Liga & negara", 
            "🏟️ Info stadion"
        ]
        
        # Menggunakan radio button untuk navigasi
        selected_page = st.sidebar.radio(
            "Pilih Halaman", 
            options=page_options,
            index=page_options.index(st.session_state.current_page) if st.session_state.current_page in page_options else 0,
            key="sidebar_navigation"
        )
        st.session_state.current_page = selected_page
        
        st.sidebar.markdown("---")
        
        if st.session_state.selected_team_name:
            st.sidebar.success(f"⚽ Tim Aktif: **{st.session_state.selected_team_name}**")
            st.sidebar.caption(f"ID: {st.session_state.selected_team}") 
        else:
            st.sidebar.warning("Tim Belum Dipilih")
        
        # --- KONTEN HALAMAN UTAMA ---
        if st.session_state.current_page == "Home":
            render_home()
        elif st.session_state.current_page == "🔍 Cari tim":
            render_cari_tim()
        elif st.session_state.current_page == "📌 Detail tim":
            render_detail_tim()
        elif st.session_state.current_page == "👨‍🦱 Daftar pemain":
            render_daftar_pemain()
        elif st.session_state.current_page == "⚽ Jadwal pertandingan":
            render_jadwal_pertandingan()
        elif st.session_state.current_page == "🎌 Liga & negara":
            render_liga_negara()
        elif st.session_state.current_page == "🏟️ Info stadion":
            render_info_stadion()

if __name__ == "__main__":
    main()