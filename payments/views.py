from rest_framework import generics, permissions
from rest_framework.response import Response
from django.db import transaction as db_transaction
from .models import Transaction
from .serializers import TransactionSerializer, WithdrawalSerializer
from accounts.models import UserProfile  # Import UserProfile
from rest_framework.exceptions import ValidationError

class CreateTransactionView(generics.CreateAPIView):
    """Handles user cash-in transactions."""
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user_profile, created = UserProfile.objects.get_or_create(user=self.request.user)  # Ensure user has profile
        amount = serializer.validated_data['amount']

        # Simulating an external payment process
        payment_success = self.process_payment(user_profile, amount)

        if payment_success:
            with db_transaction.atomic():
                user_profile.balance += amount
                user_profile.save()
                transaction = serializer.save(user=self.request.user, status="completed")

            return Response({"message": "Transaction successful!", "transaction_id": transaction.id})
        else:
            return Response({"error": "Payment failed."}, status=400)

    def process_payment(self, user_profile, amount):
        """
        Simulated payment gateway integration.
        Replace this with actual API calls to PayPal, GCash, or any other service.
        """
        return True  # Simulating a successful payment


class UserTransactionHistoryView(generics.ListAPIView):
    """Retrieves the transaction history of the logged-in user."""
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-created_at')

class RequestWithdrawalView(generics.CreateAPIView):
    """Handles user withdrawal requests (manual processing)."""
    serializer_class = WithdrawalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        amount = serializer.validated_data['amount']

        if user.profile.balance < amount:
            raise ValidationError("Insufficient balance.")

        # Process withdrawal
        with db_transaction.atomic():
            user.profile.balance -= amount
            user.profile.save()
            serializer.save(user=user, transaction_type="withdrawal", status="pending")