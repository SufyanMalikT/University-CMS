from django.test import TestCase
from django.contrib.auth import get_user_model
# Create your tests here.

User = get_user_model()
class CustomUserModelTest(TestCase):
    def setUp(self):
        user = User.objects.create(username='user1',email='user1@gmail.com')
        user.set_password("user100")
