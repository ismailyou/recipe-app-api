from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')

def detail_url(recipe_id):
    return reverse('recipe:ingredient-detail', args=[recipe_id])

def create_user(email='user@example.com', password='goodpassword'):
    return get_user_model().objects.create_user(email, password)

def create_ingredient(user, **params):

    defaults = {
        'name': 'Test ingredient',
        'quantity': 10
    }
    defaults.update(params)
    return Ingredient.objects.create(user=user, **defaults)

class PublicIngredientAPITest(TestCase):
    """Test public available ingredient api"""
    def setUp(self):
        self.client = APIClient()

    
    def test_retrieve_ingredient(self):
        """Test retrieving a list of ingredients"""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateIngredientAPITest(TestCase):
    """Test priviate available ingredient api"""
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_rerieve_ingredients(self):
        """Test retrieving a list of ingredients"""
        create_ingredient(user=self.user, name='Kale')
        create_ingredient(user=self.user, name='Vanilla')

        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        """Test retrieving a list of ingredients of a given user"""
        new_user = create_user(email='newuser@example.com')
        create_ingredient(user=new_user)
        create_ingredient(user=new_user)
        ingredient = create_ingredient(user=self.user, name="Banana")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """Test updating an existing ingredient."""

        ingredient = create_ingredient(user=self.user)
        url = detail_url(ingredient.id)

        payload = {'name': 'Updated Ingredient', 'quantity': 15}    

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()

        self.assertEqual(ingredient.name, payload['name'])
        self.assertEqual(ingredient.quantity, str(payload['quantity']))

    def test_delete_ingredient(self):
        """ Test delete ingredient"""
        ingredient = create_ingredient(user=self.user)
        url = detail_url(ingredient.id)

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())


    def test_filter_ingredients_assigned_to_recipe(self):
        """" Test filter ingredients assigned to recipe"""
        ing1 = Ingredient.objects.create(user=self.user, name="Apple")
        ing2 = Ingredient.objects.create(user=self.user, name="Turky")
        recipe = Recipe.objects.create(
            title = 'Recipe for test',
            price = Decimal('20.03'),
            time_minutes = 30,
            description = 'Test recipe',
            user = self.user
        )

        recipe.ingredients.add(ing1)

        res = self.client.get(INGREDIENTS_URL, {
            'assigned_only': 1
        })
        s1 = IngredientSerializer(ing1)
        s2 = IngredientSerializer(ing2)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filterd_ingredients_unique(self):
        """Test filtred ingredients return unique list"""
        ing1 = Ingredient.objects.create(user=self.user, name="Eggs")
        Ingredient.objects.create(user=self.user, name="Lentils")

        recipe1 = Recipe.objects.create(
            title = 'Recipe for test',
            price = Decimal('20.03'),
            time_minutes = 30,
            description = 'Test recipe',
            user = self.user
        )
        recipe2 = Recipe.objects.create(
            title = 'Recipe',
            price = Decimal('23.03'),
            time_minutes = 30,
            description = 'Test recipe',
            user = self.user
        )

        recipe1.ingredients.add(ing1)
        recipe2.ingredients.add(ing1)

        res = self.client.get(INGREDIENTS_URL, {
            'assigned_only': 1
        })

        self.assertEqual(len(res.data), 1)