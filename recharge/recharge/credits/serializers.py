from rest_framework import serializers
from .models import CreditRequest, Transaction
from accounts.serializers import SellerSerializer

class CreditRequestSerializer(serializers.ModelSerializer):

    seller = SellerSerializer(read_only=True)

    class Meta:
        model = CreditRequest
        fields = [
            'id',
            'reference_id',
            'seller',
            'amount',
            'status',
            'created_at',
            'processed_at'
        ]
        read_only_fields = ['status', 'processed_at']

    def validate_amount(self, value):

        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError("Must be authenticated to create a credit request")

        if not hasattr(request.user, 'seller_profile'):
            raise serializers.ValidationError("Only sellers can request credit increases")

        validated_data['seller'] = request.user.seller_profile
        return super().create(validated_data)


class AdminCreditRequestSerializer(serializers.ModelSerializer):
    seller = SellerSerializer(read_only=True)

    class Meta:
        model = CreditRequest
        fields = [
            'id',
            'reference_id',
            'seller',
            'amount',
            'status',
            'created_at',
            'processed_at'
        ]
        read_only_fields = ['reference_id', 'seller', 'amount', 'created_at']

    def validate_status(self, value):
        instance = getattr(self, 'instance', None)

        if instance and instance.status != 'pending' and value != instance.status:
            raise serializers.ValidationError(
                f"Cannot change status from '{instance.status}' to '{value}'. "
                "Only pending requests can be updated."
            )

        return value


class TransactionSerializer(serializers.ModelSerializer):
    seller = SellerSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'seller',
            'amount',
            'transaction_type',
            'previous_credit',
            'new_credit',
            'description',
            'status',
            'created_at',
            'completed_at'
        ]
        read_only_fields = [
            'id', 'seller', 'previous_credit', 'new_credit',
            'status', 'created_at', 'completed_at'
        ]

    def validate_amount(self, value):
        if value == 0:
            raise serializers.ValidationError("Transaction amount cannot be zero")
        return value