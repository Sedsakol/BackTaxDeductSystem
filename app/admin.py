from django.contrib import admin
from .models import User,member_profile,stair_step,fund_type,fund_list,insurance_list,insurance_type
from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.

admin.site.site_header = "TaxDeduct Admin DBMS"

User = get_user_model()

class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', )

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'password', 'active', 'admin')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]

class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email','last_login', 'date_joined', 'staff', 'is_admin','first_name','last_name','active')
    list_filter = ('admin','active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name','last_name')}),
        ('Permissions', {'fields': ('admin','staff')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ()

admin.site.register(User, UserAdmin)

class member_profileAdmin(admin.ModelAdmin):
    list_display = ('created','last_updated','user','gender','birthdate','salary','other_income','marriage','parent_num','child_num','infirm','facebook_id','risk')
    ordering = ('id',)

admin.site.register(member_profile,member_profileAdmin)

class stair_stepAdmin(admin.ModelAdmin):
    list_display = ('created','last_updated','step','max_money','rate')
    ordering = ('id',)

admin.site.register(stair_step,stair_stepAdmin)

class fund_typeAdmin(admin.ModelAdmin):
    list_display = ('created','last_updated','name','description')
    ordering = ('id',)

admin.site.register(fund_type,fund_typeAdmin)

class fund_listAdmin(admin.ModelAdmin):
    list_display = ('created','last_updated','name','description','start_date','end_date','link','risk','fundType','active')
    ordering = ('id',)

admin.site.register(fund_list,fund_listAdmin)

class insurance_typeAdmin(admin.ModelAdmin):
    list_display = ('created','last_updated','name','description')
    ordering = ('id',)

admin.site.register(insurance_type,insurance_typeAdmin)
class insurance_listAdmin(admin.ModelAdmin):
    list_display = ('created','last_updated','name','description','start_date','end_date','link','active')
    ordering = ('id',)

admin.site.register(insurance_list,insurance_listAdmin)
