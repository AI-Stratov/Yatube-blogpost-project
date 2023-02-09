from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_urls(self):
        """Проверка доступности и шаблонов адресов /tech/ и /author/."""
        urls_templates = {
            "/about/author/": "about/author.html",
            "/about/tech/": "about/tech.html",
        }
        for url, template in urls_templates.items():
            with self.subTest(name="Тестирую {} URL".format(url)):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_namespace(self):
        """Проверка namespace:name приложения about."""
        namespaces_templates = {
            reverse("about:author"): "about/author.html",
            reverse("about:tech"): "about/tech.html",
        }
        for reverse_name, template in namespaces_templates.items():
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
