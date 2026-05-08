import cv2
import numpy as np

class BioSplitLogic:
    @staticmethod
    def align_and_crop(base_img, target_h, target_w):
        """Proportional scaling followed by center crop."""
        h_base, w_base = base_img.shape[:2]
        
        # Calculate scaling factor 'a'
        a = max(target_h / h_base, target_w / w_base)
        new_h, new_w = int(h_base * a), int(w_base * a)
        
        # Resize using high-quality interpolation
        resized = cv2.resize(base_img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        
        # Center crop
        start_y = (new_h - target_h) // 2
        start_x = (new_w - target_w) // 2
        return resized[start_y:start_y + target_h, start_x:start_x + target_w]

    @staticmethod
    def encrypt(secret_gray, cover1, cover2):
        """The XOR logic hiding 8-bit secret in 3-bit LSBs across two different cover images."""
        h, w = secret_gray.shape
        
        # Prepare both covers (scale and crop to secret size)
        c1 = BioSplitLogic.align_and_crop(cover1, h, w)
        c2_base = BioSplitLogic.align_and_crop(cover2, h, w)
        
        # Share 1 is just the aligned Cover 1
        share1 = c1.copy()
        
        # Share 2 is Cover 2 with LSBs modified
        share2 = c2_base.copy()

        # Split secret into 3-bit, 3-bit, and 2-bit chunks
        s_red = (secret_gray >> 5) & 7   # Top 3 bits
        s_grn = (secret_gray >> 2) & 7   # Middle 3 bits
        s_blu = (secret_gray & 3)        # Bottom 2 bits

        # Apply XOR and embed into Share 2
        # LSB(Share 2) = LSB(Cover 1) XOR Secret_Chunk
        share2[:, :, 2] = (share2[:, :, 2] & 248) | ((c1[:, :, 2] & 7) ^ s_red) # Red
        share2[:, :, 1] = (share2[:, :, 1] & 248) | ((c1[:, :, 1] & 7) ^ s_grn) # Green
        share2[:, :, 0] = (share2[:, :, 0] & 252) | ((c1[:, :, 0] & 3) ^ s_blu) # Blue

        return share1, share2

    @staticmethod
    def decrypt(share1, share2):
        """Extract LSBs and XOR them back to recover 8-bit grayscale."""
        # Extract and XOR each channel
        r_rec = (share1[:, :, 2] & 7) ^ (share2[:, :, 2] & 7)
        g_rec = (share1[:, :, 1] & 7) ^ (share2[:, :, 1] & 7)
        b_rec = (share1[:, :, 0] & 3) ^ (share2[:, :, 0] & 3)

        # Reassemble the 8-bit image: (R << 5) | (G << 2) | B
        recovered = (r_rec << 5) | (g_rec << 2) | b_rec
        return recovered.astype(np.uint8)

    @staticmethod
    def extract_raw_lsb(img):
        """Extract LSBs from a single image and reassemble into 8-bit grayscale noise."""
        r_lsb = img[:, :, 2] & 7
        g_lsb = img[:, :, 1] & 7
        b_lsb = img[:, :, 0] & 3
        
        raw_extracted = (r_lsb << 5) | (g_lsb << 2) | b_lsb
        return raw_extracted.astype(np.uint8)