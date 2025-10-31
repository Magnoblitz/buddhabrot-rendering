import numpy as np
from PIL import Image

width, height = 512, 512
zoom = 0.8
cam_pos = (-.5, 0)

data = np.zeros((height, width, 3), dtype=np.uint8)

for y in range(height):
    for x in range(width):
        cx = (x * 2 - width) / height / zoom + cam_pos[0]
        cy = (y * 2 - height) / height / zoom + cam_pos[1]
        
        zx, zy = 0, 0

        i = 0
        for i in range(40):
            if zx*zx + zy*zy > 4:
                break
            original_zx = zx

            # burning ship
            #zx = abs(zx)
            #zy = abs(zy)

            # normal mandelbrot
            zx = zx*zx - zy*zy + cx
            zy = 2*original_zx*zy + cy

            # third power mandelbrot 
            #zx = zx*zx*zx - 3*zx*zy*zy + cx
            #zy = 3*original_zx*original_zx*zy - zy*zy*zy + cy

        r = (i / 40)*255
        g,b = r,r

        data[y, x] = (r, g, b)

Image.fromarray(data).save("output.png")