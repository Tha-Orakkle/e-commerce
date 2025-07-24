import os

def shop_logo_upload_path(instance, filename):
    """
    Returns the upload path for shop logos.
    """
    dir_name = f"shops/shp_{instance.id}"
    return os.path.join(dir_name, filename)