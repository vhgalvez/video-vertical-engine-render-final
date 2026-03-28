import os

def load_images(images_path):
    images = sorted([
        os.path.join(images_path, f)
        for f in os.listdir(images_path)
        if f.endswith(".png")
    ])
    return images
