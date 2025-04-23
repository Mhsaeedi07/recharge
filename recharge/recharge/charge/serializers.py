from rest_framework import serializers
from .models import PhoneNumber, ChargeSale
from accounts.serializers import SellerSerializer


class PhoneNumberSerializer(serializers.ModelSerializer):


    class Meta:
        model = PhoneNumber
        fields = [
            'id',
            'number',
            'current_balance',
            'last_charge_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['current_balance', 'last_charge_date', 'created_at', 'updated_at']

    def validate_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        return value


class ChargeSaleSerializer(serializers.ModelSerializer):
    seller = SellerSerializer(read_only=True)
    phone_number = PhoneNumberSerializer(read_only=True)
    phone_number_id = serializers.PrimaryKeyRelatedField(
        queryset=PhoneNumber.objects.all(),
        write_only=True,
        source='phone_number'
    )

    class Meta:
        model = ChargeSale
        fields = [
            'id',
            'transaction_uuid',
            'seller',
            'phone_number',
            'phone_number_id',
            'amount',
            'phone_initial_balance',
            'phone_final_balance',
            'status',
            'status_message',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'seller', 'phone_initial_balance', 'phone_final_balance',
            'status', 'status_message', 'created_at', 'updated_at'
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Charge amount must be greater than zero")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError("Must be authenticated to create a charge sale")

        if not hasattr(request.user, 'seller_profile'):
            raise serializers.ValidationError("Only sellers can create phone charges")

        validated_data['seller'] = request.user.seller_profile

        return super().create(validated_data)