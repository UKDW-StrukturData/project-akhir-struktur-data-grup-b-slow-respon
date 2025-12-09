import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import numpy as np
import io # Diperlukan untuk export file
import plotly.express as px # Diperlukan untuk visualisasi

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

# --- FUNGSI BARU UNTUK MENDAPATKAN AUDIO FEATURES ---
@st.cache_data
def get_audio_features(track_ids):
    if not api_connected or not track_ids:
        return pd.DataFrame()
    try:
        features = sp.audio_features(track_ids)
        # Menghapus entri 'None' yang mungkin terjadi pada track yang tidak valid
        valid_features = [f for f in features if f is not None]
        if valid_features:
            # Mengambil informasi tambahan track
            tracks = sp.tracks(track_ids)
            track_info = {}
            for track in tracks['tracks']:
                if track:
                    track_info[track['id']] = {
                        'name': track['name'],
                        'artist': ", ".join([artist['name'] for artist in track['artists']])
                    }
            
            df = pd.DataFrame(valid_features)
            # Menambahkan nama lagu dan artis
            df['name'] = df['id'].apply(lambda x: track_info.get(x, {}).get('name', 'N/A'))
            df['artist'] = df['id'].apply(lambda x: track_info.get(x, {}).get('artist', 'N/A'))
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal memuat Audio Features: {e}")
        return pd.DataFrame()

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
# PENAMBAHAN MENU BARU
menu = st.sidebar.radio("Menu", ["Home", "Search", "My Playlist", "New Releases", "Visualisasi", "Rekomendasi AI"])

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
# --- HALAMAN 3: MY PLAYLIST (Diperbarui dengan Export) ---
# -------------------------------------------------------------------------
elif menu == "My Playlist":
    st.title("Playlist Saya 🎵")
    if not st.session_state.playlist:
        st.info("Playlist masih kosong. Cari lagu dulu yuk!")
    elif not api_connected:
        st.warning("Playlist hanya menampilkan ID lagu. Koneksi API diperlukan untuk detail.")
        st.code(st.session_state.playlist)
    else:
        # --- EXPORT PLAYLIST KE CSV/JSON (FITUR BARU) ---
        playlist_data = get_audio_features(st.session_state.playlist)
        
        if not playlist_data.empty:
            st.subheader("Export Playlist")
            col_csv, col_json = st.columns(2)
            with col_csv:
                csv = playlist_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Export ke CSV",
                    data=csv,
                    file_name='streamify_playlist.csv',
                    mime='text/csv',
                )
            with col_json:
                json_data = playlist_data.to_json(orient='records').encode('utf-8')
                st.download_button(
                    label="⬇️ Export ke JSON",
                    data=json_data,
                    file_name='streamify_playlist.json',
                    mime='application/json',
                )
            st.markdown("---")
        # ----------------------------------------------
        
        st.subheader("Daftar Lagu di Playlist")
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
# --- HALAMAN 4: NEW RELEASES ---
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
            "Indonesia": "ID", "Amerika Serikat": "US", "Global (Default)": ""
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

