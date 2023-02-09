from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        self.assertEqual(str(self.post), post.text[:settings.STR_LIMIT])
        self.assertEqual(str(self.group), group.title)

    def test_verbose_name(self):
        """Проверяем, что verbose_name работает корректно."""
        post = PostModelTest.post
        field_verbose = {
            "text": "Текст поста",
            "pub_date": "Дата создания",
            "author": "Автор",
            "group": "Группа",
        }
        for value, expected in field_verbose.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name,
                    expected
                )

    def test_help_text(self):
        """Проверяем, что help_text работает корректно."""
        post = PostModelTest.post
        field_help_text = {
            "text": "Введите текст поста",
            "group": "Группа, к которой будет относиться пост",
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text,
                    expected
                )
