import tempfile
from io import BytesIO

from PIL import Image
from django.core.cache import cache
from django.core.files.temp import NamedTemporaryFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import User, Post, Follow


class TestPosts(TestCase):
    def setUp(self):
        self.new_user = User.objects.create(
            username='test_user',
            email='test@test.test',
            is_active=True,
            last_name='Test',
            password='test',
        )
        self.client_auth = Client()
        self.client_auth.force_login(self.new_user)
        self.client_unauth = Client()

    def check_post_on_pages(self, username, post_id, post_text):
        cache.clear()
        urls = [
            reverse('index'),
            reverse(
                'post', kwargs={'username': username,
                                'post_id': post_id},
            ),
            reverse('profile', kwargs={'username': username}),
        ]
        for url in urls:
            response = self.client_auth.get(url)
            self.assertContains(response, post_text)

    def test_new_user(self):
        response = (
            self.client_auth.get(
                reverse('profile', kwargs={'username': self.new_user})
            )
        )
        self.assertEqual(
            response.status_code, 200, msg='Страница /username/ не найдена'
        )

    def test_create_post_unauth_user(self):
        response = self.client_unauth.get(reverse('new_post'))
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_create_post_auth_user(self):
        self.client_auth.post(
            reverse('new_post'), data={'text': 'Новый пост'}, )
        post = Post.objects.last()
        self.check_post_on_pages(self.new_user.username, post.id, post.text)

    def test_edit_myself_post(self):
        post = Post.objects.create(text='test post',
                                   author_id=self.new_user.id)
        self.client_auth.post(
            reverse('post_edit',
                    kwargs={'username': self.new_user.username,
                            'post_id': post.id}),
            data={'text': 'Отредактированный текст'},
        )
        self.check_post_on_pages(self.new_user.username, post.id,
                                 'Отредактированный текст')

    def test_404_error(self):
        response = self.client_unauth.get('/404/', follow=True)
        self.assertEqual(response.status_code, 404)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_image(self):
        cache.clear()
        temp = NamedTemporaryFile()
        img_data = BytesIO()
        image = Image.new("RGB", size=(1, 1), color=(255, 0, 0, 0))
        image.save(img_data, format='JPEG')
        image = (
            SimpleUploadedFile(
                temp.name + '.jpg',
                img_data.getvalue(),
                'image/png'
            )
        )
        post = Post.objects.create(
            author=self.new_user,
            text='image test',
            image=image,
        )
        response = self.client_auth.get(reverse('index'))
        self.assertContains(response, '<img')

        response = (
            self.client_auth.get(
                reverse('profile', kwargs={'username': self.new_user})
            )
        )
        self.assertContains(response, '<img')

        response = (
            self.client.get(
                reverse(
                    'post',
                    kwargs={'username': self.new_user, 'post_id': post.id}
                )
            )
        )
        self.assertContains(response, '<img')

    def test_wrong_image(self):
        temp = NamedTemporaryFile(suffix='txt')
        with open(temp.name, mode='rb') as fp:
            self.response = (
                self.client_auth.post(
                    reverse('new_post'),
                    {'text': 'wrong file', 'image': fp},
                    follow=True
                )
            )
        self.assertNotEqual(self.response.status_code, 302)

    def test_cache(self):
        response = cache.get(reverse('index'), None)
        self.assertEqual(response, None)


class Follower(TestCase):
    def setUp(self):
        self.client_auth = Client()
        self.test_user_1 = (
            User.objects.create_user(
                username='test_user_1',
                email='test_user_1@test.ru',
                password='12345'
            )
        )
        self.test_user_2 = (
            User.objects.create_user(
                username='test_user_2',
                email='test_user_2@test.ru',
                password='12345'
            )
        )
        self.test_user_3 = (
            User.objects.create_user(
                username='test_user_3',
                email='test_user_3@test.ru',
                password='12345'
            )
        )
        self.post = (
            Post.objects.create(
                text='Some test text', author=self.test_user_2
            )
        )
        self.client_auth.force_login(self.test_user_1)

    def test_follow(self):
        self.client.force_login(self.test_user_1)
        self.client.get(reverse(
            'profile_follow', kwargs={'username': self.test_user_2.username})
        )
        self.assertEqual(Follow.objects.count(), 1)

    def test_unfollow(self):
        self.client.force_login(self.test_user_1)
        self.client.get(reverse(
            'profile_follow', kwargs={'username': self.test_user_2.username})
        )
        self.client.get(
            reverse(
                'profile_unfollow',
                kwargs={'username': self.test_user_2.username}
            )
        )
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_post(self):
        self.client.force_login(self.test_user_1)
        self.client.get(reverse(
            'profile_follow', kwargs={'username': self.test_user_2.username})
        )
        response = self.client.get(reverse('follow_index'))
        self.assertContains(response, self.post.text, status_code=200)
        self.client.force_login(self.test_user_3)
        response = self.client.get(reverse('follow_index'))
        self.assertNotContains(response, self.post.text, status_code=200)

    def test_comment(self):
        self.client_auth.post(
            reverse('new_post'),
            {'text': 'test_comment'},
            follow=True
        )
        response = self.client.post(
            reverse(
                'add_comment',
                kwargs={
                    'username': self.post.author.username,
                    'post_id': self.post.id}
            ),
            {'text': 'comment_text'}
        )

        self.assertRedirects(
            response,
            (
                f'/auth/login/?next=/'
                f'{self.post.author.username}/{self.post.id}/comment/'
            ),
        )
        self.client_auth.post(
            reverse(
                'add_comment',
                kwargs={
                    'username': self.post.author.username,
                    'post_id': self.post.id}
            ),
            {'text': 'comment_text'}
        )
        response = (
            self.client.get(
                reverse(
                    'post',
                    kwargs={'username': self.post.author.username,
                            'post_id': self.post.id}
                )
            )
        )
        self.assertContains(response, 'comment_text',)
