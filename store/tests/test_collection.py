from rest_framework import status
from store.models import Collection
from django.contrib.auth.models import User
import pytest
from model_bakery import baker

@pytest.fixture
def create_collection(api_client):
    def do_create_collection(collection):
        return api_client.post('/store/collections/', collection)
    return do_create_collection





@pytest.mark.django_db
class TestCreateCollection:
    def test_if_user_is_anonymous_returns_401(self, authenticate, create_collection):
        response = create_collection({'title':'a'})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        
    def test_if_user_is_not_admin_returns_403(self, authenticate, create_collection):
        authenticate()  #ARRANGE PART
        
        response = create_collection({'title':'a'})   #ACT PART
        
        assert response.status_code == status.HTTP_403_FORBIDDEN  #ASSERTION PART
        
    def test_if_data_is_valid_returns_201(self, authenticate, create_collection):
        authenticate(is_staff=True)
        
        response = create_collection({'title':'a'})
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['id'] > 0
        
        
@pytest.mark.django_db       
class TestRetriveCollection:
    def test_if_collection_exist_returns_200(self, api_client):
        collection = baker.make(Collection)
        
        response =  api_client.get(f'/store/collections/{collection.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'id': collection.id,
            'title':collection.title,
            'products_count':0
        }
        
        