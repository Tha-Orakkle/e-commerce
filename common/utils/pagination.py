from rest_framework.pagination import PageNumberPagination as PNP

import os


class Pagination(PNP):
    page_size = os.getenv('PAGE_SIZE')