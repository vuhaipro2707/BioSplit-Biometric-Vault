# BioSplit Biometric Vault

BioSplit is a secure biometric storage tool that utilizes **Visual Cryptography** and **LSB Steganography** to protect sensitive biometric data (like fingerprints or face scans). It splits a secret into two distinct "shares" that look like ordinary images, ensuring that the original secret can only be recovered when both shares are combined.

## How It Works

The system uses a custom **XOR-based LSB manipulation** algorithm:

1.  **Alignment**: The secret (grayscale) and covers (RGB) are aligned and cropped to the same dimensions.
2.  **Encryption (Splitting)**:
    *   The 8-bit secret is distributed across the 3-bit Least Significant Bits (LSBs) of the RGB channels of the covers.
    *   **Share 1** is a standard cover image (The Key).
    *   **Share 2** is a second cover image where its LSBs are modified by `LSB(Cover 1) XOR Secret`.
    *   Alone, Share 2 looks like a normal image with slight noise in the shadows, and Share 1 is just a dummy image.
3.  **Decryption (Merging)**:
    *   The system extracts LSBs from both shares.
    *   It performs an `XOR` operation between them to cancel out the cover data and perfectly reconstruct the 8-bit biometric secret.

## Features

- **Encryption**: Split a biometric secret into two different cover images.
- **Decryption**: Recover the secret by uploading both shares.
- **Single Extract (Noise Check)**: A demonstration tool showing that extracting data from just one share yields only random noise.
- **Interactive UI**: Built with Streamlit for a smooth, browser-based experience.

## Local Installation & Setup

### Prerequisites
- Python 3.9+
- Pip

### Commands
1. **Clone the repository** (or navigate to the folder).
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## Deployment with Docker

To deploy easily (e.g., on AWS EC2):

1. **Build and start the container**:
   ```bash
   docker-compose up -d --build
   ```
2. **Access the app**:
   Navigate to `http://your-server-ip:8501` in your browser.

---
*Developed for Information Security demonstration purposes.*
