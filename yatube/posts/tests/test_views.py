import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = TEMP_MEDIA_ROOT
        cls.user = User.objects.create_user(username="User")
        cls.another_user = User.objects.create_user(
            username='Не автор'
        )
        cls.small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif",
            content=cls.small_gif,
            content_type="image/gif"
        )
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
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_user_not_author = Client()
        self.another_user_not_author.force_login(self.another_user)
        cache.clear()

    def test_posts_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон и HTTP статус OK."""
        templates_page_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={
                    "slug": self.group.slug
                }
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={
                    "username": (PostViewsTests.user.username)
                }
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={
                    "post_id": (PostViewsTests.post.pk)
                }
            ): "posts/post_detail.html",
            reverse("posts:post_create"): "posts/create_post.html",
            reverse(
                "posts:post_edit", kwargs={
                    "post_id": (PostViewsTests.post.pk)
                }
            ): "posts/create_post.html",
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_posts_show_correct_context(self):
        """Шаблоны posts сформированы с правильным контекстом."""
        namespace_dict = {
            reverse("posts:index"): "page_obj",
            reverse(
                "posts:group_list",
                args=[PostViewsTests.group.slug]
            ): "page_obj",
            reverse(
                "posts:profile",
                args=[PostViewsTests.user.username]
            ): "page_obj",
            reverse(
                "posts:post_detail",
                args=[PostViewsTests.post.pk]
            ): "post",
        }
        for reverse_name, context in namespace_dict.items():
            object = self.client.get(reverse_name)
            if context == "post":
                object = object.context[context]
            else:
                object = object.context[context][0]
            post_author_0 = object.author
            post_text_0 = object.text
            post_group_0 = object.group
            post_image_0 = object.image
            post_id_0 = object.id
            posts_dict = {
                post_author_0: PostViewsTests.user,
                post_text_0: PostViewsTests.post.text,
                post_group_0: PostViewsTests.group,
                post_image_0: PostViewsTests.post.image,
                post_id_0: PostViewsTests.post.id,
            }
            for value, expected in posts_dict.items():
                with self.subTest(value=value, expected=expected):
                    self.assertEqual(value, expected)

    def test_create_post_show_correct_context(self):
        """В create и edit передан правильный контекст."""
        namespace_list = [
            reverse("posts:post_create"),
            reverse(
                "posts:post_edit",
                args=[PostViewsTests.post.pk]
            ),
        ]
        for reverse_name in namespace_list:
            response = self.authorized_client.get(reverse_name)
            form_fields = {
                "text": forms.fields.CharField,
                "group": forms.fields.ChoiceField,
                "image": forms.fields.ImageField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get("form").fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_appears_in_correct_group(self):
        """Проверка что пост появился в нужной группе"""
        namespace_dict = {
            reverse("posts:index"): "page_obj",
            reverse(
                "posts:group_list",
                args=[PostViewsTests.group.slug]
            ): "page_obj",
            reverse(
                "posts:profile",
                args=[PostViewsTests.user.username]
            ): "page_obj",
        }
        for reverse_name, context in namespace_dict.items():
            with self.subTest(reverse_name=reverse_name, context=context):
                response = self.client.get(reverse_name)
                self.assertIn(PostViewsTests.post, response.context[context])
        another_group = Group.objects.create(
            title="Другая группа",
            slug="another-group",
            description="Описание другой группы",
        )
        response = self.client.get(
            reverse("posts:group_list", args={another_group.slug})
        )
        self.assertNotIn(PostViewsTests.post, response.context["page_obj"])

    def test_follow_user_another(self):
        """Follow работает правильно."""
        self.another_user_not_author.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}))
        follow_exists = Follow.objects.filter(
            user=self.another_user,
            author=self.user).exists()
        self.assertTrue(follow_exists)

    def test_unfollow_user_another(self):
        """Unfollow работает правильно."""
        self.another_user_not_author.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}))
        self.another_user_not_author.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user.username}))
        follow_exists = Follow.objects.filter(
            user=self.another_user,
            author=self.user).exists()
        self.assertFalse(follow_exists)

    def test_follow_post(self):
        """Новая запись автора появляется в ленте подписчиков,
        и не появляется в ленте подписок не подписчиков"""
        not_follower = User.objects.create_user(
            username='Не подписчик'
        )
        self.not_follower = Client()
        self.not_follower.force_login(not_follower)
        self.another_user_not_author.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}))
        follower_response = (
            self.another_user_not_author.get(reverse('posts:follow_index'))
        )
        post_list_old = len(follower_response.context['page_obj'])
        not_follower_response = (self.not_follower.get(
            reverse('posts:follow_index')))
        post_list_unfollowed_old = len(
            not_follower_response.context['page_obj']
        )
        Post.objects.create(
            text='Текс только для подписчиков',
            author=self.user,
            group=self.group,
        )
        new_post_to_follower = (
            self.another_user_not_author.get(reverse('posts:follow_index'))
        )
        post_list_new = len(new_post_to_follower.context['page_obj'])
        not_follower_no_post = (self.not_follower.get(
            reverse('posts:follow_index')))
        post_list_unfollowed_new = len(
            not_follower_no_post.context['page_obj']
        )
        self.assertEqual(post_list_old + 1, post_list_new)
        self.assertEqual(post_list_unfollowed_old, post_list_unfollowed_new)


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="test_author")
        cls.group = Group.objects.create(
            title="Группа",
            slug="slug",
            description="Описание",
        )
        for post_number in range(19):
            cls.post = Post.objects.create(
                text=f"Текст {post_number}",
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_posts(self):
        """Проверка: количество постов на первой
        странице равно конфигу."""
        namespace_list = [
            reverse("posts:index"),
            reverse(
                "posts:group_list",
                kwargs={"slug": PostPaginatorTests.group.slug}
            ),
            reverse(
                "posts:profile",
                kwargs={"username": PostPaginatorTests.user.username}
            ),
        ]
        posts_count = settings.POSTS_PER_PAGE
        for reverse_name in namespace_list:
            response = self.client.get(reverse_name)
            self.assertEqual(len(response.context["page_obj"]), posts_count)

    def test_second_page_contains_nine_posts(self):
        """Проверка: количество постов на
        второй странице меньше конфига."""
        namespace_list = [
            reverse("posts:index") + "?page=2",
            reverse(
                "posts:group_list",
                kwargs={"slug": PostPaginatorTests.group.slug}
            ) + "?page=2",
            reverse(
                "posts:profile",
                kwargs={"username": PostPaginatorTests.user.username}
            ) + "?page=2",
        ]
        posts_count = (settings.POSTS_PER_PAGE - 1)
        for reverse_name in namespace_list:
            response = self.client.get(reverse_name)
            self.assertEqual(len(response.context["page_obj"]), posts_count)

    def test_post_correct_context(self):
        """Проверка: содержимое постов на странице соответствует ожиданиям."""
        namespace_list = [
            reverse("posts:index"),
            reverse(
                "posts:group_list",
                kwargs={"slug": PostPaginatorTests.group.slug}
            ),
            reverse(
                "posts:profile",
                kwargs={"username": PostPaginatorTests.user.username}
            ),
        ]
        for reverse_name in namespace_list:
            response = self.client.get(reverse_name)
            page_obj = response.context["page_obj"]
            for post in page_obj:
                self.assertEqual(post.author, PostPaginatorTests.user)
                self.assertEqual(post.group, PostPaginatorTests.group)
                self.assertEqual(post.text, f"Текст {post.id-1}")


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = TEMP_MEDIA_ROOT
        cls.user = User.objects.create_user(username='User')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Название группы',
            slug='slug',
            description='Описание'
        )
        cls.post = Post.objects.create(
            text='Текст',
            group=cls.group,
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_cache_index(self):
        """Проверка: cтраница index кэшируется и обновляется."""
        response = CacheViewsTest.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='Новый тестовый текст',
            author=CacheViewsTest.user,
        )
        response_now = CacheViewsTest.authorized_client.get(
            reverse('posts:index'))
        current_posts = response_now.content
        self.assertEqual(current_posts, posts,
                         'Кэшированная страница не приходит.')

        cache.clear()
        response_new = CacheViewsTest.authorized_client.get(
            reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(current_posts, new_posts, 'Кэш не обновляется.')
