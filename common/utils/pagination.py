from rest_framework.pagination import PageNumberPagination as PNP
from django.conf import settings


class Pagination(PNP):

    @property
    def page_size(self):
        return settings.REST_FRAMEWORK["PAGE_SIZE"]
