import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import numpy as np 

# --- KONFIGURASI API (WAJIB DIISI) ---
CLIENT_ID = "7b9a0310b1734b728b21d0e84199c8c5" 
CLIENT_SECRET = "ef6212c353da4cca99e71b5bb2b7cfee"

# Inisialisasi Spotipy
try:
    auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    api_connected = True
    st.sidebar.success("Koneksi Spotify API Berhasil ✅")
except Exception as e:
    api_connected = False
    st.sidebar.error(f"Koneksi Spotify Gagal: {e}")

# --- SETUP SESSION STATE ---
if "users_db" not in st.session_state:
    # PERBAIKAN LOGIN: Tambahkan 'livta' agar bisa login sesuai gambar
    st.session_state.users_db = {"admin": "12345", "livta": "12345", "odan@gmail.com": "12345"} # Menambahkan odan@gmail.com dan livta
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "playlist" not in st.session_state:
    st.session_state.playlist = []

# --- FUNGSI AUTH ---
def login_user(username, password):
    db = st.session_state.users_db
    if username in db and db[username] == password:
        return True
    return False

def register_user(username, password):
    if username in st.session_state.users_db:
        return False
    st.session_state.users_db[username] = password
    return True

# --- HALAMAN UTAMA ---
st.set_page_config(page_title="Streamify Music", layout="wide", page_icon="🎵")

# Sidebar
st.sidebar.title("🎵 Streamify")
if st.session_state.logged_in:
    # Username login sudah disesuaikan agar bisa login dengan 'livta' atau 'odan@gmail.com'
    st.sidebar.write(f"Halo, **{st.session_state.username}**!")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# Memastikan menu hanya berisi yang ada kodenya
# PERUBAHAN MENU: MENGGANTI 'Audio Features' dan 'Trending' dengan 'New Releases'
menu = st.sidebar.radio("Menu", ["Home", "Search", "My Playlist", "New Releases"]) 

# Pengecekan Login untuk akses menu selain Home
if not st.session_state.logged_in and menu != "Home":
    st.warning("Silakan Login terlebih dahulu di menu Home.")
    st.stop()

# -------------------------------------------------------------------------
# --- HALAMAN 1: HOME (LOGIN/REGISTER) ---
# -------------------------------------------------------------------------
if menu == "Home":
    st.title("Selamat Datang di Streamify 🎧")
    
    if st.session_state.logged_in:
        st.success("Anda sudah login! Silakan gunakan menu di sebelah kiri untuk mulai mendengarkan musik.")
        st.info("💡 Tips: Pergi ke menu 'Search' untuk mencari lagu.")
    else:
        st.header("Login atau Register")
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.subheader("Login")
            user_in = st.text_input("Username", key="l_user")
            pass_in = st.text_input("Password", type="password", key="l_pass")
            if st.button("Masuk"):
                # Menghilangkan error "Username atau password salah!" jika login dengan 'livta'
                if login_user(user_in, pass_in):
                    st.session_state.logged_in = True
                    st.session_state.username = user_in
                    st.success("Login Berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau Password salah!") 

        with tab2:
            st.subheader("Daftar Akun Baru")
            new_user = st.text_input("Buat Username/Email", key="r_user")
            new_pass = st.text_input("Buat Password", type="password", key="r_pass")
            if st.button("Daftar"):
                if new_user and new_pass:
                    if register_user(new_user, new_pass):
                        st.success("Akun berhasil dibuat! Silakan login.")
                    else:
                        st.error("Username sudah dipakai.")
                else:
                    st.warning("Data tidak boleh kosong.")

# -------------------------------------------------------------------------
# --- HALAMAN 2: SEARCH ---
# -------------------------------------------------------------------------
elif menu == "Search":
    st.title("Cari Lagu atau Artis 🔍")
    
    if not api_connected:
        st.error("API Belum terkoneksi. Fitur ini tidak dapat digunakan.")
    else:
        query = st.text_input("Ketik judul lagu atau nama artis...", placeholder="Contoh: Tulus, Hati-Hati di Jalan")
        search_type = st.selectbox("Tipe", ["track", "artist"])
        
        if query:
            try:
                results = sp.search(q=query, limit=10, type=search_type)
                
                if search_type == "track":
                    tracks = results['tracks']['items']
                    for track in tracks:
                        col1, col2, col3 = st.columns([1, 4, 1])
                        
                        with col1:
                            if track['album']['images']:
                                st.image(track['album']['images'][0]['url'])
                        
                        with col2:
                            st.subheader(track['name'])
                            artist_names = ", ".join([artist['name'] for artist in track['artists']])
                            st.write(f"👤 **{artist_names}** | 💿 {track['album']['name']}")
                            if track['preview_url']:
                                st.audio(track['preview_url'])
                            else:
                                st.caption("Preview audio tidak tersedia dari Spotify")
                        
                        with col3:
                            if st.button("➕ Add", key=f"add_{track['id']}"):
                                if track['id'] not in st.session_state.playlist:
                                    st.session_state.playlist.append(track['id'])
                                    st.toast("Lagu ditambahkan!", icon="✅")
                                else:
                                    st.toast("Lagu sudah ada di playlist", icon="⚠️")
                        st.divider()
                        
                elif search_type == "artist":
                    artists = results['artists']['items']
                    for artist in artists:
                        st.subheader(artist['name'])
                        col_img, col_info = st.columns([1, 3])
                        with col_img:
                             if artist['images']:
                                st.image(artist['images'][0]['url'], width=150)
                        with col_info:
                             st.write(f"Followers: **{artist['followers']['total']:,}**")
                             st.write(f"Genre: **{', '.join(artist['genres']).title()}**")
                        st.divider()
                        
            except Exception as e:
                st.error(f"Error saat mencari: {e}")

