import tempfile
from io import BytesIO

from PIL import Image
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
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

    # def test_create_post_auth_user(self):
    #     self.client_auth.post(
    #         reverse('new_post'), data={'text': 'Новый пост'}, )
    #     post = Post.objects.last()
    #     self.check_post_on_pages(self.new_user.username, post.id, 'Новый пост')
    #
    #     def test_edit_myself_post(self):
    #         post = Post.objects.create(text='test post',
    #                                    author_id=self.new_user.id)
    #         self.client_login.post(
    #             reverse('post_edit',
    #                     kwargs={'username': self.new_user.username,
    #                             'post_id': post.id}),
    #             data={'text': 'Отредактированный текст'},
    #         )
    #         self.check_post_on_pages(self.new_user.username, post.id,
    #                                  'Отредактированный текст')

    def test_404_error(self):
        response = self.client_unauth.get('/404/', follow=True)
        self.assertEqual(response.status_code, 404)

    def test_image(self):
        img_data = BytesIO()
        image = Image.new("RGB", size=(1, 1), color=(255, 0, 0, 0))
        image.save(img_data, format='JPEG')
        image_name = 'test'
        image = (
            SimpleUploadedFile(
                image_name + '.jpg',
                img_data.getvalue(),
                'image/png'
            )
        )

        self.client_auth.post(
            reverse('new_post'),
            {'text': 'image test',
             'image': image},
            follow=True
        )
        post = Post.objects.last()
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
        with open('posts/apps.py', mode='rb') as fp:
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

    def post_follow_check(self, post, follow=False):
        cache.clear()
        response = self.client.get(f'/follow/')
        if follow:
            self.assertContains(response, post.text)
        else:
            self.assertNotContains(response, post.text)

    def test_follow(self):
        self.client_auth.post(
            reverse('new_post'),
            {'text': 'test_follow'},
            follow=True
        )
        post = Post.objects.last()
        response = self.client.get('/follow/')
        self.assertRedirects(response, '/auth/login/?next=/follow/')
        self.post_follow_check(post, False)
        self.client_auth.get(f'/{post.author.username}/follow/')
        self.post_follow_check(post, True)
        self.client_auth.get(f'/{post.author.username}/unfollow/')
        self.post_follow_check(post, False)

    def test_comment(self):
        self.client_auth.post(
            reverse('new_post'),
            {'text': 'test_comment'},
            follow=True
        )
        post = Post.objects.last()
        comment_text = 'comment'
        response = self.client.post(
            f'/{post.author.username}/{post.id}/comment/',
            {'text': comment_text})
        self.assertRedirects(
            response,
            f'/auth/login/?next=/{post.author.username}/{post.id}/comment/',
        )
        self.client_auth.post(
            f'/{post.author.username}/{post.id}/comment/',
            {'text': comment_text}
        )
        response = self.client.get(f'/{post.author.username}/{post.id}/')
        self.assertContains(response, comment_text,)
