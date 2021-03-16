from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin , Group
from django.utils import timezone
from solo.models import SingletonModel

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
        member_profile.objects.create(user=user)
        user.save(using=self._db)
        return user
    
    def create_admin(self, email, password=None):

        user = self.create_user(
            email,
            password=password,
        )
        user.admin = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):

        user = self.create_user(
            email,
            password=password,
        )
        user.admin = True
        user.staff = True
        user.save(using=self._db)
        return user

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

    group = models.ManyToManyField(Group, blank=True, related_name='user_groups')
    

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        return self.email

    def __str__(self):              # __unicode__ on Python 2
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.staff

    @property
    def is_admin(self):
        "Is the user a admin member?"
        return self.admin

    @property
    def is_active(self):
        "Is the user active?"
        return self.active

    @property
    def is_superpartner(self):
        "Is the user superpartner?"
        return self.superpartner

    @property
    def is_member(self):
        "Is the user member?"
        return self.bemember

    @property
    def is_partner(self):
        "Is the user active?"
        return self.bepartner

    @property
    def is_seller(self):
        "Is the user active?"
        return self.seller
    

class MemberUser(User):

    class Meta:
        proxy = True

class AdminUser(User):

    class Meta:
        proxy = True
        
class member_profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gender = models.CharField(max_length=250, null=True,blank=True)
    birthdate = models.DateField(null=True,blank=True)
    salary = models.IntegerField(null=True,blank=True)
    other_income = models.IntegerField(null=True,blank=True)
    parent_num = models.IntegerField(null=True,blank=True)
    child_num = models.IntegerField(null=True,blank=True)
    marriage = models.IntegerField(null=True,blank=True)
    infirm = models.IntegerField(null=True,blank=True)
    facebook_id = models.CharField(max_length=250, null=True,blank=True)
    risk = models.CharField(max_length=250, null=True,blank=True)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

#stair
class stair_step(models.Model):
    step = models.IntegerField(unique=True)
    max_money = models.IntegerField(null=True,blank=False)
    rate = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)


#fund
class fund_type(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250 ,null=True ,blank=True)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f'{self.name}'

