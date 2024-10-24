
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def create_user(email='user@example.com', password='goodpass'):
    return get_user_model().objects.create_user(email=email, password=password)


def detail_url(tag_id):
    """create and return tag details url"""
    return reverse('recipe:tag-detail', args=[tag_id])


class PublicTagAPITest(TestCase):
    """Test the publicly available tags API"""
    def setUP(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to access the tags API"""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagAPITest(TestCase):
    """Test the authorized tags API"""
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags"""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')

        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test getting a list of tags of the auth user"""

        new_user = create_user(email='newuser@exapmle.com')
        Tag.objects.create(user=new_user, name='Test Tag')
        tag = Tag.objects.create(user=self.user, name='Fruit')
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """ test updating a tag """
        tag = Tag.objects.create(user=self.user, name='Test Tag')
        payload = {'name': 'Updated Tag'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(res.data['name'], payload['name'])

    def test_deleting_tag(self):
        """ test deleting a tag """
        tag = Tag.objects.create(user=self.user, name='Test Tag')
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_filtred_tags_assigned_to_recipe(self):
        """Test listing tags are assigned to recipe"""
        tag1 = Tag.objects.create(user=self.user, name='Test Tag')
        tag2 = Tag.objects.create(user=self.user, name='Test Tag2')

        recipe = Recipe.objects.create(
            user=self.user,
            title='Test Recipe',
            time_minutes=10,
            price=Decimal('10.00'),
            description='Test Description'
        )
        recipe.tags.add(tag1)
        res = self.client.get(TAGS_URL, {
            'assigned_only': 1
        })
        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtred_tags_unique(self):
        """test returned list of tags must be unique"""
        tag = Tag.objects.create(user=self.user, name='Test Tag')
        Tag.objects.create(user=self.user, name='Test Tag')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Test Recipe',
            time_minutes=10,
            price=Decimal('10.00')
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Test Recipe2',
            time_minutes=10,
            price=Decimal('10.00')
        )
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {
            'assigned_only': 1
        })

        self.assertEqual(len(res.data), 1)
