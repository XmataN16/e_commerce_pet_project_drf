from django.db import models
from django.conf import settings
from catalog.models import Product

User = settings.AUTH_USER_MODEL

class Order(models.Model):
    STATUS_CHOICES = (("new", "New"), ("paid", "Paid"), ("shipped", "Shipped"), ("cancelled", "Cancelled"))
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
