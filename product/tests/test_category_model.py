from product.models import Category

def test_category_creation(category_factory):
    """
    Test the creation of a category.
    """
    category = category_factory(name="Fashion and Apparel")
    assert category.name == "Fashion and Apparel"
    assert category.slug == "fashion-and-apparel"
    assert Category.objects.count() == 1


def test_category_str(category):
    """
    Test the string representation of a category.
    """
    assert str(category) == f"<Category: {category.id}> {category.slug}"


def test_category_ordering(category_factory):
    """
    Test the ordering of categories by created_at.
    """
    c1 = category_factory(name="Fashion")
    c2 = category_factory(name="Electronics")
    c3 = category_factory(name="Books")

    categories = Category.objects.all()
    assert list(categories) == [c3, c2, c1] 


def test_category_save_slug(category):
    """
    Test that the slug is automatically generated from the name.
    """
    category.name = "Fashion & Apparel"
    category.save()

    assert category.slug == "fashion-apparel", "Slug was not updated correctly after saving"