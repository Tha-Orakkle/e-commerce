from django.contrib.auth import get_user_model

import pytest

User = get_user_model()
pytest_plugins = ['product.tests.conftest']


@pytest.fixture
def customer_no_cart(db):
    count = User.objects.filter(is_customer=True, is_superuser=False).count() + 1
    customer = User.objects.create_user(
        email=f"customer{count}@email.com",
        password="Password123#",
    )
    return customer