from django.db import models


class LoanCategory(models.Model):
    category_id = models.CharField(blank=False, null=False, max_length=200)
    category_name = models.CharField(blank=False, null=False, max_length=250)
    display_name = models.CharField(max_length=200)
    is_permanent_loan = models.BooleanField(
        blank=False, null=False, default=False, verbose_name="Permenant loan to wards."
    )
    is_active = models.BooleanField(blank=False, null=False, default=False)
    image = models.ImageField(blank=False, null=False, upload_to="images")
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_models",
    )
    customer = models.ForeignKey(
        "Customer", on_delete=models.DO_NOTHING, blank=False, null=False
    )

    class Meta:
        permissions = [("manage_loan_categories", "Can manage loan categories")]

    def __str__(self) -> str:
        return self.category_name


class Model(models.Model):
    modelid = models.CharField(
        db_column="ModelId", primary_key=True, max_length=50
    )  # Field name made lowercase.
    modelcode = models.CharField(
        db_column="ModelCode", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    modelshortname = models.CharField(
        db_column="ModelShortName", max_length=255, blank=True, null=True
    )  # Field name made lowercase.

    categoryid = models.ForeignKey(
        "Category", models.DO_NOTHING, db_column="CategoryId", blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "Model"


class Category(models.Model):
    categoryid = models.CharField(
        db_column="CategoryId", primary_key=True, max_length=50
    )  # Field name made lowercase.
    categorycode = models.CharField(
        db_column="CategoryCode", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    categoryshortname = models.CharField(
        db_column="CategoryShortName", max_length=255, blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Category"

    def __str__(self):
        return self.categoryshortname


class LoanRequest(models.Model):
    categoryid = models.ForeignKey(
        "Category", models.DO_NOTHING, db_column="CategoryId", blank=True, null=True
    )  # Field name made lowercase.
    loanrequestid = models.CharField(
        db_column="LoanRequestId", primary_key=True, max_length=50
    )  # Field name made lowercase.
    loanrequestcode = models.CharField(
        db_column="LoanRequestCode", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    loanrequeststatusid = models.CharField(
        db_column="LoanRequestStatusId", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    requestedbyid = models.CharField(
        db_column="RequestedById", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    requestdate = models.DateTimeField(
        db_column="RequestDate", blank=True, null=True
    )  # Field name made lowercase.
    modelid = models.CharField(
        db_column="ModelId", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    startdate = models.DateTimeField(
        db_column="StartDate", blank=True, null=True
    )  # Field name made lowercase.
    enddate = models.DateTimeField(
        db_column="EndDate", blank=True, null=True
    )  # Field name made lowercase.
    personnelid = models.CharField(
        db_column="PersonnelId", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    siteid = models.CharField(
        db_column="SiteId", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    locationid = models.CharField(
        db_column="LocationId", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    organisationid = models.CharField(
        db_column="OrganisationId", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    branchid = models.CharField(
        db_column="BranchId", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    teamid = models.CharField(
        db_column="TeamId", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    quantity = models.IntegerField(
        db_column="Quantity", blank=True, null=True
    )  # Field name made lowercase.
    loanrequestnotes = models.TextField(
        db_column="LoanRequestNotes", blank=True, null=True
    )  # Field name made lowercase.
    creationdate = models.DateTimeField(
        db_column="CreationDate", blank=True, null=True
    )  # Field name made lowercase.
    modificationdate = models.DateTimeField(
        db_column="ModificationDate", blank=True, null=True
    )  # Field name made lowercase.
    requestedfor = models.CharField(
        db_column="RequestedFor", max_length=255, blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "LoanRequest"


class Location(models.Model):
    locationid = models.CharField(
        db_column="LocationId", primary_key=True, max_length=50
    )  # Field name made lowercase.
    locationcode = models.CharField(
        db_column="LocationCode", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    locationshortname = models.CharField(
        db_column="LocationShortName", max_length=255, blank=True, null=True
    )  # Field name made lowercase.
    locationlongname = models.TextField(
        db_column="LocationLongName", blank=True, null=True
    )  # Field name made lowercase.
    locationdescription = models.TextField(
        db_column="LocationDescription", blank=True, null=True
    )  # Field name made lowercase.
    siteid = models.ForeignKey(
        "Site", models.DO_NOTHING, db_column="SiteId", blank=True, null=True
    )  # Field name made lowercase.
    inactive = models.BooleanField(db_column="Inactive", blank=True, null=True)
    locationtypeid = models.ForeignKey(
        "LocationType",
        models.DO_NOTHING,
        db_column="LocationTypeId",
        blank=True,
        null=True,
    )

    class Meta:
        managed = False
        db_table = "Location"

    def __str__(self) -> str:
        return self.locationshortname

    def get_site_id(self):
        return self.siteid.siteid if self.siteid else None


class Site(models.Model):
    siteid = models.CharField(
        db_column="SiteId", primary_key=True, max_length=50
    )  # Field name made lowercase.
    sitecode = models.CharField(
        db_column="SiteCode", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    siteshortname = models.CharField(
        db_column="SiteShortName", max_length=255, blank=True, null=True
    )  # Field name made lowercase.
    customerid = models.CharField(
        db_column="CustomerId",
        max_length=50,
        db_collation="SQL_Latin1_General_CP1_CI_AS",
        blank=True,
        null=True,
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Site"

    def __str__(self):
        return self.siteshortname


class Locationtype(models.Model):
    locationtypeid = models.CharField(
        db_column="LocationTypeId", primary_key=True, max_length=50
    )  # Field name made lowercase.
    locationtypecode = models.CharField(
        db_column="LocationTypeCode", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    locationtypeshortname = models.CharField(
        db_column="LocationTypeShortName", max_length=255, blank=True, null=True
    )  # Field name made lowercase.
    customerid = models.CharField(
        db_column="CustomerId",
        max_length=50,
        db_collation="SQL_Latin1_General_CP1_CI_AS",
        blank=True,
        null=True,
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "LocationType"

    def __str__(self):
        return self.locationtypeshortname


class Customer(models.Model):
    customerid = models.CharField(
        db_column="CustomerId",
        primary_key=True,
        max_length=50,
        db_collation="SQL_Latin1_General_CP1_CI_AS",
    )  # Field name made lowercase.
    customercode = models.CharField(
        db_column="CustomerCode",
        max_length=50,
        db_collation="SQL_Latin1_General_CP1_CI_AS",
        blank=True,
        null=True,
    )  # Field name made lowercase.
    customershortname = models.CharField(
        db_column="CustomerShortName",
        max_length=255,
        db_collation="SQL_Latin1_General_CP1_CI_AS",
        blank=True,
        null=True,
    )  # Field name made lowercase.
    customerlongname = models.TextField(
        db_column="CustomerLongName",
        db_collation="SQL_Latin1_General_CP1_CI_AS",
        blank=True,
        null=True,
    )  # Field name made lowercase.
    customerdescription = models.TextField(
        db_column="CustomerDescription",
        db_collation="SQL_Latin1_General_CP1_CI_AS",
        blank=True,
        null=True,
    )  # Field name made lowercase.
    customernotes = models.TextField(
        db_column="CustomerNotes",
        db_collation="SQL_Latin1_General_CP1_CI_AS",
        blank=True,
        null=True,
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "customer"

    def __str__(self):
        return self.customershortname
