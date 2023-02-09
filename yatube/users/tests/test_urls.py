from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CreationForm

User = get_user_model()


class UsersURLTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user")
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_users_unauthorized_urls(self):
        """Проверка доступности и шаблонов адресов users."""
        guest_urls_templates = {
            "/auth/signup/":
            "users/signup.html",
            "/auth/logout/":
            "users/logged_out.html",
            "/auth/login/":
            "users/login.html",
            "/auth/password_reset/":
            "users/password_reset_form.html",
            "/auth/password_reset/done/":
            "users/password_reset_done.html",
            "/auth/reset/<uidb64>/<token>/":
            "users/password_reset_confirm.html",
            "/auth/reset/done/":
            "users/password_reset_complete.html",
        }
        for url, template in guest_urls_templates.items():
            with self.subTest(name="Тестирую {} URL".format(url)):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_passwords_urls(self):
        """Страницы password_change и password_change_done
         недоступны неавторизованному клиенту."""
        password_urls = [
            "/auth/password_change/",
            "/auth/password_change/done/",
        ]
        for url in password_urls:
            with self.subTest(name="Тестирую {} URL".format(url)):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_passwords_templates(self):
        """Для страниц password_change и password_change_done
         используются правильные шаблоны."""
        password_templates = {
            "/auth/password_change/": "users/password_change_form.html",
            "/auth/password_change/done/": "users/password_change_done.html",
        }
        for url, template in password_templates.items():
            with self.subTest(name="Тестирую {} URL".format(url)):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_signup_page_passes_form(self):
        """На страницу reverse('users:signup') в контексте
         передаётся форма для создания нового пользователя.."""
        response = self.guest_client.get(reverse("users:signup"))
        self.assertIsInstance(response.context["form"], CreationForm)
        self.assertContains(
            response, "csrfmiddlewaretoken"
        )
