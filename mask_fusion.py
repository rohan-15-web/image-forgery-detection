import cv2
import numpy as np

def fuse_all_masks(gradcam, orb_mask=None, seg_mask=None, retouch_mask=None):
    """
    Combine all masks into one final tamper mask
    """

    # Convert GradCAM → binary
    gradcam_mask = (gradcam > 0.4).astype("uint8") * 255

    masks = [gradcam_mask]

    if orb_mask is not None:
        masks.append(orb_mask)

    if seg_mask is not None:
        masks.append(seg_mask)

    if retouch_mask is not None:
        masks.append(retouch_mask)

    final_mask = masks[0]

    # Merge all masks
    for m in masks[1:]:
        m = cv2.resize(m, (final_mask.shape[1], final_mask.shape[0]))
        final_mask = cv2.bitwise_or(final_mask, m)

    # Clean mask (remove noise)
    kernel = np.ones((5, 5), np.uint8)
    final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel)
    final_mask = cv2.medianBlur(final_mask, 5)

    return final_mask


def overlay_mask(image_path, mask, save_path):
    """
    Overlay red mask on original image
    """
    img = cv2.imread(image_path)

    mask = cv2.resize(mask, (img.shape[1], img.shape[0]))

    colored = np.zeros_like(img)
    colored[:, :, 2] = mask  # red channel

    overlay = cv2.addWeighted(img, 0.7, colored, 0.3, 0)

    cv2.imwrite(save_path, overlay)