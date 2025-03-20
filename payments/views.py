from rest_framework import status, generics, permissions, serializers
from rest_framework.response import Response
from django.db import transaction as db_transaction
from .models import Transaction
from django.db import models
from .serializers import TransactionSerializer, WithdrawalSerializer, UserSummarySerializer
from accounts.models import UserProfile  # Import UserProfile
from rest_framework.exceptions import ValidationError
from django.conf import settings
import paypalrestsdk
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

class CreateTransactionView(generics.CreateAPIView):
    """Handles user cash-in transactions, including PayPal integration."""
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        amount = request.data.get("amount")
        if not amount:
            return Response({"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Process PayPal Payment
        payment_success, approval_url = self.process_payment(amount, request.user.username)

        if not payment_success:
            return Response({"error": "Payment creation failed"}, status=status.HTTP_400_BAD_REQUEST)

        # Save transaction with pending status (no balance update yet)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, transaction_type="cash-in", status="pending")

        return Response({"approval_url": approval_url}, status=status.HTTP_201_CREATED)

    def process_payment(self, amount, username):
        """
        Integrates with PayPal to create a payment and return the approval URL.
        """
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET
        })

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": "http://localhost:8000/api/payments/paypal-success/",
                "cancel_url": "http://localhost:8000/api/payments/paypal-cancel/"
            },
            "transactions": [{
                "amount": {"total": str(amount), "currency": "USD"},
                "description": f"Cash-in for user {username}"
            }]
        })

        if payment.create():
            approval_url = next((link.href for link in payment.links if link.rel == "approval_url"), None)
            return bool(approval_url), approval_url
        return False, None


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

        if user.userprofile.balance < amount:
            raise serializers.ValidationError("Insufficient balance.")

        # Save withdrawal request with 'pending' status (DO NOT DEDUCT BALANCE HERE)
        transaction = serializer.save(user=user, transaction_type="withdrawal", status="pending")

        return Response({
            "message": "Withdrawal request submitted. Admin will review and process it.",
            "transaction_id": transaction.id
        })

class UserSummaryView(generics.RetrieveAPIView):
        """Provides a summary of the user's balance and transactions."""
        permission_classes = [permissions.IsAuthenticated]

        def get(self, request, *args, **kwargs):
            user = request.user
            transactions = Transaction.objects.filter(user=user)

            total_deposited = \
            transactions.filter(transaction_type="cash-in", status="completed").aggregate(total=models.Sum("amount"))[
                "total"] or 0
            total_withdrawn = transactions.filter(transaction_type="withdrawal", status="completed").aggregate(
                total=models.Sum("amount"))["total"] or 0
            recent_transactions = transactions.order_by("-created_at")[:5]  # Get last 5 transactions

            data = {
                "balance": user.profile.balance,
                "total_deposited": total_deposited,
                "total_withdrawn": total_withdrawn,
                "recent_transactions": UserSummarySerializer(recent_transactions, many=True).data
            }

            return Response(data)

class PayPalSuccessView(APIView):
    """Handles PayPal success callback and updates user balance."""
    permission_classes = [permissions.AllowAny]  # Allow any user (no authentication required)

    def get(self, request, *args, **kwargs):
        payment_id = request.query_params.get("paymentId")
        payer_id = request.query_params.get("PayerID")

        if not payment_id or not payer_id:
            return Response({"error": "Missing payment details"}, status=status.HTTP_400_BAD_REQUEST)

        # Configure PayPal SDK
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET
        })

        try:
            payment = paypalrestsdk.Payment.find(payment_id)
        except paypalrestsdk.ResourceNotFound:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        if payment.execute({"payer_id": payer_id}):
            amount = float(payment.transactions[0].amount.total)

            # Find the pending transaction for this payment
            try:
                transaction = Transaction.objects.filter(
                    payment_method="paypal",
                    status="pending"
                ).latest("created_at")  # Get the latest pending transaction

                user = transaction.user
                user.profile.balance += Decimal(str(amount))  # Update balance directly on the User model
                user.save()

                transaction.status = "completed"
                transaction.save()

                return Response({"message": "Payment successful, balance updated!"}, status=status.HTTP_200_OK)

            except Transaction.DoesNotExist:
                return Response({"error": "Transaction not found or already processed."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Payment execution failed"}, status=status.HTTP_400_BAD_REQUEST)

class PayPalCancelView(generics.GenericAPIView):
    """Handles PayPal payment cancellation."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Delete the pending transaction if payment was canceled
        Transaction.objects.filter(user=request.user, transaction_type="cash-in", status="pending").delete()
        return Response({"message": "Payment was canceled by the user, transaction removed."})