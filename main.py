import streamlit as st
import json
import pandas as pd
import requests
import os
import matplotlib.pyplot as plt           
from io import BytesIO                   
from reportlab.pdfgen import canvas      
from reportlab.lib.pagesizes import A4   
from reportlab.lib.utils import ImageReader

# =========================================================================================
# 1. KONFIGURASI AI (DIRECT API) & DATABASE
# =========================================================================================
# Pastikan APIKEY ada di st.secrets
try:
    GEMINI_API_KEY = st.secrets["APIKEY"]
except:
    GEMINI_API_KEY = ""

USER_DB_FILE = 'users.json'

def load_users():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USER_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f)

def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta3/models/text-bison-001:generateText?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"prompt": {"text": prompt}}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        res_json = response.json()
        if response.status_code == 200:
            return res_json['candidates'][0]['output']
        else:
            error_msg = res_json.get('error', {}).get('message', 'Terjadi kesalahan pada server AI.')
            return f"⚠️ Error AI ({response.status_code}): {error_msg}"
    except Exception as e:
        return f"❌ Koneksi Gagal: {str(e)}"

# Inisialisasi Session State
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None
if 'my_playlist' not in st.session_state: st.session_state.my_playlist = []

# =========================================================================================
# 2. LOAD DATA MUSIK (OPTIMALISASI DATA.JSON)
# =========================================================================================
@st.cache_data
def load_music_data():
    try:
        if os.path.exists('data.json'):
            df = pd.read_json('data.json')
            if 'album_release_date' in df.columns:
                df['album_release_date'] = pd.to_datetime(df['album_release_date'], errors='coerce')
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal memuat data.json: {e}")
        return pd.DataFrame()

df_master = load_music_data()

# Helper untuk durasi
def ms_to_min(ms):
    sec = int((ms/1000)%60)
    mins = int((ms/(1000*60))%60)
    return f"{mins}:{sec:02d}"

# =========================================================================================
# 3. ANTARMUKA UTAMA
# =========================================================================================
st.set_page_config(page_title="Streamify Pro AI", layout="wide", page_icon="🎵")

if st.session_state.logged_in:
    st.sidebar.title(f"🎵 Halo, {st.session_state.user}")
    page = st.sidebar.radio("Menu:", ["HOME", "Cari Lagu & AI", "Playlist Saya", "Statistik Musik", "Logout"])
else:
    st.sidebar.title("🎵 Streamify")
    page = st.sidebar.radio("Akses:", ["Login", "Registrasi"])

# --- LOGIKA HALAMAN ---

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

elif page == "Logout":
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.my_playlist = []
    st.rerun()

elif page == "HOME":
    if not st.session_state.logged_in: st.warning("Silakan login!")
    else:
        st.title(f"🏡 Selamat Datang, {st.session_state.user}!")
        if not df_master.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Lagu", len(df_master))
            c2.metric("Total Artis", df_master['artist_names'].nunique() if 'artist_names' in df_master.columns else 0)
            
            if 'popularity' in df_master.columns:
                top_song = df_master.nlargest(1, 'popularity')['track_name'].values[0]
                c3.metric("Top Hit", top_song)
            
            st.markdown("---")
            st.subheader("Rekomendasi Terpopuler Hari Ini")
            st.dataframe(df_master[['track_name', 'artist_names', 'album_name', 'popularity']].sort_values(by='popularity', ascending=False).head(10))

elif page == "Cari Lagu & AI":
    if not st.session_state.logged_in: st.warning("Login dulu!")
    else:
        st.title("🔍 Cari & AI Advisor")
        t1, t2 = st.tabs(["Pencarian", "Tanya Gemini AI ✨"])
        
        with t1:
            q = st.text_input("Cari judul lagu, artis, atau album...")
            if q:
                res = df_master[
                    df_master['track_name'].str.contains(q, case=False, na=False) | 
                    df_master['artist_names'].str.contains(q, case=False, na=False)
                ]
                if not res.empty:
                    for index, row in res.head(10).iterrows():
                        with st.container(border=True):
                            col_img, col_info, col_btn = st.columns([1, 4, 1])
                            with col_img:
                                if 'album_image_url' in row:
                                    st.image(row['album_image_url'], width=100)
                            with col_info:
                                st.markdown(f"**{row['track_name']}** - {row['artist_names']}")
                                st.caption(f"Album: {row['album_name']} | Populer: {row['popularity']}")
                                if 'track_preview_url' in row and row['track_preview_url']:
                                    st.audio(row['track_preview_url'], format="audio/mp3")
                            with col_btn:
                                if st.button("➕ Tambah", key=f"add_{index}"):
                                    st.session_state.my_playlist.append(row.to_dict())
                                    st.toast(f"Ditambahkan: {row['track_name']}")
                else:
                    st.info("Lagu tidak ditemukan.")

        with t2:
            user_msg = st.text_area("Tanya AI (Contoh: 'Rekomendasi lagu BLACKPINK')", height=100)
            if st.button("Minta Saran AI"):
                if user_msg:
                    sample_data = df_master[['track_name', 'artist_names']].sample(min(15, len(df_master))).to_string()
                    full_prompt = f"Data lagu kami:\n{sample_data}\n\nUser: {user_msg}\nBerikan rekomendasi lagu berdasarkan data tersebut."
                    with st.spinner("AI sedang berpikir..."):
                        jawaban = ask_gemini(full_prompt)
                        st.markdown(jawaban)
                else:
                    st.warning("Silakan isi permintaan Anda.")

elif page == "Playlist Saya":
    if not st.session_state.logged_in: st.warning("Silakan login!")
    else:
        st.title(f"🎶 Playlist {st.session_state.user}")
        if not st.session_state.my_playlist:
            st.info("Playlist kamu kosong.")
        else:
            for i, t in enumerate(st.session_state.my_playlist):
                with st.expander(f"{i+1}. {t['track_name']} - {t['artist_names']}"):
                    st.write(f"Album: {t['album_name']}")
                    if 'track_duration_ms' in t:
                        st.write(f"Durasi: {ms_to_min(t['track_duration_ms'])}")
                    if st.button("🗑️ Hapus Lagu", key=f"del_{i}"):
                        st.session_state.my_playlist.pop(i)
                        st.rerun()

elif page == "Statistik Musik":
    if not st.session_state.logged_in: st.warning("Silakan login!")
    else:
        st.title("📊 Statistik Artis Terpopuler")
        if not df_master.empty and 'artist_names' in df_master.columns:
            top_art = df_master['artist_names'].value_counts().head(10)
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(top_art.index, top_art.values, color='skyblue')
            ax.set_title("Top 10 Artis Berdasarkan Jumlah Lagu")
            plt.xticks(rotation=45, ha="right")
            st.pyplot(fig)

            st.subheader("Detail Jumlah Lagu")
            st.table(top_art)

            # PDF Generator
            img_buffer = BytesIO()
            fig.savefig(img_buffer, format="png", bbox_inches="tight")
            img_buffer.seek(0)
            
            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, 820, f"Statistik Musik Streamify - User: {st.session_state.user}")
            c.drawImage(ImageReader(img_buffer), 50, 450, width=500, height=300, preserveAspectRatio=True)
            c.showPage()
            c.save()
            pdf_buffer.seek(0)

            st.download_button(
                label="⬇️ Unduh Laporan (PDF)",
                data=pdf_buffer,
                file_name=f"Statistik_{st.session_state.user}.pdf",
                mime="application/pdf"
            )