# -------------------------------------------------------------------------
# --- HALAMAN 5: VISUALISASI DATA (FITUR BARU) ---
# -------------------------------------------------------------------------
elif menu == "Visualisasi":
    st.title("Visualisasi Data Playlist 📊")
    if not api_connected:
        st.error("Koneksi API diperlukan untuk fitur ini.")
        st.stop()
        
    if not st.session_state.playlist:
        st.info("Playlist Anda kosong. Tambahkan lagu dari menu 'Search' untuk melihat visualisasi.")
        st.stop()
    
    st.info("Fitur ini menganalisis karakteristik audio (Audio Features) dari lagu-lagu di Playlist Anda.")
    
    # Ambil data Audio Features
    df_features = get_audio_features(st.session_state.playlist)
    
    if df_features.empty:
        st.warning("Gagal memuat data fitur audio. Mungkin ada masalah dengan ID lagu.")
        st.stop()

    st.subheader("Data Fitur Audio")
    st.dataframe(df_features[['name', 'artist', 'danceability', 'energy', 'valence', 'tempo', 'acousticness']])
    
    st.markdown("---")
    
    # Pilihan visualisasi
    visualization_type = st.selectbox("Pilih Tipe Visualisasi", ["Rata-rata Fitur", "Scatter Plot Fitur"])
    
    # Visualisasi Rata-rata Fitur
    if visualization_type == "Rata-rata Fitur":
        st.subheader("Rata-rata Karakteristik Audio Playlist")
        
        # Pilih fitur yang relevan untuk Bar Chart
        features_to_plot = ['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence']
        
        # Hitung rata-rata
        df_mean = df_features[features_to_plot].mean().reset_index()
        df_mean.columns = ['Feature', 'Average Value']
        
        # Buat Bar Chart menggunakan Plotly
        fig = px.bar(
            df_mean, 
            x='Feature', 
            y='Average Value', 
            color='Feature',
            title='Rata-Rata Fitur Audio Playlist',
            labels={'Average Value': 'Nilai Rata-Rata (0.0 - 1.0)', 'Feature': 'Fitur Audio'},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Nilai 1.0 menunjukkan karakteristik sangat kuat (misalnya danceability tinggi berarti lagu sangat cocok untuk menari).")
        

    # Visualisasi Scatter Plot (untuk perbandingan 2 fitur)
    elif visualization_type == "Scatter Plot Fitur":
        st.subheader("Hubungan Antar Fitur Audio Lagu")
        
        # Fitur yang bisa dipilih
        available_features = ['danceability', 'energy', 'valence', 'tempo', 'acousticness', 'loudness']
        
        col_x, col_y = st.columns(2)
        with col_x:
            feature_x = st.selectbox("Pilih Fitur X", available_features, index=0)
        with col_y:
            # Pastikan fitur Y berbeda dari X
            default_index_y = 1 if available_features[0] == feature_x else 0
            feature_y = st.selectbox("Pilih Fitur Y", available_features, index=default_index_y)

        # Buat Scatter Plot menggunakan Plotly
        fig = px.scatter(
            df_features, 
            x=feature_x, 
            y=feature_y, 
            hover_data=['name', 'artist'],
            color='artist',
            title=f'Scatter Plot: {feature_x.title()} vs {feature_y.title()}',
            height=550
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Setiap titik merepresentasikan satu lagu, dengan sumbu X adalah **{feature_x.title()}** dan sumbu Y adalah **{feature_y.title()}**.")
        

# -------------------------------------------------------------------------
# --- HALAMAN 6: REKOMENDASI AI (FITUR BARU) ---
# -------------------------------------------------------------------------
elif menu == "Rekomendasi AI":
    st.title("Rekomendasi Lagu Berdasarkan Playlist 🧠")
    
    if not api_connected:
        st.error("Koneksi API diperlukan untuk fitur ini.")
        st.stop()
        
    if not st.session_state.playlist:
        st.info("Playlist Anda kosong. Tambahkan lagu terlebih dahulu untuk mendapatkan rekomendasi.")
        st.stop()

    st.info("Fitur ini merekomendasikan lagu baru dari Spotify berdasarkan lagu-lagu yang sudah ada di Playlist Anda (Seed Tracks).")
    
    # Ambil hingga 5 ID lagu pertama sebagai 'seed'
    seed_tracks = st.session_state.playlist[:5]
    
    st.subheader(f"Lagu yang Dijadikan Referensi ({len(seed_tracks)} Lagu)")
    # Menampilkan nama lagu referensi
    seed_track_names = []
    try:
        tracks = sp.tracks(seed_tracks)
        for track in tracks['tracks']:
            if track:
                artist_names = ", ".join([artist['name'] for artist in track['artists']])
                seed_track_names.append(f"- **{track['name']}** oleh {artist_names}")
    except Exception:
        st.warning("Gagal memuat detail lagu referensi.")

    st.markdown("\n".join(seed_track_names))
    st.markdown("---")

    # Ambil rekomendasi dari Spotify API
    try:
        recommendations = sp.recommendations(seed_tracks=seed_tracks, limit=10)
        
        st.subheader("Rekomendasi untuk Anda")
        
        if recommendations and 'tracks' in recommendations and recommendations['tracks']:
            for track in recommendations['tracks']:
                col1, col2, col3 = st.columns([1, 4, 1])
                with col1:
                    if track['album']['images']:
                        st.image(track['album']['images'][0]['url'])

                with col2:
                    st.write(f"**{track['name']}**")
                    artist_names = ", ".join([artist['name'] for artist in track['artists']])
                    st.caption(f"👤 {artist_names} | 💿 {track['album']['name']}")
                    if track['preview_url']:
                        st.audio(track['preview_url'])
                    else:
                        st.caption("Preview audio tidak tersedia.")
                
                with col3:
                    if st.button("➕ Add", key=f"rec_add_{track['id']}"):
                        if track['id'] not in st.session_state.playlist:
                            st.session_state.playlist.append(track['id'])
                            st.toast("Rekomendasi ditambahkan!", icon="✅")
                            # Tidak perlu rerun, hanya tampilkan toast
                        else:
                            st.toast("Lagu sudah ada di playlist", icon="⚠️")
                st.divider()
        else:
            st.warning("Tidak ada rekomendasi lagu yang ditemukan. Coba tambahkan lebih banyak lagu ke playlist Anda.")

    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Terjadi kesalahan saat memuat rekomendasi: {e}")
    except Exception as e:
        st.error(f"Kesalahan umum: {e}")