import streamlit as st
import cv2
import numpy as np
from core_logic import BioSplitLogic
import os

st.set_page_config(page_title="BioSplit Tool", layout="centered")

# Initialize Session State to keep track of the workflow
if 'step' not in st.session_state: st.session_state.step = 1
if 'shares' not in st.session_state: st.session_state.shares = None
if 'recovered_img' not in st.session_state: st.session_state.recovered_img = None

st.title("BioSplit Biometric Vault")
tab1, tab2, tab3 = st.tabs(["Encryption (Split)", "Decryption (Merge)", "Single Extract (Noise Check)"])

# --- TAB 1: ENCRYPTION ---
with tab1:
    st.subheader("1. Upload Secret")
    file = st.file_uploader("Upload Fingerprint/Face (PNG/JPG)", type=['png', 'jpg'], key="enc_up")
    
    # Check if a new file is uploaded to reset everything
    if file:
        file_id = f"{file.name}_{file.size}"
        if "last_enc_file" not in st.session_state or st.session_state.last_enc_file != file_id:
            st.session_state.step = 1
            st.session_state.shares = None
            st.session_state.last_enc_file = file_id
            st.rerun()

    if file:
        # Load and convert to Grayscale
        raw = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        st.image(gray, caption="Standardized Grayscale Secret")
        
        if st.button("Confirm Secret & Choose Cover"):
            st.session_state.step = 2
            st.session_state.shares = None  # Reset old shares when new secret is confirmed
            st.rerun()

    if st.session_state.step >= 2:
        st.divider()
        st.subheader("2. Select Key Covers from Library")
        lib_files = [f for f in os.listdir("library") if f.endswith((".png", ".jpg", ".avif"))]
        
        # Check if selection changed to reset generated shares
        current_selection = f"{st.session_state.get('c1_sel')}_{st.session_state.get('c2_sel')}"
        if "last_selection" in st.session_state and st.session_state.last_selection != current_selection:
            st.session_state.shares = None
        st.session_state.last_selection = current_selection

        # UI for covering selection with previews
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("**Cover 1 (The Key)**")
            cover1_name = st.selectbox("Select Image 1", lib_files, index=0, key="c1_sel")
            c1_preview = cv2.imread(os.path.join("library", cover1_name))
            if c1_preview is not None:
                st.image(cv2.cvtColor(c1_preview, cv2.COLOR_BGR2RGB), use_container_width=True)
        
        with col_c2:
            st.markdown("**Cover 2 (The Vessel)**")
            cover2_name = st.selectbox("Select Image 2", lib_files, index=min(1, len(lib_files)-1), key="c2_sel")
            c2_preview = cv2.imread(os.path.join("library", cover2_name))
            if c2_preview is not None:
                st.image(cv2.cvtColor(c2_preview, cv2.COLOR_BGR2RGB), use_container_width=True)
        
        if st.button("Generate Shares", use_container_width=True):
            c1_path = os.path.join("library", cover1_name)
            c2_path = os.path.join("library", cover2_name)
            
            img_c1 = cv2.imread(c1_path)
            img_c2 = cv2.imread(c2_path)
            
            s1, s2 = BioSplitLogic.encrypt(gray, img_c1, img_c2)
            
            # Save to session state
            _, buffer1 = cv2.imencode(".png", s1)
            _, buffer2 = cv2.imencode(".png", s2)
            st.session_state.shares = (buffer1.tobytes(), buffer2.tobytes(), s1, s2)
            st.success("Encryption Complete!")

        if st.session_state.shares:
            b1, b2, s1_img, s2_img = st.session_state.shares
            col1, col2 = st.columns(2)
            
            # Convert BGR (OpenCV) to RGB for correct Streamlit display
            s1_rgb = cv2.cvtColor(s1_img, cv2.COLOR_BGR2RGB)
            s2_rgb = cv2.cvtColor(s2_img, cv2.COLOR_BGR2RGB)
            
            col1.image(s1_rgb, caption="Share 1 (Key)")
            col2.image(s2_rgb, caption="Share 2 (Cipher)")
            
            col1.download_button("Download Share 1", b1, "share1.png", mime="image/png")
            col2.download_button("Download Share 2", b2, "share2.png", mime="image/png")

# --- TAB 2: DECRYPTION ---
with tab2:
    st.subheader("Reassemble Secret")
    up1 = st.file_uploader("Upload Share 1", type='png', key="dec_1")
    up2 = st.file_uploader("Upload Share 2", type='png', key="dec_2")
    
    # Reset recovered image if new files are uploaded
    if (up1 and "last_up1" not in st.session_state) or (up1 and st.session_state.get("last_up1") != up1.name):
        st.session_state.recovered_img = None
        st.session_state.last_up1 = up1.name
    if (up2 and "last_up2" not in st.session_state) or (up2 and st.session_state.get("last_up2") != up2.name):
        st.session_state.recovered_img = None
        st.session_state.last_up2 = up2.name

    if up1 and up2:
        if st.button("Decrypt & Recover"):
            # Decode shares
            img1 = cv2.imdecode(np.frombuffer(up1.read(), np.uint8), cv2.IMREAD_COLOR)
            img2 = cv2.imdecode(np.frombuffer(up2.read(), np.uint8), cv2.IMREAD_COLOR)
            
            if img1.shape != img2.shape:
                st.error("Error: Shares must have the same resolution!")
            else:
                recovered, integrity = BioSplitLogic.decrypt(img1, img2)
                _, rec_buffer = cv2.imencode(".png", recovered)
                st.session_state.recovered_img = (rec_buffer.tobytes(), recovered, integrity)
                st.balloons()

        if st.session_state.recovered_img:
            rec_bytes, rec_raw, integrity = st.session_state.recovered_img
            st.image(rec_raw, caption="RECOVERED SECRET")
            
            # Display Integrity Metrics
            st.metric("Integrity Score (Bit Check)", f"{integrity:.2f}%")
            if integrity > 99.9:
                st.success("✅ Perfect Data Integrity. The shares match the original secret.")
            elif integrity > 90.0:
                st.warning("⚠️ High Integrity, but some noise detected.")
            else:
                st.error("❌ Low Integrity! The shares may have been tampered with or are from different sessions.")
                
            st.download_button("Download Recovered Secret", rec_bytes, "recovered_secret.png", mime="image/png")

# --- TAB 3: SINGLE EXTRACT ---
with tab3:
    st.subheader("Extract LSB from a Single Image")
    st.info("Upload any share to see that without the key, the extracted data is just noise.")
    single_up = st.file_uploader("Upload One Share (PNG)", type='png', key="single_up")
    
    if single_up:
        s_img = cv2.imdecode(np.frombuffer(single_up.read(), np.uint8), cv2.IMREAD_COLOR)
        
        if st.button("Extract Raw LSBs"):
            raw_extracted = BioSplitLogic.extract_raw_lsb(s_img)
            
            st.image(raw_extracted, caption="Extracted Data (Noise)", width=400)
            st.warning("As you can see, this image alone contains no recognizable biometric data.")