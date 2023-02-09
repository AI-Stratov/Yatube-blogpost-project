from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="User")
        cls.group = Group.objects.create(
            title="Заголовок",
            slug="slug",
            description="Описание",
        )
        cls.post = Post.objects.create(
            text="Текст",
            pub_date="Дата",
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_unexisting_url_returns_404(self):
        """Запрос к несуществующей странице вернёт ошибку 404
        и кастомный шаблон."""
        response = self.client.get("/unexisting_page/")
        template = "core/404.html"
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, template)

    def test_urls(self):
        """URL-адрес использует соответствующий шаблон."""
        urls_templates = {
            "/": "posts/index.html",
            f"/profile/{PostURLTests.user.username}/": "posts/profile.html",
            f"/group/{PostURLTests.group.slug}/": "posts/group_list.html",
            f"/posts/{PostURLTests.post.id}/": "posts/post_detail.html",
            "/create/": "posts/create_post.html",
            f"/posts/{PostURLTests.post.id}/edit/": "posts/create_post.html",
        }
        for (
            url,
            template,
        ) in urls_templates.items():
            with self.subTest(name="Тестирую {} URL".format(url)):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_guest(self):
        """Страницы index, group, profile и post
        доступны неавторизованному клиенту"""
        url_names = [
            "/",
            f"/group/{PostURLTests.group.slug}/",
            f"/profile/{PostURLTests.user.username}/",
            f"/posts/{PostURLTests.post.id}/",
        ]
        for url in url_names:
            with self.subTest(name="Тестирую {} URL".format(url)):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_authorized(self):
        """Страницы create и post_edit недоступны неавторизованному клиенту"""
        url_names = [
            "/create/",
            f"/posts/{PostURLTests.post.id}/edit/",
        ]
        for url in url_names:
            with self.subTest(name="Тестирую {} URL".format(url)):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_url_redirect_guest(self):
        """ Страница create перенаправляет неавторизованного клиента
        на страницу авторизации."""
        response = self.client.get("/create/", follow=True)
        self.assertRedirects(response, "/auth/login/?next=/create/")

    def test_post_edit_author_check(self):
        """ Только у автора есть доступ к редактированию поста."""
        new_user = User.objects.create_user(username='newuser')
        self.client.force_login(new_user)
        response = self.authorized_client.get(
            f"/posts/{PostURLTests.post.id}/edit/"
        )
        new_response = self.client.get(
            f"/posts/{PostURLTests.post.id}/edit/"
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(new_response.status_code, HTTPStatus.FORBIDDEN)