# -------------------------------------------------------------------------
# --- HALAMAN 3: MY PLAYLIST ---
# -------------------------------------------------------------------------
elif menu == "My Playlist":
    st.title("Playlist Saya 🎵")
    
    if not st.session_state.playlist:
        st.info("Playlist masih kosong. Cari lagu dulu yuk!")
        
    elif not api_connected:
        st.warning("Playlist hanya menampilkan ID lagu. Koneksi API diperlukan untuk detail.")
        st.code(st.session_state.playlist)
    else:
        tracks_to_remove = []
        need_rerun = False

        for i, track_id in enumerate(st.session_state.playlist):
            try:
                track = sp.track(track_id)
                
                with st.container():
                    col1, col2, col3 = st.columns([1, 4, 1])
                    with col1:
                        if track['album']['images']:
                            st.image(track['album']['images'][min(len(track['album']['images']) - 1, 2)]['url']) 
                    with col2:
                        artist_names = ", ".join([artist['name'] for artist in track['artists']])
                        st.write(f"**{track['name']}** - {artist_names}")
                        if track['preview_url']:
                            st.audio(track['preview_url'])
                        else:
                            st.caption("Preview audio tidak tersedia.")
                    with col3:
                        if st.button("❌ Hapus", key=f"del_{track_id}"):
                            st.session_state.playlist.remove(track_id)
                            st.toast("Lagu dihapus!", icon="🗑️")
                            st.rerun() 
                st.divider()
            
            except spotipy.exceptions.SpotifyException:
                tracks_to_remove.append(track_id)
                st.warning(f"Lagu dengan ID **{track_id}** tidak valid dan akan dihapus dari playlist.")
                need_rerun = True
            except Exception as e:
                st.error(f"Gagal memuat info lagu: {e}")

        if tracks_to_remove:
            for track_id in tracks_to_remove:
                if track_id in st.session_state.playlist:
                    st.session_state.playlist.remove(track_id)
        
        if need_rerun:
            st.rerun()

# -------------------------------------------------------------------------
# --- HALAMAN 4: NEW RELEASES (Menggantikan Audio Features & Trending) ---
# -------------------------------------------------------------------------
elif menu == "New Releases":
    st.title("Album Baru Dirilis 💿")
    st.info("Menampilkan album-album terbaru yang dirilis di Spotify.")

    if not api_connected:
        st.error("API Belum terkoneksi. Fitur ini tidak dapat digunakan.")
        st.stop()
        
    try:
        # Pilihan negara (Contoh: ID dan US lebih sering memiliki data)
        countries = {
            "Indonesia": "ID"
        }
        country_name = st.selectbox("Pilih Negara", list(countries.keys()))
        country_code = countries[country_name]
        
        # Panggil API untuk New Releases (Endpoint yang stabil untuk Client Credentials)
        results = sp.new_releases(country=country_code, limit=6)
        
        st.subheader(f"Album Baru di {country_name}")
        
        # Tampilkan dalam kolom
        cols = st.columns(3)
        
        if results and 'albums' in results and 'items' in results['albums']:
            albums = results['albums']['items']
            for i, album in enumerate(albums):
                with cols[i % 3]:
                    st.markdown(f"**{album['name']}**")
                    artist_names = ", ".join([artist['name'] for artist in album['artists']])
                    st.caption(f"Oleh: {artist_names}")
                    
                    if album['images']:
                        st.image(album['images'][0]['url'], width=150)
                    
                    # Tambahkan tautan ke Spotify eksternal
                    if 'spotify' in album['external_urls']:
                        st.markdown(f"[Lihat di Spotify]({album['external_urls']['spotify']})")
                    st.markdown("---")
        else:
            st.warning("Tidak ada album baru yang ditemukan untuk negara ini.")
            
    except spotipy.exceptions.SpotifyException as e:
        # Menangani error API umum (sekarang harusnya jarang terjadi)
        st.error(f"Terjadi kesalahan saat memuat New Releases: {e}")
    except Exception as e:
        st.error(f"Kesalahan umum: {e}")