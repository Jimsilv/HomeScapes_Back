from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'amount', 'payment_method', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at', 'user']

    def validate_amount(self, value):
        """Ensure the amount is greater than zero."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'payment_method', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

    def validate_amount(self, value):
        """Ensure the amount is greater than zero and does not exceed the user's balance."""
        user_profile = self.context['request'].user.profile
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        if value > user_profile.balance:
            raise serializers.ValidationError("Insufficient balance.")
        return value

class UserSummarySerializer(serializers.ModelSerializer):
        """Serializer to return basic transaction details."""

        class Meta:
            model = Transaction
            fields = ['transaction_type', 'amount', 'status', 'created_at']