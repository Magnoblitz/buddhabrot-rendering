import cv2

def nonlocal_denoise(input_path, output_path, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21):
    # load image
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {input_path}")

    # convert BGR to RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # apply denoising
    denoised = cv2.fastNlMeansDenoisingColored(
        img_rgb, None,
        h=h,
        hColor=hColor,
        templateWindowSize=templateWindowSize,
        searchWindowSize=searchWindowSize
    )

    # save denoised version
    denoised_bgr = cv2.cvtColor(denoised, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, denoised_bgr)

    return denoised



nonlocal_denoise("test.png", "test_out.png", 10, 5)
