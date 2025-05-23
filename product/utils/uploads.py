from django.conf import settings
import os


def product_upload_image_path(instance, filename):
    """
    Returns the upload path for product images.
    """
    dir_name = 'products/pdt_' + str(instance.product.id)
    return os.path.join(dir_name, filename)