import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="test_user")
        cls.group = Group.objects.create(
            title="Заголовок",
            slug="slug",
            description="Описание",
        )
        cls.post = Post.objects.create(
            text="Текст",
            author=cls.user,
            group=cls.group,
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_authorized_client_post_create(self):
        """При отправке валидной формы со страницы создания
        поста создаётся новая запись в базе данных."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            "text": "Пост от авторизованного пользователя",
            "author": PostFormsTests.user,
            "group": PostFormsTests.group.pk,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.latest('pk')
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.author, form_data['author'])
        self.assertEqual(new_post.group.pk, form_data['group'])
        self.assertEqual(
            new_post.image.field.upload_to + uploaded.name,
            new_post.image.name
        )
        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={
                "username": PostFormsTests.user.username
            }),
        )

    def test_authorized_post_edit(self):
        """При отправке валидной формы со страницы редактирования поста
         происходит изменение поста с post_id в базе данных."""
        post_count = Post.objects.count()
        form_data = {
            "text": "Отредактированный пост",
            "author": PostFormsTests.user,
            "group": PostFormsTests.group.pk,
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={
                "post_id": PostFormsTests.post.pk
            }),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), post_count)
        new_post = Post.objects.get(pk=PostFormsTests.post.pk)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.author, form_data['author'])
        self.assertEqual(new_post.group.pk, form_data['group'])
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={
                "post_id": PostFormsTests.post.pk
            }),
        )

    def test_guest_client_post_create(self):
        """Неавторизованный пользователь не может создавать посты."""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Пост от неавторизованного пользователя",
            "group": PostFormsTests.group.id,
        }
        self.client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_comment_authorized(self):
        """Авторизованный пользователь может писать комментарии."""
        comment_count = Comment.objects.count()
        post_id = self.post.pk
        form_comment_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_comment_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        new_comment = Comment.objects.latest('pk')
        self.assertEqual(new_comment.text, form_comment_data['text'])
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': post_id}))

    def test_comment_unauthorized(self):
        """Неавторизованный пользователь не может
        писать комментарии."""
        comment_count = Comment.objects.count()
        post_id = self.post.pk
        form_comment_data = {
            'text': 'Тестовый комментарий',
        }
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_comment_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
