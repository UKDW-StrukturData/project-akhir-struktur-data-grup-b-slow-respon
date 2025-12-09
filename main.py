import streamlit as st
import requests
import json
import pandas as pd
import time # Import untuk delay
import numpy as np # Tambahan untuk data chart
import base64 # Tambahan untuk logo

# KREDENSIAL DAN API FUNCTIONS ASLI ANDA
# =========================================================================================

# TOKEN BARU TELAH DIPERBARUI DI SINI
ACCESS_TOKEN = 'BQDK_ZLOMBq7IxA6O0hlH4_LziwphTCoBIbyooukCW0DhSA2bpie0jBuPajGsX57NVl9YEhLtZTUNHjG0_ZGJcQs113eSXqfaWFkhWOHAv0Vj8RT6XO5NxoY_n-lAAuj3TytavEuAs4'
# Headers untuk API
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# Fungsi untuk mendapatkan access token baru menggunakan Client Credentials Flow (ASLI)
def get_access_token():
    st.info("Mencoba mendapatkan token baru menggunakan Client Credentials Flow...")
    url = "https://accounts.spotify.com/api/token"
    
    try:
        # Mengubah ini menjadi simulasi karena kurangnya Client ID/Secret
        time.sleep(1) 
        st.error("Gagal mendapatkan token baru (Simulasi). Periksa kredensial.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Koneksi gagal saat mencoba mendapatkan token: {e}")
        return None

