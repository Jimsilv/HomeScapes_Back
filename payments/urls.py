from django.urls import path
from .views import CreateTransactionView, UserTransactionHistoryView

urlpatterns = [
    path("cash-in/", CreateTransactionView.as_view(), name="cash-in"),
    path("history/", UserTransactionHistoryView.as_view(), name="transaction-history"),
]
