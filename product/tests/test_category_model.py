from product.models import Category

def test_category_creation(category):
    """
    Test the creation of a category.
    """
    assert category.name == "Test Category"
    assert category.slug == "test-category"
    assert Category.objects.count() == 1


def test_category_str(category):
    """
    Test the string representation of a category.
    """
    assert str(category) == f"<Category: {category.id}> {category.slug}"


def test_category_ordering(db_access):
    """
    Test the ordering of categories by created_at.
    """

    # Create three categories with different names
    category1 = Category.objects.create(name="Electronics")
    category2 = Category.objects.create(name="Books")
    category3 = Category.objects.create(name="Clothing")

    categories = Category.objects.all()
    assert list(categories) == [category2, category3, category1] 


def test_category_save_slug(category):
    """
    Test that the slug is automatically generated from the name.
    """
    category.name = "New Category Name"
    category.save()
    
    assert category.slug == "new-category-name", "Slug was not updated correctly after saving"
