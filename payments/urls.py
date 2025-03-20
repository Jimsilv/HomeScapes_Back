from django.urls import path
from .views import  PayPalSuccessView, PayPalCancelView, CreateTransactionView, UserTransactionHistoryView, RequestWithdrawalView, UserSummaryView

urlpatterns = [
    path("cash-in/", CreateTransactionView.as_view(), name="cash-in"),
    path("history/", UserTransactionHistoryView.as_view(), name="transaction-history"),
    path('withdraw/', RequestWithdrawalView.as_view(), name='request-withdrawal'),
    path('transactions/',UserSummaryView.as_view(), name='transactions'),
    path("paypal-success/", PayPalSuccessView.as_view(), name="paypal-success"),
    path("paypal-cancel/", PayPalCancelView.as_view(), name="paypal-cancel"),
]
