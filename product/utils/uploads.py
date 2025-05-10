from django.conf import settings
import os


def product_upload_image_path(instance, filename):
    """
    Returns the upload path for product images.
    """
    dir_name = 'products/product_' + str(instance.product.id)
    try:
        os.mkdir(settings.MEDIA_ROOT / dir_name)
    except FileExistsError:
        pass
    return os.path.join(dir_name, filename)