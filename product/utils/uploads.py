from django.conf import settings
import os


def product_upload_image_path(instance, filename):
    """
    Returns the upload path for product images.
    """
    shop_id = instance.product.shop.id
    dir_name = f"shp_{shop_id}/products/pdt_{instance.product.id}"
    _, ext = os.path.splitext(filename)
    
    from uuid import uuid4
    new_filename = f"{str(uuid4())[:8]}{ext.lower()}"
    return os.path.join(dir_name, new_filename)