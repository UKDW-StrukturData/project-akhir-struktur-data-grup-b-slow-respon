import streamlit as st
import json
import pandas as pd
import requests
import os
import matplotlib.pyplot as plt   
import google.generativeai as genai       
from io import BytesIO                   
from reportlab.pdfgen import canvas      
from reportlab.lib.pagesizes import A4   
from reportlab.lib.utils import ImageReader

# =========================================================================================
# 1. KONFIGURASI AI (DIRECT API) & DATABASE
# =========================================================================================
API_KEY = st.secrets.get("APIKEY", "")
USER_DB_FILE = "users.json"

def load_users():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USER_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f)

model = None
ai_connected = False

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        ai_connected = True
    except Exception as e:
        st.error(f"⚠️ API Key ada, tapi koneksi ke Gemini gagal: {e}")
else:
    st.warning("⚠️ API Key Gemini belum ditemukan di secrets.toml")

def ask_gemini(prompt):
    if not ai_connected or model is None:
        return "❌ Gemini AI belum terhubung."

    try:
        response = model.generate_content(prompt)
        return response.text if response.text else "AI tidak merespons."
    except Exception as e:
        return f"❌ Gagal generate konten: {e}"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "my_playlist" not in st.session_state:
    st.session_state.my_playlist = []


# =========================================================================================
# 2. LOAD DATA MUSIK
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

# =========================================================================================
# 3. ANTARMUKA UTAMA
# =========================================================================================
st.set_page_config(page_title="Streamify Pro AI", layout="wide", page_icon="🎵")

# Sidebar Navigasi
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

elif page == "Cari Lagu & AI":
    if not st.session_state.logged_in: st.warning("Login dulu!")
    else:
        st.title("🔍 Cari & AI Advisor")
        t1, t2 = st.tabs(["Pencarian", "Tanya Gemini AI ✨"])
        
        with t1:
            q = st.text_input("Cari judul lagu atau artis...")
            if q:
                res = df_master[
                    df_master['track_name'].str.contains(q, case=False, na=False) | 
                    df_master['artist_names'].str.contains(q, case=False, na=False)
                ]
                if not res.empty:
                    for index, row in res.head(10).iterrows():
                        col_a, col_b = st.columns([4, 1])
                        col_a.write(f"🎵 **{row['track_name']}** - {row['artist_names']}")
                        # Key unik menggunakan index agar tidak error
                        if col_b.button("Tambah", key=f"add_{index}"):
                            st.session_state.my_playlist.append(row.to_dict())
                            st.toast(f"Ditambahkan: {row['track_name']}")
                else:
                    st.info("Lagu tidak ditemukan.")

        with t2:
            user_msg = st.text_area("Tanya AI (Contoh: 'Rekomendasi lagu yang mirip Taylor Swift')", height=100)
            if st.button("Minta Saran AI"):
                if user_msg:
                    sample_data = df_master[['track_name', 'artist_names']].sample(min(20, len(df_master))).to_string()
                    full_prompt = f"Data lagu kami:\n{sample_data}\n\nUser: {user_msg}\nBerikan rekomendasi lagu."
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
            # Menggunakan list comprehension untuk menghindari index error saat pop
            for i, t in enumerate(st.session_state.my_playlist):
                col1, col2 = st.columns([5, 1])
                col1.write(f"{i+1}. **{t['track_name']}** - {t['artist_names']}")
                if col2.button("Hapus", key=f"del_{i}"):
                    st.session_state.my_playlist.pop(i)
                    st.rerun()

elif page == "Statistik Musik":
    if not st.session_state.logged_in:
        st.warning("Silakan login!")
    else:
        st.title("📊 Statistik Artis Terpopuler")

        if not df_master.empty and 'artist_names' in df_master.columns:
            top_art = df_master['artist_names'].value_counts().head(10)

            # ===== BUAT GRAFIK (MATPLOTLIB) =====
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.bar(top_art.index, top_art.values)
            ax.set_title("Top 10 Artis Terpopuler")
            ax.set_xlabel("Nama Artis")
            ax.set_ylabel("Jumlah Lagu")
            plt.xticks(rotation=45, ha="right")

            st.pyplot(fig)

            # ===== TABEL =====
            st.subheader("Detail Jumlah Lagu")
            st.table(top_art)

            # ===== SIMPAN GRAFIK KE MEMORY =====
            img_buffer = BytesIO()
            fig.savefig(img_buffer, format="png", bbox_inches="tight")
            img_buffer.seek(0)

            # ===== BUAT PDF =====
            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=A4)

            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, 820, "Statistik Artis Terpopuler")

            c.setFont("Helvetica", 10)
            c.drawString(50, 800, "Top 10 Artis berdasarkan jumlah lagu")

            c.drawImage(
                ImageReader(img_buffer),
                50, 400,
                width=500,
                height=300,
                preserveAspectRatio=True
            )

            c.showPage()
            c.save()
            pdf_buffer.seek(0)

            # ===== TOMBOL DOWNLOAD PDF =====
            st.download_button(
                label="⬇️ Unduh Grafik (PDF)",
                data=pdf_buffer,
                file_name="Statistik_Artis_Terpopuler.pdf",
                mime="application/pdf",
                type="primary"
            )