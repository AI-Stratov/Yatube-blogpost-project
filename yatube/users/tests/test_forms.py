import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..forms import CreationForm

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class SignupFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = CreationForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_form_submission_creates_new_user(self):
        """При заполнении формы создаётся новый пользователь."""
        initial_user_count = User.objects.count()
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": 'johndoe',
            "email": "johndoe@example.com",
            "password1": "Pass123321",
            "password2": "Pass123321",
        }
        self.client.post(
            reverse("users:signup"), data=form_data, follow=True)
        final_user_count = User.objects.count()
        self.assertEqual(final_user_count, initial_user_count + 1)
