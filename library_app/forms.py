from django import forms
from django.core.exceptions import ValidationError
from django.forms import Form, ModelForm, modelformset_factory

from .models import Category, LoanCategory, Location


class LoanRequestForm(Form):
    category = forms.ModelMultipleChoiceField(
        queryset=LoanCategory.objects.all().filter(is_active=True).order_by(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        error_messages={"required": "Please select a category from below!"},
        # to_field_name="equip_model_id",
    )

    exclude_location = [
        "45B7DCD1518B4F289BF692BD28EE8F45",
        "45EE813FF5D442AFB799B48F49C50C75",
        "614353F632C442B1A1F4F353965CA129",
        "619FB2C31CB64F298C4AA4C17C4EF8B9",
        "8D008371-0C50-4F4C-9918-C4C185725DA2",
        "STG2005081100002",
        "951CB87BFBF347039BCD60D4C31785BA",
    ]
    location = forms.ModelChoiceField(
        label="Select your location from dropdown:",
        empty_label="Select a location",
        required=True,
        queryset=Location.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    requester_name = forms.CharField(
        label="Enter your name:",
        max_length=200,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "e.g. John"},
        ),
    )
    extension = forms.IntegerField(
        label="Enter your Extension:",
        required=True,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your extension number",
                "row": 4,
            }
        ),
    )
    # notes = forms.Textarea()
    notes = forms.CharField(
        label="Additional Notes:",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Enter additional information like patient MRN",
                "row": 4,
                "rows": 5,
            }
        ),
        # required=False caused submit spinner and modal to not function properly. So made note required
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Exclude specific locations and load from 'equip'
        self.fields["location"].queryset = (
            Location.objects.using("equip")
            .exclude(locationtypeid__in=self.exclude_location)
            .filter(
                siteid__siteid="STG200404040007",
                inactive=0,
                locationtypeid_id__isnull=False,
            )
            .order_by("locationshortname")
        )

    def clean_requester_name(self):
        return self.cleaned_data["requester_name"].strip()

    def clean_notes(self):
        notes = self.cleaned_data.get("notes", "")
        return notes.strip()

    def clean_extension(self):
        extension = self.cleaned_data["extension"]
        if extension <= 0:
            raise ValidationError("Extension must be postive number")
        return extension


class LogisticsRequestForm(Form):
    equipment_number = forms.CharField(
        label="equipment number",
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "e.g. 5512345"}),
    )
    request_details = forms.CharField(
        label="Enter your name",
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "e.g. John"}),
    )
    planned_date = forms.DateField(
        label="planned-date",
        required=True,
        widget=forms.TextInput(attrs={"type": "date"}),
    )


class CategoryManagementForm(ModelForm):
    """Manage the category that gets syncornised from eQuip
    this allows for user to set the display name,
    set it to active and or set it to permenant loan on the form"""

    image = forms.ImageField(required=False, widget=forms.ClearableFileInput)
    category_id = forms.CharField(label="Category ID:")
    category_name = forms.CharField(label="Category Name")
    display_name = forms.CharField(
        label="Display Name",
        widget=forms.TextInput(attrs={"placeholder": "Enter name to be seen by user"}),
    )
    is_active = forms.BooleanField(label="Is Active")
    is_permanent_loan = forms.BooleanField(required=False, label="Permanent Loan")

    class Meta:
        model = LoanCategory
        fields = [
            "category_id",
            "display_name",
            "category_name",
            "is_permanent_loan",
            "is_active",
            "image",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for _, field in self.fields.items():
            w = field.widget

            if isinstance(
                w,
                (
                    forms.TextInput,
                    forms.NumberInput,
                    forms.EmailInput,
                    forms.URLInput,
                    forms.Textarea,
                ),
            ):
                w.attrs.setdefault("class", "form-control")

            elif isinstance(w, (forms.Select, forms.SelectMultiple)):
                w.attrs.setdefault("class", "form-select")

            elif isinstance(w, forms.ClearableFileInput):
                w.attrs.setdefault("class", "form-control")
            elif isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault("class", "form-check-input")
                w.attrs.setdefault("role", "switch")

            self.fields["category_id"].disabled = True
            self.fields["category_name"].disabled = True

            # hide crispyform labels

    def clean(self):
        cleaned = super().clean()
        image = cleaned.get("image")

        if image is False:
            raise forms.ValidationError("Image cannot be removed.")

        has_existing_image = bool(getattr(self.instance, "image", None))

        if not image and not has_existing_image:
            self.add_error("image", "Pleae upload an image")

        return cleaned


CategoryManagementFormSet = modelformset_factory(
    LoanCategory, form=CategoryManagementForm, extra=0, can_delete=False
)


class CategoryLookupForm(ModelForm):
    class Meta:
        model = Category
        fields = ["categoryid", "categoryshortname"]


class CategoryCreateForm(ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.using("equip").order_by("categoryshortname"),
        empty_label="Select a category",
        required=True,
        label="eQuip Category",
        to_field_name="categoryid",
    )

    class Meta:
        model = LoanCategory
        fields = [
            "category",
            "display_name",
            "is_permanent_loan",
            "is_active",
            "image",
        ]

    def save(self, commit=True):
        # TODO on saving check if the category already exisist
        # and if so give an error and prevent saving
        object = super().save(commit=False)

        cat = self.cleaned_data["category"]
        object.category_id = cat.categoryid
        object.category_name = cat.categoryshortname

        if commit:
            object.save()
        return object
