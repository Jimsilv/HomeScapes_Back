from django.urls import path
from .views import CreateTransactionView, UserTransactionHistoryView, RequestWithdrawalView

urlpatterns = [
    path("cash-in/", CreateTransactionView.as_view(), name="cash-in"),
    path("history/", UserTransactionHistoryView.as_view(), name="transaction-history"),
    path('withdraw/', RequestWithdrawalView.as_view(), name='request-withdrawal')

]