class fund_list(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    start_date = models.DateField()
    end_date = models.DateField()
    link = models.CharField(max_length=250)
    risk = models.IntegerField()
    fundType = models.ManyToManyField(fund_type)
    dividend_payout = models.BooleanField(default=False)
    asset_management = models.CharField(max_length=250, null=True)
    active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f'{self.name}'

#insurance
class insurance_type(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250 ,null=True ,blank=True)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f'{self.name}'
    
class insurance_list(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    public_limited_company = models.CharField(max_length=250, null=True)
    link = models.CharField(max_length=250)
    insuranceType = models.ManyToManyField(insurance_type)
    active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f'{self.name}'

#facebook
class facebook_categories(models.Model):
    facebook_id = models.CharField(max_length=250, null=False,blank=False)
    categories_version = models.IntegerField(null=False,blank=False)
    data = models.JSONField()
    created = models.DateTimeField(auto_now_add=True, editable=False)

#plan_type
class plan_types(models.Model):
    plan_name = models.CharField(max_length=250, null=False,blank=False)
    plan_description = models.CharField(max_length=250, null=False,blank=False)
    plan_data = models.TextField(null=False,blank=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return f'Plan Type {self.pk} : {self.plan_name}'

#dataset
class dataset(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    facebook_id = models.CharField(max_length=250, null=True,blank=True)
    gender = models.CharField(max_length=250, null=True,blank=True)
    age = models.IntegerField(null=True,blank=True)
    salary = models.IntegerField(null=True,blank=True)
    other_income = models.IntegerField(null=True,blank=True)
    parent_num = models.IntegerField(null=True,blank=True)
    child_num = models.IntegerField(null=True,blank=True)
    marriage = models.IntegerField(null=True,blank=True)
    infirm = models.IntegerField(null=True,blank=True)
    risk_question = models.CharField(max_length=250, null=True,blank=True)
    risk_type = models.IntegerField(null=True,blank=True)
    categories_version = models.IntegerField(null=False,blank=False)
    categories_data = models.JSONField()
    ans_type = models.IntegerField(null=True,blank=True)

class predict_dataset(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    facebook_id = models.CharField(max_length=250, null=True,blank=True)
    gender = models.CharField(max_length=250, null=True,blank=True)
    age = models.IntegerField(null=True,blank=True)
    salary = models.IntegerField(null=True,blank=True)
    other_income = models.IntegerField(null=True,blank=True)
    parent_num = models.IntegerField(null=True,blank=True)
    child_num = models.IntegerField(null=True,blank=True)
    marriage = models.IntegerField(null=True,blank=True)
    infirm = models.IntegerField(null=True,blank=True)
    risk_question = models.CharField(max_length=250, null=True,blank=True)
    risk_type = models.IntegerField(null=True,blank=True)
    categories_version = models.IntegerField(null=False,blank=False)
    categories_data = models.JSONField()
    predict_ans_type = models.IntegerField(null=True,blank=True)

class MLConfiguration(SingletonModel):
    ml_file_name = models.CharField(max_length=255, default='sklearn_model.sav', help_text='example : sklearn_model.sav')
    categories_version = models.IntegerField(default=1)
    drop_features = models.TextField(null=True, blank=True, default="['Art', 'Band', 'Chef', 'Mood', 'Show', 'Actor', 'Cause', 'Color', 'Event', 'Gamer', 'Legal', 'Topic', 'Author', 'Course', 'Dancer', 'Editor', 'Sports', 'Athlete', 'Cuisine', 'Finance', 'Profile', 'Science', 'Comedian', 'Designer', 'Diseases', 'Election', 'Fan Page', 'Language', 'Locality', 'Musician', 'Producer', 'Orchestra', 'Residence', 'Scientist', 'Surgeries', 'Journalist', 'Agriculture', 'Labor Union', 'Nationality', 'Real Estate', 'Social Club', 'Sports Club', 'Visual Arts', 'Work Status', 'Armed Forces', 'Concert Tour', 'Entrepreneur', 'Meeting Room', 'Talent Agent', 'Ticket Sales', 'Work Project', 'Fashion Model', 'Film Director', 'Fitness Model', 'Literary Arts', 'Public Toilet', 'Satire/Parody', 'Sports Season', 'Work Position', 'Not a Business', 'Campus Building', 'Digital Creator', 'Harmonized Page', 'Hotel & Lodging', 'Performance Art', 'Performing Arts', 'Sports Promoter', 'Theatrical Play', 'Exchange Program', 'Medical & Health', 'News Personality', 'Spiritual Leader', 'Community Service', 'Editorial/Opinion', 'University (NCES)', 'University Status', 'Outdoor Recreation', 'Youth Organization', 'City Infrastructure', 'Charity Organization', 'Motivational Speaker', 'Private Members Club', 'Advertising/Marketing', 'Sorority & Fraternity', 'Religious Organization', 'Theatrical Productions', 'Commercial & Industrial', 'Travel & Transportation', 'Country Club / Clubhouse', 'Media Restoration Service', 'Religious Place of Worship', 'Automotive, Aircraft & Boat', 'Landmark & Historical Place', 'Public & Government Service', 'Automated Teller Machine (ATM)', 'Beauty, Cosmetic & Personal Care', 'Non-Governmental Organization (NGO)', 'Environmental Conservation Organization']" ,
                                    help_text="example : ['Art', 'Band', 'Chef', 'Mood', 'Show', 'Actor', 'Cause', 'Color', 'Event', 'Gamer', 'Legal', 'Topic', 'Author', 'Course', 'Dancer', 'Editor', 'Sports', 'Athlete', 'Cuisine', 'Finance', 'Profile', 'Science', 'Comedian', 'Designer', 'Diseases', 'Election', 'Fan Page', 'Language', 'Locality', 'Musician', 'Producer', 'Orchestra', 'Residence', 'Scientist', 'Surgeries', 'Journalist', 'Agriculture', 'Labor Union', 'Nationality', 'Real Estate', 'Social Club', 'Sports Club', 'Visual Arts', 'Work Status', 'Armed Forces', 'Concert Tour', 'Entrepreneur', 'Meeting Room', 'Talent Agent', 'Ticket Sales', 'Work Project', 'Fashion Model', 'Film Director', 'Fitness Model', 'Literary Arts', 'Public Toilet', 'Satire/Parody', 'Sports Season', 'Work Position', 'Not a Business', 'Campus Building', 'Digital Creator', 'Harmonized Page', 'Hotel & Lodging', 'Performance Art', 'Performing Arts', 'Sports Promoter', 'Theatrical Play', 'Exchange Program', 'Medical & Health', 'News Personality', 'Spiritual Leader', 'Community Service', 'Editorial/Opinion', 'University (NCES)', 'University Status', 'Outdoor Recreation', 'Youth Organization', 'City Infrastructure', 'Charity Organization', 'Motivational Speaker', 'Private Members Club', 'Advertising/Marketing', 'Sorority & Fraternity', 'Religious Organization', 'Theatrical Productions', 'Commercial & Industrial', 'Travel & Transportation', 'Country Club / Clubhouse', 'Media Restoration Service', 'Religious Place of Worship', 'Automotive, Aircraft & Boat', 'Landmark & Historical Place', 'Public & Government Service', 'Automated Teller Machine (ATM)', 'Beauty, Cosmetic & Personal Care', 'Non-Governmental Organization (NGO)', 'Environmental Conservation Organization']"
                                    )

    def __str__(self):
        return "Machine Learning Configuration"

    class Meta:
        verbose_name = "Machine Learning Configuration"