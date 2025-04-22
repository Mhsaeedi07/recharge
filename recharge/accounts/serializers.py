from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Seller

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_seller', 'is_admin_user']
        read_only_fields = ['is_seller', 'is_admin_user']


class SellerSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)

    class Meta:
        model = Seller
        fields = ['id', 'user', 'credit', 'created_at', 'updated_at']
        read_only_fields = ['credit']