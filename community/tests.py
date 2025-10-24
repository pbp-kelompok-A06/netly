from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from community.models import Forum, Forum_Post
from authentication_user.models import UserProfile
import json


class ForumViewsTestCase(TestCase):

    def setUp(self):

        self.user1 = User.objects.create_user(
            username='bambang',
            password='halo'
        )
        self.user2 = User.objects.create_user(
            username='agus',
            password='halo'
        )
        
        self.profile1 = UserProfile.objects.create(user=self.user1, fullname="bambang")
        self.profile2 = UserProfile.objects.create(user=self.user2, fullname="agus")
        

        self.forum = Forum.objects.create(
            title='Forum Bola',
            description='Forum bola ini adalah',
            creator_id=self.profile1
        )
        self.forum.member.add(self.profile1)
        

        self.post = Forum_Post.objects.create(
            header='Liverpool',
            content='kalah',
            forum_id=self.forum,
            user_id=self.profile1
        )
        

        self.client = Client()
    
    def tearDown(self):
        Forum_Post.objects.all().delete()
        Forum.objects.all().delete()
        User.objects.all().delete()


class FetchForumTestCase(ForumViewsTestCase):
    
    def test_fetch_forum_general(self):
        self.client.login(username='bambang', password='halo')
        response = self.client.get(reverse('community:forum'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum.html')
        self.assertIn('data', response.context)
        self.assertTrue(len(response.context['data']) > 0)
    
    def test_fetch_forum_member_check(self):
        self.client.login(username='bambang', password='halo')
        response = self.client.get(reverse('community:forum'))
        
        forum = response.context['data'][0]
        self.assertTrue(forum.is_member)
    
    def test_fetch_forum_non_member(self):
        self.client.login(username='agus', password='halo')
        response = self.client.get(reverse('community:forum'))
        
        forum = response.context['data'][0]
        self.assertFalse(forum.is_member)

    def test_fetch_forum_unauthenticated(self):
        response = self.client.get(reverse('community:forum'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)


class FetchForumByIdTestCase(ForumViewsTestCase):

    def test_fetch_own_forum_success(self):
        self.client.login(username='bambang', password='halo')
        response = self.client.get(
            reverse('community:fetch_forum_id', args=[self.forum.id])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['title'], 'Forum Bola')
    
    def test_fetch_other_user_forum_failure(self):
        self.client.login(username='agus', password='halo')
        response = self.client.get(
            reverse('community:fetch_forum_id', args=[self.forum.id])
        )
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(len(data['data']), 0)

    def test_fetch_forum_id_unauthenticated(self):
        response = self.client.get(reverse('community:fetch_forum_id', args=[self.forum.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)


class FetchPostByIdTestCase(ForumViewsTestCase):

    def test_fetch_posts_as_member(self):
        self.client.login(username='bambang', password='halo')
        response = self.client.get(
            reverse('community:fetch_post_id', args=[self.forum.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['header'], 'Liverpool')
    
    def test_fetch_posts_as_non_member(self):
        self.client.login(username='agus', password='halo')
        response = self.client.get(
            reverse('community:fetch_post_id', args=[self.forum.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('You are not a member of this forum.', response.content.decode())
    
    def test_fetch_posts_returns_user_data(self):

        self.client.login(username='bambang', password='halo')
        response = self.client.get(
            reverse('community:fetch_post_id', args=[self.forum.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        self.assertIn('user', data['data'][0])
        self.assertEqual(data['data'][0]['user']['username'], 'bambang')
        self.assertIn('current_user_id', data)
    
    def test_fetch_posts_render_template(self):

        self.client.login(username='bambang', password='halo')
        response = self.client.get(
            reverse('community:fetch_post_id', args=[self.forum.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum_post.html')
        self.assertIn('id_forum', response.context)
        self.assertIn('forum_name', response.context)

    def test_fetch_posts_id_unauthenticated(self):

        response = self.client.get(reverse('community:fetch_post_id', args=[self.forum.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)



class CreateForumTestCase(ForumViewsTestCase):
    
    def test_create_forum_success(self):
        self.client.login(username='bambang', password='halo')
        response = self.client.post(
            reverse('community:create_forum'),
            {
                'title': 'new forum',
                'description': 'tes'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        forum = Forum.objects.get(title='new forum')
        self.assertEqual(forum.creator_id, self.profile1)
        self.assertIn(self.profile1, forum.member.all())
    
    def test_create_forum_invalid_data(self):

        self.client.login(username='bambang', password='halo')
        response = self.client.post(
            reverse('community:create_forum'),
            {
                'title': '',  
                'description': 'Description'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_create_forum_unauthenticated(self):
        response = self.client.post(reverse('community:create_forum'), {
            'title': 'tes',
            'description': 'tes'
        })
        self.assertEqual(response.status_code, 302)


class JoinForumTestCase(ForumViewsTestCase):
    
    def test_join_forum_success(self):
        self.client.login(username='agus', password='halo')
        response = self.client.post(
            reverse('community:join_forum'),
            {'id_forum': self.forum.id}
        )
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn(self.profile2, self.forum.member.all())
    
    def test_join_forum_already_member(self):

        self.client.login(username='bambang', password='halo')
        response = self.client.post(
            reverse('community:join_forum'),
            {'id_forum': self.forum.id}
        )
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('already joined', data['msg'])

    def test_join_forum_unauthenticated(self):
        response = self.client.post(reverse('community:join_forum'), {'id_forum': self.forum.id})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)



class UnjoinForumTestCase(ForumViewsTestCase):

    def test_unjoin_forum_as_member(self):
        self.forum.member.add(self.profile2)
        self.client.login(username='agus', password='halo')
        
        response = self.client.post(
            reverse('community:unjoin_forum'),
            {'id_forum': self.forum.id}
        )
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertNotIn(self.profile2, self.forum.member.all())
    
    def test_unjoin_forum_as_creator_and_it_will_delete_forum(self):

        self.client.login(username='bambang', password='halo')
        forum_id = self.forum.id
        
        response = self.client.post(
            reverse('community:unjoin_forum'),
            {'id_forum': forum_id}
        )
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertFalse(Forum.objects.filter(id=forum_id).exists())
    
    def test_unjoin_forum_not_member(self):
        self.client.login(username='agus', password='halo')
        response = self.client.post(
            reverse('community:unjoin_forum'),
            {'id_forum': self.forum.id}
        )
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_unjoin_forum_unauthenticated(self):
        response = self.client.post(reverse('community:unjoin_forum'), {'id_forum': self.forum.id})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)


class CreatePostTestCase(ForumViewsTestCase):
    
    def test_create_post_success(self):
        self.client.login(username='bambang', password='halo')
        response = self.client.post(
            reverse('community:create_post', args=[self.forum.id]),
            {
                'header': 'tes',
                'content': 'New Content'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        post = Forum_Post.objects.get(header='tes')
        self.assertEqual(post.user_id, self.profile1)
        self.assertEqual(post.forum_id, self.forum)
    
    def test_create_post_invalid_data(self):
        self.client.login(username='bambang', password='halo')
        response = self.client.post(
            reverse('community:create_post', args=[self.forum.id]),
            {
                'header': '',  
                'content': 'tes'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_create_post_unauthenticated(self):
        response = self.client.post(reverse('community:create_post', args=[self.forum.id]), {
            'header': 'tes',
            'content': 'tes'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)



class UpdateForumTestCase(ForumViewsTestCase):
    
    def test_update_forum_as_creator(self):
        self.client.login(username='bambang', password='halo')
        response = self.client.post(
            reverse('community:update_forum', args=[self.forum.id]),
            {
                'title': 'tes update',
                'description': 'tes update'
            }
        )
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        self.forum.refresh_from_db()
        self.assertEqual(self.forum.title, 'tes update')
    
    def test_update_forum_as_non_creator(self):
        self.client.login(username='agus', password='halo')
        response = self.client.post(
            reverse('community:update_forum', args=[self.forum.id]),
            {
                'title': 'tes',
                'description': 'tes'
            }
        )
        
        self.assertEqual(response.status_code, 404)

    def test_update_forum_unauthenticated(self):
        response = self.client.post(reverse('community:update_forum', args=[self.forum.id]), {
            'title': 'tes update',
            'description': 'tes update'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)



class DeleteForumTestCase(ForumViewsTestCase):
    
    def test_delete_forum_as_creator(self):
        self.client.login(username='bambang', password='halo')
        forum_id = self.forum.id
        
        response = self.client.get(
            reverse('community:delete_forum', args=[forum_id])
        )
        
        self.assertEqual(response.status_code, 302)  
        self.assertFalse(Forum.objects.filter(id=forum_id).exists())
    
    def test_delete_forum_as_non_creator(self):
        self.client.login(username='agus', password='halo')
        response = self.client.get(
            reverse('community:delete_forum', args=[self.forum.id])
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Forum.objects.filter(id=self.forum.id).exists())

    def test_delete_forum_unauthenticated(self):
        response = self.client.get(reverse('community:delete_forum', args=[self.forum.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)



class DeletePostTestCase(ForumViewsTestCase):
    
    def test_delete_post_as_author(self):
        self.client.login(username='bambang', password='halo')
        post_id = self.post.id
        
        response = self.client.post(
            reverse('community:delete_forum_post', args=[post_id])
        )
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertFalse(Forum_Post.objects.filter(id=post_id).exists())
    
    def test_delete_post_as_non_author(self):
        self.client.login(username='agus', password='halo')
        response = self.client.post(
            reverse('community:delete_forum_post', args=[self.post.id])
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Forum_Post.objects.filter(id=self.post.id).exists())
    
    def test_delete_post_unauthenticated(self):
        response = self.client.post(reverse('community:delete_forum_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

