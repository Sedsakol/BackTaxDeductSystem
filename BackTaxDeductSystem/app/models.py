from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
# Create your models here.


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_member(self, email, password=None):

        user = self.create_user(
            email,
            password=password,
        )
        user.bemember = True

        profile = member(user=user)
        profile.save()
        user.save(using=self._db)
        return user
    
    def create_admin(self, email, password=None):

        user = self.create_user(
            email,
            password=password,
        )
        medpoint_admin.objects.create(user=user)
        user.admin = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):

        user = self.create_user(
            email,
            password=password,
        )
        medpoint_admin.objects.create(user=user)
        user.admin = True
        user.staff = True
        user.save(using=self._db)
        return user

class MemberUser(User):

    class Meta:
        proxy = True

class AdminUser(User):

    class Meta:
        proxy = True


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    first_name = models.CharField(max_length=250, null=True, blank=True)
    last_name = models.CharField(max_length=250, null=True, blank=True)
    
    
    #user_type
    admin = models.BooleanField(default=False)  # admin
    staff = models.BooleanField(default=False)  # super admin

    #user permission รออัพเดท!!!
    #user_permissions = models.ForeignKey(user_permissions, on_delete=models.CASCADE)

    last_login = models.DateTimeField(auto_now=True, editable=False, null=True)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    date_joined = models.DateTimeField(default=timezone.now, editable=False)
    
    active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

class member_profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gender = models.CharField(max_length=250, null=True)
    birthdate = models.DateField()
    salary = models.IntegerField(null=True,blank=True)
    other_income = models.IntegerField(null=True,blank=True)
    parent_num = models.IntegerField(null=True,blank=True)
    child_num = models.IntegerField(null=True,blank=True)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    infirm = models.IntegerField(null=True,blank=True)
    facebook_id = models.IntegerField(null=True,blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    
