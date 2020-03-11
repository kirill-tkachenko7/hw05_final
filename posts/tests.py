from django.test import TestCase, Client, override_settings
from posts.models import *
from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
# from django.test.utils import setup_test_environment, teardown_test_environment
from PIL import Image
import tempfile

TEST_CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

@override_settings(CACHES=TEST_CACHE)
class PostsTest(TestCase):
    def _create_image(self):
        # create a test image to avoid accessing real files during testing
        # https://dirtycoder.net/2016/02/09/testing-a-model-that-have-an-imagefield/
 
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            image = Image.new('RGB', (200, 200), 'white')
            image.save(f, 'PNG')
 
        return open(f.name, mode='rb')

    def _create_file(self):
        file = SimpleUploadedFile('filename.txt', b'hello world', 'text/plain')
        return file
    
    def setUp(self):
        # try:
        #     setup_test_environment()
        # except:
        #     teardown_test_environment()
        #     setup_test_environment()
        self.client = Client()
        self.user = User.objects.create_user(
            username='sarah', email='connor.s@skynet.com', password='12345')
        self.follower = User.objects.create_user(
            username='T-800', email='terminator@skynet.com', password='illbeback')
        self.post = Post.objects.create(
            text="You're talking about things I haven't done yet in the past tense. It's driving me crazy!", 
            author=self.user)
        self.image = self._create_image()
        self.file = self._create_file()

    def tearDown(self):
        self.image.close()

    def test_profile(self):
        """ test that there is a user profile page for each user """
        response = self.client.get('/sarah/')
        self.assertEqual(response.status_code, 200, "profile page does not exist")
        self.assertEqual(len(response.context['page']), 1, "new post is not displayed on profile page")
        self.assertIsInstance(response.context['profile'], User)
        self.assertEqual(response.context['profile'].username, self.user.username, "wrong profile displayed")
    
    def test_add_post_authenticated(self):
        """ test that authenticated user can add new posts """
        if self.client.login(username='sarah', password='12345'):
            response = self.client.get('/new/')
            self.assertEqual(response.status_code, 200, 'Authenticated user must be able to add posts')
        else:
            self.assertTrue(False, 'Failed to authenticate test user')

    def test_add_post_anonymous(self):
        """ test that anonymous user cannot add new posts and is redirected to home page """
        self.client.logout()
        response = self.client.get('/new/')
        self.assertRedirects(response, 
            '/auth/login/?next=/new/',  
            msg_prefix="anonymous user is not redirected to login page")
    
    def test_post_home(self):
        """ test that new post appears on the home page """
        response = self.client.get('/')
        self.assertIn(self.post, 
            response.context['page'], 
            'new post must appear on the home page')
        self.assertEqual(self.post, 
            response.context['page'][0],
            "psot text is on the home page is incorrect")

    def test_post_profile(self):
        """ test that new post appears on author's profile page """
        response = self.client.get(f'/sarah/')
        self.assertIn(self.post, 
            response.context['page'], 
            "new post must appear on the author's profile page")
        self.assertEqual(self.post, 
            response.context['page'][0],
            "post text is on the author's profile page is incorrect")
        
    def test_post_view(self):
        """ test that post appears on post view page """
        response = self.client.get(f'/sarah/{self.post.id}/')

        # test that post page exists
        self.assertEqual(response.status_code, 200, "post page does not exist")

        # test that the right post is displayed
        self.assertEqual(self.post, 
            response.context['post'], 
            "new post must appear on post view page")

    def test_edit_post_anonymous(self):
        self.client.logout()
        response = self.client.get(f'/sarah/{self.post.id}/edit/')
        self.assertRedirects(response,
            f'/sarah/{self.post.id}/',
            msg_prefix='anonymous user is not redirected to post view')

    def test_edit_post_wrong_user(self):
        if self.client.login(username='T-800', password='illbeback'):
            response = self.client.get(f'/sarah/{self.post.id}/edit/')
            self.assertRedirects(response,
                f'/sarah/{self.post.id}/',
                msg_prefix='wrong user is not redirected to post view')
        else:
            self.assertTrue(False, 'Failed to authenticate test user')

    def test_edit_post_authenticated(self):
        if self.client.login(username='sarah', password='12345'):
            response = self.client.get(f'/sarah/{self.post.id}/edit/')
            self.assertEqual(response.status_code, 200, 'Authenticated user must be able to edit posts')

            # edit post and test that it was updated in the db
            orig_text = self.post.text
            new_text = "That's great see your getting it. И немного кириллицы для остроты ощущений"
            self.client.post(f'/sarah/{self.post.id}/edit/', {'text': new_text})
            self.post.refresh_from_db() # reload post after it was updated
            self.assertEqual(self.post.text, new_text)
            
            # import django.utils.html.escape to account for special characters
            # which are escaped by default in template variables
            # https://code.djangoproject.com/wiki/AutoEscaping
            from django.utils.html import escape
            
            # check that changes are reflected on home page, author's profile and post page
            for url in ('/', '/sarah/', f'/sarah/{self.post.id}/'):
                response = self.client.get(url)
                self.assertContains(response,
                    escape(self.post.text), 
                    msg_prefix=f'updates were not reflected in {url}')
                
                # make sure existing post is edited, not a new one added
                self.assertNotContains(response, 
                    escape(orig_text), 
                    msg_prefix=f'old post text remains in {url}')

        else:
            self.assertTrue(False, 'Failed to authenticate test user')

    def test_comments_anonymous(self):
        """ test that anonymous user cannot add comments """
        self.client.logout()
        response = self.client.post(f'/sarah/{self.post.id}/comment/', {'text': 'test comment'})
        self.assertFalse(
            Comment.objects.filter(post=self.post,  text='test comment').exists(),
            'Comment object was created')
        self.assertRedirects(response, f'/auth/login/?next=/sarah/{self.post.id}/comment/',
            msg_prefix='anonymous user is not redirected to login page')

    def test_comments_authenticated(self):
        """ test that authenticated user can add comments """
        if self.client.login(username='T-800', password='illbeback'):
            response = self.client.post(f'/sarah/{self.post.id}/comment/', {'text': 'deep'})
            self.assertTrue(
                Comment.objects.filter(post=self.post, author=self.follower, text='deep').exists(),
                'Comment object was not created')
            self.assertRedirects(response, f'/sarah/{self.post.id}/',
                msg_prefix='user is not redirected to post page after commenting')
            response = self.client.get(f'/sarah/{self.post.id}/')
            self.assertEqual(response.context['comments'][0].text, 'deep',
                'comment not displayed on post page')
        else:
            self.assertTrue(False, 'Failed to authenticate test user')

    def test_follow(self):
        """ test following, unfollowing and accessing followed authors' posts """
        if self.client.login(username='T-800', password='illbeback'):
            # test following
            response = self.client.get('/sarah/')
            self.assertContains(response, 'href="/sarah/follow"', 
                msg_prefix='"Follow" button not found on profile page')
            self.assertNotContains(response, 'href="/sarah/unfollow"', 
                msg_prefix='"Unfollow" button found on profile page')
            response = self.client.get('/sarah/follow')
            self.assertTrue(
                Follow.objects.filter(user=self.follower, author=self.user).exists(), 
                "Follow object was not created")
            
            # test that follower can see followed author's post 
            response = self.client.get('/follow/')
            self.assertIn(
                self.post, response.context['page'], 
                "follower can not see their subscriptions on /follow/ page")
            
            # test unfollowing
            response = self.client.get('/sarah/')
            self.assertNotContains(response, 'href="/sarah/follow"', 
                msg_prefix='"Follow" button found on profile page')
            self.assertContains(response, 'href="/sarah/unfollow"', 
                msg_prefix='"Unfollow" button not found on profile page')
            response = self.client.get('/sarah/unfollow')
            self.assertFalse(Follow.objects.filter(user=self.follower, author=self.user).exists(),
                "Follow object was not deleted")

            # test that author's posts do not appear on /follow/ for non-followers
            response = self.client.get('/follow/')
            self.assertNotIn(
                self.post, response.context['page'], 
                "author not followed, but their post appears on /follow/")
        else:
            self.assertTrue(False, 'Failed to authenticate test user')

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_image_upload(self):
        if self.client.login(username='sarah', password='12345'):
            # add an image to the test post
            response = self.client.post(f'/sarah/{self.post.id}/edit/', 
                {'text': self.post.text, 'image': self.image})
            
            # test that image successfully uploaded
            self.assertRedirects(response, f'/sarah/{self.post.id}/')

            # check that changes are reflected on home page, author's profile and post page
            for url in ('/', '/sarah/', f'/sarah/{self.post.id}/'):
                response = self.client.get(url)
                self.assertContains(response,
                    "<img", 
                    msg_prefix=f'image is not shown in {url}')
        else:
            self.assertTrue(False, 'Failed to authenticate test user')

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_non_image_upload(self):
        if self.client.login(username='sarah', password='12345'):
            response = self.client.post(f'/sarah/{self.post.id}/edit/', 
                {'text': self.post.text, 'image': self.file})
            self.assertTrue(response.context['form'].has_error('image'))
        else:
            self.assertTrue(False, 'Failed to authenticate test user')
    
class TestCache(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='sarah', 
            email='connor.s@skynet.com', 
            password='12345')
        self.client = Client()
        self.client.login(username='sarah', password='12345')

    def test_index_cache_key(self):
        """ test that there is cache with key 'index_page' """
        key = make_template_fragment_key('index_page', [1])
        self.client.get('/')
        self.assertTrue(bool(cache.get(key)), 'no data in cache under key "index_page"')
        cache.clear()
        self.assertFalse(bool(cache.get(key)), 'cache not cleared')
    
    def test_index_cache(self):
        """ test that changes appear on index page only after cache is cleared """
        response = self.client.get('/')
        self.client.post('/new/', {'text': 'There is no fate but what we make for ourselves.'})
        response = self.client.get('/')
        self.assertNotContains(
            response, 
            'There is no fate but what we make for ourselves.', 
            msg_prefix="index page not cached")
        cache.clear()
        response = self.client.get('/')
        self.assertContains(
            response, 
            'There is no fate but what we make for ourselves.', 
            msg_prefix="post does not appear on index page after clearing cache")


