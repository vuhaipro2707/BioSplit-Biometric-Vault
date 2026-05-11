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
        
        # Share 1 is Cover 1 with random bits injected into all 8 LSB positions used
        share1 = c1.copy()
        
        # Share 2 is Cover 2 with LSBs modified
        share2 = c2_base.copy()

        # Split secret into 3-bit, 3-bit, and 2-bit chunks
        s_red = (secret_gray >> 5) & 7   # Top 3 bits
        s_grn = (secret_gray >> 2) & 7   # Middle 3 bits
        s_blu = (secret_gray & 3)        # Bottom 2 bits
        
        # Generate 8 random bits per pixel for Share 1 (3 in Red, 3 in Green, 2 in Blue)
        r_red = np.random.randint(0, 8, size=(h, w), dtype=np.uint8)
        r_grn = np.random.randint(0, 8, size=(h, w), dtype=np.uint8)
        r_blu = np.random.randint(0, 4, size=(h, w), dtype=np.uint8)
        
        # Inject random bits into Share 1
        share1[:, :, 2] = (share1[:, :, 2] & 248) | r_red
        share1[:, :, 1] = (share1[:, :, 1] & 248) | r_grn
        share1[:, :, 0] = (share1[:, :, 0] & 252) | r_blu

        # Bit checking: XOR all bits of the secret pixel
        bit_check = ( (secret_gray >> 7) ^ (secret_gray >> 6) ^ (secret_gray >> 5) ^ 
                      (secret_gray >> 4) ^ (secret_gray >> 3) ^ (secret_gray >> 2) ^ 
                      (secret_gray >> 1) ^ (secret_gray) ) & 1
        
        # Share 2 bit check bit
        r_check = np.random.randint(0, 2, size=(h, w), dtype=np.uint8)
        share1[:, :, 0] = (share1[:, :, 0] & 251) | (r_check << 2)

        # Apply XOR and embed into Share 2
        share2[:, :, 2] = (share2[:, :, 2] & 248) | (r_red ^ s_red) 
        share2[:, :, 1] = (share2[:, :, 1] & 248) | (r_grn ^ s_grn)
        share2[:, :, 0] = (share2[:, :, 0] & 248) | (r_blu ^ s_blu) | ((r_check ^ bit_check) << 2)

        return share1, share2

    @staticmethod
    def decrypt(share1, share2):
        """Extract LSBs and XOR them back to recover 8-bit grayscale."""
        # Extract and XOR each channel using Share 1 as the key (One-Time Pad)
        r_rec = (share1[:, :, 2] & 7) ^ (share2[:, :, 2] & 7)
        g_rec = (share1[:, :, 1] & 7) ^ (share2[:, :, 1] & 7)
        b_rec = (share1[:, :, 0] & 3) ^ (share2[:, :, 0] & 3)
        
        # Recover 8-bit
        recovered = (r_rec << 5) | (g_rec << 2) | b_rec
        
        # Verify bit checking
        extracted_parity = ((share1[:, :, 0] >> 2) & 1) ^ ((share2[:, :, 0] >> 2) & 1)
        
        actual_parity = ( (recovered >> 7) ^ (recovered >> 6) ^ (recovered >> 5) ^ 
                          (recovered >> 4) ^ (recovered >> 3) ^ (recovered >> 2) ^ 
                          (recovered >> 1) ^ (recovered) ) & 1
        
        # Calculate consistency: percent of pixels where parity matches
        match_map = (extracted_parity == actual_parity)
        integrity_score = np.mean(match_map) * 100
        
        return recovered.astype(np.uint8), integrity_score

    @staticmethod
    def extract_raw_lsb(img):
        """Extract LSBs from a single image and reassemble into 8-bit grayscale noise."""
        r_lsb = img[:, :, 2] & 7
        g_lsb = img[:, :, 1] & 7
        b_lsb = img[:, :, 0] & 3
        
        raw_extracted = (r_lsb << 5) | (g_lsb << 2) | b_lsb
        return raw_extracted.astype(np.uint8)