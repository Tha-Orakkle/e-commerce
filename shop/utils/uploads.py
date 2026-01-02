import os

def shop_logo_upload_path(instance, filename):
    """
    Returns the upload path for shop logos.
    """
    dir_name = f"shp_{instance.id}/logo"
    return os.path.join(dir_name, filename)