from django.contrib.auth.models import User
from django.db import models
from expense.models import Expense


# Create your models here.
class Category(models.Model):
    user = models.ForeignKey(User, related_name="categories", on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    date = models.DateField(auto_now=True)

    def __str__(self) -> str:
        return self.name

    @property
    def total_expense_cost(self):
        expenses = Expense.objects.all().filter(category=self.id)
        return sum([expense.amount for expense in expenses])