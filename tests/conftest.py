import pytest
import csv
import os
from pathlib import Path
from rest_framework.test import APIClient
from tests.factories.user_factory import UserFactory, DoctorFactory, PatientFactory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def auto_login_user(api_client, user_factory):
    user = user_factory()
    api_client.force_authenticate(user=user)
    return api_client, user

def load_test_data(filename):
    """Hàm đọc file CSV từ thư mục tests/data/"""
    base_path = Path(__file__).parent / "data"
    file_path = base_path / filename
    
    data_list = []
    if os.path.exists(file_path):
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data_list.append(row)
    return data_list

