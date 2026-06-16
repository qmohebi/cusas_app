import pytest
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.contenttypes.models import ContentType

from library_app.models import LoanCategory


@pytest.mark.django_db
def test_loan_category_defaults():
    image = SimpleUploadedFile("test.jpg", b"filecontent", content_type="image/jpeg")
    category = LoanCategory.objects.create(
        category_id="01",
        category_name="vital signs",
        display_name="blood pressure",
        image=image,
    )
    assert category.is_permanent_loan is False
    assert category.is_active is False


@pytest.mark.django_db
def test_manage_loan_category_permission_exists():
    content_type=ContentType.objects.get_for_model(LoanCategory)

    assert Permission.objects.filter(
        content_type=content_type, codename='manage_loan_categories',
    ).exists()