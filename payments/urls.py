from django.urls import path
from .views import CreateTransactionView, UserTransactionHistoryView, RequestWithdrawalView, UserSummaryView

urlpatterns = [
    path("cash-in/", CreateTransactionView.as_view(), name="cash-in"),
    path("history/", UserTransactionHistoryView.as_view(), name="transaction-history"),
    path('withdraw/', RequestWithdrawalView.as_view(), name='request-withdrawal'),
    path('transactions/',UserSummaryView.as_view(), name='transactions')
]
