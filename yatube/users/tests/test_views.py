from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user")
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_users_pages_uses_correct_template(self):
        """Проверка доступности и шаблонов адресов users."""
        guest_urls_templates = {
            reverse(
                "users:signup"
            ):
                "users/signup.html",
            reverse(
                "users:logout"
            ):
                "users/logged_out.html",
            reverse(
                "users:login"
            ):
                "users/login.html",
            reverse(
                "users:password_reset"
            ):
                "users/password_reset_form.html",
            reverse(
                "users:password_reset_done"
            ):
                "users/password_reset_done.html",
        }
        for reverse_name, template in guest_urls_templates.items():
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_passwords_urls(self):
        """Страницы password_change и password_change_done
         недоступны неавторизованному клиенту."""
        password_urls = [
            reverse("users:password_change"),
            reverse("users:password_change_done"),
        ]
        for reverse_name in password_urls:
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_passwords_templates(self):
        """Для страниц password_change и password_change_done
         используются правильные шаблоны."""
        password_templates = {
            reverse(
                "users:password_change"
            ):
                "users/password_change_form.html",
            reverse(
                "users:password_change_done"
            ):
                "users/password_change_done.html",
        }
        for reverse_name, template in password_templates.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
