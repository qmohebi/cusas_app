import factory

from library_app.models import LoanCategory, Location

class LoanCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model=LoanCategory

    category_id = factory.Sequence(lambda n: f"loan-cat-{n}")
    category_name = factory.Sequence(lambda n: f"Loan Category {n}")
    display_name = factory.LazyAttribute(lambda obj: obj.category_name)
    is_permanent_loan = False
    is_active = True
    image = factory.django.ImageField(filename="test.jpg")
    parent = None

