import taichi as ti
import numpy as np
from PIL import Image
import time

# Parameters
ti.init(arch=ti.vulkan)

width, height = 800, 800
samples = 50000000     # total random c samples
real_min, real_max = -2.0, 1.0
imag_min, imag_max = -1.5, 1.5

# device histograms
low_hist = ti.field(dtype=ti.i32, shape=(height, width))
mid_hist = ti.field(dtype=ti.i32, shape=(height, width))
high_hist = ti.field(dtype=ti.i32, shape=(height, width))


# Kernel helper funcs
@ti.func
def lcg_rand_pair(idx: ti.i32):
    # Return two pseudo-random numbers in [0,1) from an index using LCG

    i64 = ti.u64(idx)
    r = (i64 * ti.u64(1664525) + ti.u64(1013904223)) & ti.u64(0xffffffff)
    r2 = ((i64 + ti.u64(1234567)) * ti.u64(22695477) + ti.u64(1)) & ti.u64(0xffffffff)
    denom = ti.u64(0xffffffff)
    return float(r) / float(denom), float(r2) / float(denom)



# Render kernel
@ti.kernel
def render(hist : ti.template(), samples: ti.i32, max_iter: ti.i32, re_min: ti.f64, re_max: ti.f64, im_min: ti.f64, im_max: ti.f64):
    # Precompute scales
    re_scale = (width - 1) / (re_max - re_min)
    im_scale = (height - 1) / (im_max - im_min)

    for idx in range(samples):
        # generate a random complex c in the region
        r01, r02 = lcg_rand_pair(idx)
        c_re = r01 * (re_max - re_min) + re_min
        c_im = r02 * (im_max - im_min) + im_min

        # First pass: check escape iteration (no storage)
        z_re = 0.0
        z_im = 0.0
        escaped = 0  # number of iterations when it escaped
        for it in range(max_iter):
            # z = z^2 + c (real/imag)

            # uncomment these lines for the burning ship fractal
            #z_re = abs(z_re)
            #z_im = abs(z_im)

            # uncomment this line for the tricorn fractal
            z_im = -z_im

            zr = z_re * z_re - z_im * z_im + c_re
            zi = 2.0 * z_re * z_im + c_im
            z_re, z_im = zr, zi
            if z_re * z_re + z_im * z_im > 4.0:
                escaped = it + 1
                break

        if escaped == 0:
            # the point is part of Mandelbrot set so skip it
            continue

        # Second pass: paint the orbit of the point
        z_re = 0.0
        z_im = 0.0
        for it in range(escaped):


            # uncomment these lines for the burning ship fractal
            #z_re = abs(z_re)
            #z_im = abs(z_im)

            # uncomment this line for the tricorn fractal
            #z_im = -z_im



            zr = z_re * z_re - z_im * z_im + c_re
            zi = 2.0 * z_re * z_im + c_im
            z_re, z_im = zr, zi

            # map complex z to pixel coords
            x = int((z_re - re_min) * re_scale)
            y = int((im_max - z_im) * im_scale)

            if 0 <= x < width and 0 <= y < height:
                # atomic add required for parallel kernels
                ti.atomic_add(hist[y, x], 1)




# Start of rendering code:

# save start time and fill all the histograms with 0
start_time = time.time()
low_hist.fill(0)
mid_hist.fill(0)
high_hist.fill(0)




# max iteration values (these create the output colors/contrast):

# high contrast nebula
low_iter = 500
mid_iter = 5000
high_iter = 20000

# traditional nebulabrot
#low_iter = 50
#mid_iter = 200
#high_iter = 800



# render the histograms
render(low_hist, samples, low_iter, real_min, real_max, imag_min, imag_max)
render(mid_hist, samples, mid_iter, real_min, real_max, imag_min, imag_max)
render(high_hist, samples, high_iter, real_min, real_max, imag_min, imag_max)

# copy the hists to the CPU
low = low_hist.to_numpy().astype(np.float64)
mid = mid_hist.to_numpy().astype(np.float64)
high = high_hist.to_numpy().astype(np.float64)



# apply a tonemap to the histograms to create the final colors
def tonemap(arr, exposure=1.0, deadzone=0.9999, knee=0.99999):
    # 1. log compress first
    arr = np.log1p(arr * exposure)

    # 2. floor the values
    # anything below this percentile is black
    floor_val = np.percentile(arr, deadzone * 100)
    arr = arr - floor_val
    arr[arr < 0] = 0.0

    # 3. define a "knee" where the glow starts
    knee_val = np.percentile(arr, knee * 100)
    if knee_val > 0:
        arr = arr / knee_val  # normalize only relative to knee
    arr = np.clip(arr, 0.0, 1.0)

    return arr

low  = tonemap(low,  exposure=1.0, deadzone=0.65,  knee=0.65)
mid  = tonemap(mid,  exposure=1.0, deadzone=0.75,  knee=0.75)
high = tonemap(high, exposure=1.0, deadzone=0.8,  knee=0.8)

# scale the color values to 0-255
low  = (low  * 255).astype(np.uint8)
mid  = (mid  * 255).astype(np.uint8)
high = (high * 255).astype(np.uint8)




# stack the layers into RGB
rgb = np.dstack([high, mid, low])    # switching high and low also looks cool like a fiery nebula

#img_arr = data.astype(np.uint8)
#img = Image.fromarray(img_arr, mode="L")
img = Image.fromarray(rgb, mode="RGB")

img.save("buddhabrot.png")
print(f"Saved buddhabrot.png in {time.time() - start_time:.2f}s")
