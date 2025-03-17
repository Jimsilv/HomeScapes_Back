from django.contrib import admin
from django.db import transaction as db_transaction
from .models import Transaction
from accounts.models import UserProfile  # Ensure UserProfile is imported

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'payment_method')
    search_fields = ('user__username', 'payment_method')

    actions = ['approve_withdrawals', 'reject_withdrawals']

    def approve_withdrawals(self, request, queryset):
        """Admin action to approve withdrawals."""
        for transaction in queryset.filter(transaction_type="withdrawal", status="pending"):
            user_profile = transaction.user.profile

            if user_profile.balance >= transaction.amount:
                user_profile.balance -= transaction.amount  # Deduct balance
                user_profile.save()

                transaction.status = "completed"
                transaction.save()
                self.message_user(request, f"✅ Approved withdrawal of {transaction.amount} for {transaction.user.username}.")
            else:
                self.message_user(request, f"❌ Insufficient balance for {transaction.user.username}.", level="error")

    def reject_withdrawals(self, request, queryset):
        """Admin action to reject withdrawals."""
        queryset.filter(transaction_type="withdrawal", status="pending").update(status="failed")
        self.message_user(request, "❌ Selected withdrawals have been rejected.")

    def save_model(self, request, obj, form, change):
        """
        Automatically deduct balance when the status is changed to 'completed' manually.
        """
        if change:  # Only trigger when updating an existing transaction
            old_instance = Transaction.objects.get(id=obj.id)
            if old_instance.status != "completed" and obj.status == "completed":
                user_profile = obj.user.profile
                if user_profile.balance >= obj.amount:
                    user_profile.balance -= obj.amount
                    user_profile.save()
                else:
                    self.message_user(request, f"❌ Insufficient balance for {obj.user.username}.", level="error")
                    return

        super().save_model(request, obj, form, change)

    approve_withdrawals.short_description = "✅ Approve selected withdrawals"
    reject_withdrawals.short_description = "❌ Reject selected withdrawals"

class PendingWithdrawalAdmin(admin.ModelAdmin):
    """Admin view for only pending withdrawal transactions."""
    list_display = ('user', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('payment_method',)
    search_fields = ('user__username', 'payment_method')

    def get_queryset(self, request):
        """Show only pending withdrawals."""
        return super().get_queryset(request).filter(transaction_type="withdrawal", status="pending")

admin.site.register(Transaction, TransactionAdmin)
