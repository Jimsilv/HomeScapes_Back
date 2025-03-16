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