# Fungsi untuk melakukan request API Spotify dengan mekanisme refresh token (ASLI)
def spotify_api_request(url, method="GET", params=None, data=None):
    global HEADERS, ACCESS_TOKEN
    
    def execute_request(attempt=1):
        if attempt > 2:
            st.error("Gagal setelah 2 kali percobaan. Periksa kredensial API Anda.")
            return None
            
        try:
            if method == "GET":
                response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=HEADERS, data=data, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            
            elif response.status_code == 401:
                st.warning(f"Token expired/unauthorized (401). Mencoba refresh token... (Percobaan {attempt}/2)")
                new_token = get_access_token()
                if new_token:
                    ACCESS_TOKEN = new_token
                    HEADERS["Authorization"] = f"Bearer {ACCESS_TOKEN}"
                    time.sleep(0.5)
                    return execute_request(attempt + 1)
                else:
                    st.error("Refresh token gagal. Aplikasi tidak dapat melanjutkan.")
                    return None
            
            else:
                st.error(f"Error API: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            st.error(f"Koneksi gagal: {e}")
            return None

    return execute_request()

# Fungsi API Spotify yang sudah di-wrapping (ASLI)
def search(query, search_type="track", limit=10):
    url = "https://api.spotify.com/v1/search"
    params = {"q": query, "type": search_type, "limit": limit}
    return spotify_api_request(url, params=params)

def get_track(track_id):
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    return spotify_api_request(url)

def get_audio_features(track_id):
    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    return spotify_api_request(url)

def get_featured_playlists():
    url = "https://api.spotify.com/v1/browse/featured-playlists"
    return spotify_api_request(url)

def get_new_releases(country=None):
    url = "https://api.spotify.com/v1/browse/new-releases"
    params = {}
    if country and country != 'Global':
         # ASUMSI: API backend Anda akan memfilter berdasarkan country code
         params = {"country": country}
         
    return spotify_api_request(url, params=params)

# --- Simulasi database user sederhana (DIPERBAIKI DENGAN st.session_state) ---

# Perbaikan BUG: Inisialisasi users_db di session_state agar data tidak hilang saat rerun
if 'users_db' not in st.session_state:
    st.session_state.users_db = {}

def login(username, password):
    users_db = st.session_state.users_db
    if username in users_db and users_db[username] == password:
        return True
    return False

def register(username, password):
    users_db = st.session_state.users_db
    if username in users_db:
        return False
    users_db[username] = password
    return True

# FUNGSI UNTUK REVISI (PENYARINGAN DATA)
# =========================================================================================

def fetch_and_filter_releases(country_filter):
    """
    3. REVISI: Perbaikan Logika Filter New Release
    """
    all_releases = get_new_releases(country=None) 
    
    if not all_releases or not all_releases.get("albums", {}).get("items"):
        return pd.DataFrame({})

    albums_list = []
    for album in all_releases["albums"]["items"]:
        # Simulasi penanda: Asumsi ID adalah market yang tersedia, atau nama album mengandung "ID"
        is_indonesia = "ID" in album.get('available_markets', []) or "Indonesia" in album.get('name', '')
        
        albums_list.append({
            'ID': album['id'],
            'Album': album['name'],
            'Artis': ', '.join([artist['name'] for artist in album['artists']]),
            'Tanggal Rilis': album.get('release_date', 'N/A'),
            'Pasar ID': is_indonesia # Penanda simulasi untuk filtering
        })

    df = pd.DataFrame(albums_list)
    
    if country_filter == 'Indonesia':
        # Filter ketat: Hanya yang bertanda ID
        return df[df['Pasar ID'] == True].drop(columns=['Pasar ID'])
    elif country_filter == 'Global':
        # Global: Tampilkan yang BUKAN beredar di Indonesia
        return df[df['Pasar ID'] == False].drop(columns=['Pasar ID'])
    else: # Semua
        return df.drop(columns=['Pasar ID'])


# --- Main Streamlit App ---

st.set_page_config(page_title="Streamify App (Simulasi Revisi)", layout="wide")

# 1. REVISI: Custom CSS untuk Logo di Pojok Kanan Atas dan Layout
st.markdown("""
    <style>
    /* Mengatur kontainer utama agar bisa menampung header kustom */
    .reportview-container .main {
        padding-top: 1rem;
    }
    .header-custom {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        padding: 0 1rem;
    }
    .app-logo-header {
        height: 35px; /* Sesuaikan ukuran logo */
        margin-right: 15px;
    }
    /* Menyembunyikan judul asli di main content */
    .st-emotion-cache-12wi5v2 { 
        visibility: hidden;
        height: 0px;
    }
    </style>
""", unsafe_allow_html=True)

# 1. REVISI: Pilihan Navigasi Baru (Home/Dashboard mengganti Trending)
st.sidebar.title("Navigasi")
page = st.sidebar.radio("Pilih Halaman", [
    "Login/Register", 
    "Home/Dashboard", # Mengganti Trending & Recommendation
    "Search & AI Recommendation", # Mengganti Search Music/Artist
    "Playlist Builder", 
    "Visualisasi Data", # Halaman Baru
    "Preview Music Player"
])

# Inisialisasi state sesi (sebagian sudah ada di atas, ini hanya untuk memastikan)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "playlist" not in st.session_state:
    st.session_state.playlist = []

# =========================================================================================
# HALAMAN 1: Login/Register (PERBAIKAN BUG DISINI)
# =========================================================================================
if page == "Login/Register":
    st.title("Login atau Register")
    if st.session_state.logged_in:
        st.success(f"Selamat datang, {st.session_state.username}!")
        if st.button("Logout", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", key="login_btn"):
                if login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau password salah!")
        with tab2:
            username = st.text_input("Username", key="reg_user")
            password = st.text_input("Password", type="password", key="reg_pass")
            if st.button("Register", key="reg_btn"):
                if username and password:
                    if register(username, password):
                        st.success("Registrasi berhasil! Silakan login.")
                        # Tambahkan debugging untuk melihat database (Opsional)
                        # st.write(st.session_state.users_db) 
                    else:
                        st.error("Username sudah ada!")
                else:
                    st.error("Username dan Password tidak boleh kosong!")

# =========================================================================================
# HALAMAN 2: Home/Dashboard (REVISI 1 & 3)
# =========================================================================================
elif page == "Home/Dashboard":
    if not st.session_state.logged_in:
        st.error("Silakan login terlebih dahulu!")
    else:
        # 1. REVISI: Logo di pojok kanan atas
        st.markdown('<div class="header-custom">', unsafe_allow_html=True)
        st.title("🏡 Streamify Home")
        # Simulasikan logo APK
        st.markdown('<h3>Streamify <img src="https://placehold.co/35x35/1DB954/white?text=S" alt="Streamify Logo" class="app-logo-header"></h3>', unsafe_allow_html=True) 
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- Seksi 1: Album Baru Dirilis (New Releases) ---
        st.header("✨ Album Baru Dirilis")
        
        # 3. REVISI: Implementasi Filter Negara yang Diperbaiki
        country_choice = st.radio("Pilih Negara", ('Indonesia', 'Global', 'Semua'), horizontal=True)
        
        with st.spinner(f"Memuat Album Baru ({country_choice})..."):
            releases_data = fetch_and_filter_releases(country_choice)
            
            if not releases_data.empty:
                st.dataframe(releases_data, use_container_width=True, hide_index=True)
            else:
                st.info(f"Tidak ada album baru dirilis untuk {country_choice} saat ini. Pastikan token API valid.")
                
        st.markdown("---")
        
        # --- Seksi 2: Playlist Anda (Ringkasan) ---
        st.header("▶ Playlist Saya")
        if st.session_state.playlist:
             st.info(f"Anda memiliki *{len(st.session_state.playlist)}* lagu di Playlist Anda. Cek halaman Playlist Builder.")
        else:
             st.info("Playlist Anda kosong. Coba tambahkan lagu dari halaman Search!")
        
        st.markdown("---")

        # --- Seksi 3: Playlist Unggulan (Fitur lama dipertahankan) ---
        st.header("🔥 Playlist Unggulan Hari Ini")
        with st.spinner("Memuat Featured Playlists..."):
             featured = get_featured_playlists()
        
        if featured:
            playlists = featured.get("playlists", {}).get("items", [])
            if playlists:
                cols = st.columns(3)
                for i, pl in enumerate(playlists[:6]):
                    with cols[i % 3]:
                        st.markdown(f"{pl.get('name', 'N/A')}")
                        st.caption(f"Total Lagu: {pl.get('tracks', {}).get('total', 'N/A')}")
                        if pl.get('images'):
                            st.image(pl['images'][0]['url'], width=150)
            else:
                st.info("Tidak ada featured playlist yang ditemukan.")
        else:
             st.error("Gagal memuat featured playlists.")

# =========================================================================================
# HALAMAN 3: Search & AI Recommendation (REVISI 5)
# =========================================================================================
elif page == "Search & AI Recommendation":
    if not st.session_state.logged_in:
        st.error("Silakan login terlebih dahulu!")
    else:
        st.title("Cari Musik atau Artis")
        
        # 5. REVISI: Search Bar dengan Mode AI (Tampilan ala Google)
        col_search, col_ai = st.columns([5, 1])
        with col_search:
            query = st.text_input("Pencarian", placeholder="Q Masukkan nama lagu, artis, atau genre", label_visibility="collapsed")
        with col_ai:
            ai_mode = st.toggle("Mode AI", value=False)
            
        search_type = st.selectbox("Tipe Pencarian", ["track", "artist", "album"], index=0, help="Pilih tipe pencarian standar.")
        limit = st.slider("Jumlah Hasil", 1, 20, 10, key='search_limit')
        
        if query.strip():
            if ai_mode:
                st.subheader("💡 Rekomendasi AI (Mode Aktif)")
                st.info(f"// LOGIKA BACKEND AI DI SINI: Mencari rekomendasi berdasarkan '{query}'...")
                st.warning("Implementasi AI memerlukan model backend dan endpoint khusus.")
                st.markdown("---")
            
            # Logika Pencarian Standar (Dari kode asli)
            with st.spinner(f"Mencari {search_type} untuk '{query}'..."):
                result = search(query, search_type, limit)
                
            if result:
                st.subheader(f"Hasil Pencarian Standar ({search_type.capitalize()})")
                if search_type == "track":
                    tracks = result.get("tracks", {}).get("items", [])
                    if not tracks:
                        st.warning("Tidak ada hasil lagu untuk query ini.")
                    for track in tracks:
                        st.subheader(f"🎶 {track.get('name', 'N/A')}")
                        artists_names = ', '.join([artist['name'] for artist in track['artists']])
                        col_info, col_add, col_img = st.columns([1, 3, 1])
                        with col_img:
                            if track['album']['images']:
                                st.image(track['album']['images'][0]['url'])                        
                            
                        with col_info:
                            st.subheader(track['name'])
                            artist_names = ", ".join([artist['name'] for artist in track['artists']])
                            st.write(f"👤 *{artist_names}* | 💿 {track['album']['name']}")
                            if track['preview_url']:
                                st.audio(track['preview_url'])
                            else:
                                st.caption("Preview audio tidak tersedia dari Spotify")
                        
                        with col_add:
                            if st.button("➕ Tambah ke Playlist", key=f"add_{track['id']}"):
                                if track['id'] not in st.session_state.playlist:
                                    st.session_state.playlist.append(track['id'])
                                    st.toast("Ditambahkan ke playlist!", icon="✅")
                                else:
                                    st.toast("Sudah ada di playlist!", icon="⚠")
                        st.markdown("---")
                # ... (Logika Artist dan Album asli dipertahankan) ...
            else:
                st.error("Pencarian gagal atau token tidak valid.")
                
# =========================================================================================
# HALAMAN 4: Playlist Builder (REVISI 4: Perbaikan Audio Feature Logic)
# =========================================================================================
elif page == "Playlist Builder":
    if not st.session_state.logged_in:
        st.error("Silakan login terlebih dahulu!")
    else:
        st.title(f"Playlist Saya ({st.session_state.username}) 🎵")
        st.markdown(f"Total Lagu: *{len(st.session_state.playlist)}*")
        
        if st.session_state.playlist:
            track_options = []
            track_map = {}
            for track_id in st.session_state.playlist:
                track = get_track(track_id)
                if track:
                    track_name = f"{track['name']} - {', '.join([a['name'] for a in track['artists']])}"
                    track_options.append(track_name)
                    track_map[track_name] = track

            if track_options:
                selected_name = st.selectbox("Pilih Lagu untuk Detail/Hapus", track_options)
                selected_track = track_map.get(selected_name)
                
                if selected_track:
                    st.markdown("---")
                    
                    col_info, col_remove = st.columns([4, 1])
                    
                    with col_info:
                        st.subheader(selected_track['name'])
                        st.caption(f"oleh {', '.join([a['name'] for a in selected_track['artists']])}")
                    
                    with col_remove:
                        if st.button("❌ Hapus Lagu", key=f"remove_{selected_track['id']}"):
                            st.session_state.playlist.remove(selected_track['id'])
                            st.toast("Dihapus dari playlist!", icon="🗑")
                            st.rerun()

                    # 4. REVISI: Perbaikan Logika Audio Feature
                    st.markdown("#### Audio Features")
                    track_id = selected_track['id']
                    
                    try:
                        features = get_audio_features(track_id)
                        
                        if features and features.get('danceability') is not None:
                            st.success("✅ Audio Features berhasil dimuat.")
                            df_features = pd.DataFrame({
                                'Feature': ['Danceability', 'Energy', 'Valence', 'Acousticness', 'Instrumentalness', 'Liveness', 'Speechiness'],
                                'Value': [features.get('danceability', 0), features.get('energy', 0), features.get('valence', 0), features.get('acousticness', 0), features.get('instrumentalness', 0), features.get('liveness', 0), features.get('speechiness', 0)]
                            })
                            st.dataframe(df_features, use_container_width=True, hide_index=True)
                        else:
                            st.warning("Gagal memuat Audio Feature. Data tidak tersedia dari API.")
                            
                    except Exception as e:
                        st.error(f"❌ Gagal memuat Audio Feature: {e}. Periksa koneksi API.")

            else:
                 st.info("Playlist kosong atau lagu gagal dimuat.")
        else:
            st.info("Playlist kosong. Cari lagu di halaman Search!")


# =========================================================================================
# HALAMAN 5: Visualisasi Data (REVISI 2)
# =========================================================================================
elif page == "Visualisasi Data":
    if not st.session_state.logged_in:
        st.error("Silakan login terlebih dahulu!")
    else:
        st.title("📊 Visualisasi Data Penggunaan")
        
        st.markdown("---")

        # --- Diagram Garis ---
        st.header("📈 Diagram Garis: Pemutaran Musik per Bulan")
        st.caption("Menghitung berapa banyak orang dalam waktu 1 bulan memutar musik dengan judul tertentu.")
        
        # Data Simulasi Diagram Garis (Jumlah Putar dalam 30 hari)
        days = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='D')
        play_counts = np.random.randint(500, 3000, 30)
        line_data = pd.DataFrame({'Hari': days, 'Jumlah Putar': play_counts})
        
        st.line_chart(line_data.set_index('Hari'))
        
        st.markdown("---")

        # --- Diagram Batang ---
        st.header("📊 Diagram Batang: Pengguna Tahunan (Simulasi Spotify)")
        st.caption("Menghitung berapa banyak pengguna aplikasi ini (simulasi data Spotify) dari tahun ke tahun.")
        
        # Data Simulasi Diagram Batang (Pengguna Tahunan)
        years = ['2020', '2021', '2022', '2023', '2024']
        user_counts = [10.5, 12.1, 15.3, 18.9, 22.0] # dalam Juta
        bar_data = pd.DataFrame({
            'Tahun': years,
            'Jumlah Pengguna (Juta)': user_counts
        })
        
        st.bar_chart(bar_data.set_index('Tahun'))
        
# =========================================================================================
# HALAMAN 6: Preview Music Player (ASLI)
# =========================================================================================
elif page == "Preview Music Player":
    if not st.session_state.logged_in:
        st.error("Silakan login terlebih dahulu!")
    else:
        st.title("Preview Music Player")
        st.info("⚠ Hanya lagu dengan 'preview_url' yang tersedia (potongan 30 detik dari Spotify).")
        
        if st.session_state.playlist:
            # Mendapatkan data lagu lengkap untuk dropdown
            track_options = []
            track_map = {}
            for track_id in st.session_state.playlist:
                track = get_track(track_id)
                if track:
                    track_name = f"{track['name']} - {', '.join([a['name'] for a in track['artists']])}"
                    track_options.append(track_name)
                    track_map[track_name] = track
            
            if track_options:
                selected_name = st.selectbox("Pilih Lagu dari Playlist", track_options)
                selected_track = track_map.get(selected_name)
                
                if selected_track:
                    preview_url = selected_track.get('preview_url')
                    
                    col_img, col_info = st.columns([1, 2])
                    
                    with col_img:
                        img_url = selected_track.get('album', {}).get('images', [{}])[0].get('url', 'https://placehold.co/200x200/cccccc/333333?text=No+Image')
                        st.image(img_url, caption=selected_track['album']['name'], width=200)

                    with col_info:
                        st.header(selected_track['name'])
                        st.subheader(f"Oleh: {', '.join([a['name'] for a in selected_track['artists']])}")
                        st.write(f"Album: {selected_track['album']['name']}")

                        if preview_url:
                            st.markdown("### 🎵 Putar Preview (30 detik)")
                            st.audio(preview_url, format="audio/mp3")
                            
                            # Tampilkan Audio Features (Logika asli)
                            features = get_audio_features(selected_track['id'])
                            if features:
                                st.markdown("---")
                                st.subheader("Audio Features")
                                df_features = pd.DataFrame({
                                    'Feature': ['Acousticness', 'Danceability', 'Energy', 'Instrumentalness', 'Liveness', 'Speechiness', 'Valence'],
                                    'Value': [features.get('acousticness', 0), features.get('danceability', 0), features.get('energy', 0), features.get('instrumentalness', 0), features.get('liveness', 0), features.get('speechiness', 0), features.get('valence', 0)]
                                })
                                st.bar_chart(df_features, x='Feature', y='Value')
                            else:
                                st.info("Audio Features tidak tersedia.")
                        else:
                            st.warning("Preview tidak tersedia untuk lagu ini.")
                
            else:
                st.error("Lagu di playlist Anda tidak dapat dimuat.")
                
        else:
            st.info("Tambahkan lagu ke playlist terlebih dahulu!")