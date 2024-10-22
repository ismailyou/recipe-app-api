from unittest.mock import patch
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models

def create_user(email='emailtest@example.com', password='password123'):
    return get_user_model().objects.create_user(email, password)

class ModelTests(TestCase):
    def test_create_user_with_email_successfully(self):
        email = 'test@example.com'
        password = 'changeme'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalize(self):
        sample_emails = [
            ['test@example.com', 'test@example.com'],
            ['Test1@example.com', 'Test1@example.com'],
            ['TEST2@example.COM', 'TEST2@example.com'],
            ['Test3@EXAMPLE.com', 'Test3@example.com']
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email,
                password='test123'
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email='',password='test123')


    def test_create_superuser(self):
        email = 'test@example.com'
        password = 'changeme'
        user = get_user_model().objects.create_superuser(
            email=email,
            password=password
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """ test creating a recipe"""
        user = get_user_model().objects.create_user(
            'email@example.com','goodpass'
        )
        recipe = models.Recipe.objects.create(
            user = user,
            title = 'recipe title',
            time_minutes = 60,
            price = Decimal('20.06'),
            description = 'recipe description'
        )
        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """test creating a tag"""
        user = create_user()
        tag = models.Tag.objects.create(
            user = user,
            name = 'tag name'
        )
        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test  creating an ingredient"""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user = user,
            name = 'Ingedient Name',
            quantity = '100g'
        )
        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_filename_uuid(self, mock_uuid):
        """test generating image path"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')   
