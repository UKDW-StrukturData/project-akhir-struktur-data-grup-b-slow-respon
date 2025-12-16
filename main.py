import streamlit as st
import json
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import os

# =========================================================================================
# 1. KONFIGURASI AI & DATABASE USER
# =========================================================================================
GEMINI_API_KEY = "AIzaSyDl-DXlC2bRLSyhHrKAr7A_UYGPmHGopBc"
genai.configure(api_key=GEMINI_API_KEY)

USER_DB_FILE = 'users.json'

def load_users():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USER_DB_FILE, 'w') as f:
        json.dump(users, f)

# Inisialisasi Session State
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None
if 'my_playlist' not in st.session_state: st.session_state.my_playlist = []

# =========================================================================================
# 2. LOAD DATA MUSIK
# =========================================================================================
@st.cache_data
def load_music_data():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            df = pd.DataFrame(json.load(f))
            df['album_release_date'] = pd.to_datetime(df['album_release_date'], errors='coerce')
            return df
    except:
        return pd.DataFrame()

df_master = load_music_data()

# =========================================================================================
# 3. ANTARMUKA UTAMA
# =========================================================================================
st.set_page_config(page_title="Streamify Pro AI", layout="wide")

# Sidebar Navigasi
if st.session_state.logged_in:
    st.sidebar.title(f"🎵 Halo, {st.session_state.user}")
    page = st.sidebar.radio("Menu:", ["HOME", "Cari Lagu & AI", "Playlist Saya", "Statistik Musik", "Logout"])
else:
    st.sidebar.title("🎵 Streamify")
    page = st.sidebar.radio("Akses:", ["Login", "Registrasi"])

# --- LOGIKA HALAMAN ---

# 1. REGISTRASI
if page == "Registrasi":
    st.title("📝 Buat Akun Baru")
    new_user = st.text_input("Username Baru")
    new_pass = st.text_input("Password Baru", type="password")
    confirm_pass = st.text_input("Konfirmasi Password", type="password")
    
    if st.button("Daftar Sekarang"):
        users = load_users()
        if not new_user or not new_pass:
            st.error("Data tidak boleh kosong!")
        elif new_user in users:
            st.error("Username sudah terdaftar!")
        elif new_pass != confirm_pass:
            st.error("Password tidak cocok!")
        else:
            save_user(new_user, new_pass)
            st.success("Akun berhasil dibuat! Silakan pindah ke menu Login.")

# 2. LOGIN
elif page == "Login":
    st.title("🔐 Login Access")
    u_input = st.text_input("Username")
    p_input = st.text_input("Password", type="password")
    
    if st.button("Masuk"):
        users = load_users()
        if u_input in users and users[u_input] == p_input:
            st.session_state.logged_in = True
            st.session_state.user = u_input
            st.success("Login Berhasil!")
            st.rerun()
        else:
            st.error("Username atau Password salah!")

# 3. LOGOUT
elif page == "Logout":
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.my_playlist = []
    st.rerun()

# 4. HOME (Hanya jika sudah login)
elif page == "HOME":
    if not st.session_state.logged_in: st.warning("Silakan login!")
    else:
        st.title(f"🏡 Selamat Datang, {st.session_state.user}!")
        if not df_master.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Lagu", len(df_master))
            c2.metric("Total Artis", df_master['artist_names'].nunique())
            c3.metric("Top Hit", df_master.nlargest(1, 'popularity')['track_name'].values[0])
            st.markdown("---")
            st.subheader("🔥 Rekomendasi Untukmu")
            st.dataframe(df_master[['track_name', 'artist_names', 'popularity']].sample(10), use_container_width=True)

# 5. CARI LAGU & AI
elif page == "Cari Lagu & AI":
    if not st.session_state.logged_in: st.warning("Login dulu!")
    else:
        st.title("🔍 Cari & AI Advisor")
        t1, t2 = st.tabs(["Pencarian", "Tanya Gemini AI ✨"])
        
        with t1:
            q = st.text_input("Cari lagu...")
            if q:
                res = df_master[df_master['track_name'].str.contains(q, case=False, na=False)]
                for _, row in res.head(5).iterrows():
                    st.write(f"🎵 {row['track_name']} - {row['artist_names']}")

        with t2:
            user_msg = st.text_area("Request lagu (Contoh: 'Kasih lagu yang mirip NIKI')", height=100)
            if st.button("Minta Saran AI"):
                try:
                    # CARA PEMANGGILAN YANG BENAR UNTUK GEMINI 1.5 FLASH
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    context = df_master[['track_name', 'artist_names']].sample(15).to_string()
                    full_prompt = f"Data lagu: {context}\n\nUser: {user_msg}"
                    
                    with st.spinner("Berpikir..."):
                        response = model.generate_content(full_prompt)
                        st.write(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.info("Jalankan: pip install -U google-generativeai")

# 6. PLAYLIST SAYA
elif page == "Playlist Saya":
    if not st.session_state.logged_in: st.warning("Silakan login!")
    else:
        st.title(f"🎶 Playlist {st.session_state.user}")
        if not st.session_state.my_playlist: st.info("Playlist kosong.")
        else:
            for i, t in enumerate(st.session_state.my_playlist):
                with st.expander(f"{i+1}. {t['track_name']} - {t['artist_names']}"):
                    if st.button("Hapus", key=f"del_{i}"):
                        st.session_state.my_playlist.pop(i)
                        st.rerun()

# 7. STATISTIK MUSIK
elif page == "Statistik Musik":
    if not st.session_state.logged_in: st.warning("Silakan login!")
    else:
        st.title("📊 Statistik")
        if not df_master.empty:
            top_art = df_master['artist_names'].value_counts().head(10)
            fig = px.bar(top_art, color_continuous_scale='Magma')
            st.plotly_chart(fig, use_container_width=True)