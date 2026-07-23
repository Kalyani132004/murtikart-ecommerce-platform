from django.db import models

#custom usermodel
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
        ('wholesaler', 'Wholesaler'),
    )
    profile_img = models.ImageField(upload_to='profile_images', null=True)
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    mobile2 = models.CharField(max_length=15, blank=True, null=True)
    mobile3 = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # for business profile
    business_name = models.CharField(max_length=100, blank=True, null=True)
    proprietor_name = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
#product model
class Product(models.Model):

    TYPE_CHOICES = (
        ('decorated', 'Decorated'),
        ('color', 'Color'),
    )

    VISIBILITY_CHOICES = (
        ('customer', 'Customer'),
        ('wholesaler', 'Wholesaler'),
        ('both', 'Both')
    )

    model_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    size = models.DecimalField(max_digits=5, decimal_places=2)  # in feet
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    image = models.ImageField(upload_to='products/')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Order(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_orders', null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    delivery_address = models.TextField(blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)
    
    date = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=20, default='pending')

    # this method helps to show the pending amount on admin panel
    @property
    def get_pending_amount(self):
        return self.total_amount - self.paid_amount
    
    @property
    def get_cart_total(self):
        #without dicount actual amt
        # if the OrderItem contains the product and qty with the gets the actual price
        return sum(item.product.price * item.quantity for item in self.items.all())

    @property
    def get_discount_savings(self):
        """gets the Gross Total - Saved Total"""
        gross = self.get_cart_total
        net = self.total_amount
        savings = float(gross) - float(net)
        return savings if savings > 0 else 0
    
    def save(self, *args, **kwargs):
        # payment status logic 
        if self.paid_amount >= self.total_amount:
            self.is_paid = True
            self.payment_status = 'fully_paid'
        elif self.paid_amount > 0:
            self.is_paid = False
            self.payment_status = 'partially_paid'
        else:
            self.is_paid = False
            self.payment_status = 'pending'
            
        super(Order, self).save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} - {self.user.full_name}"
    
#order item
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_item_price(self):
        # calculate the each ganpati bappa model total price (Rate * Qty)     
        return self.price * self.quantity
    
    #newly added fields
    def get_cart_total(self):
        # without discount actual price 
        return sum(item.price * item.quantity for item in self.items.all())

    def get_discount_amount(self):
        """fetch the total: (Gross Total - Saved Total)"""
        total_before_discount = self.get_cart_total()
        return total_before_discount - self.total_amount
    
    @property
    def disc_amt(self):
        #actual price  (Gross) - (Net)
        gross = sum(item.price * item.quantity for item in self.items.all())
        return gross - self.total_amount

    @property
    def get_cart_total(self):
        return sum(item.price * item.quantity for item in self.items.all())
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    
#payment
class Payment(models.Model):

    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.DecimalField(max_digits=10, decimal_places=2)
    pending = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Payment for Order {self.order.id}"
#discount    
class Discount(models.Model):

    tier_name = models.CharField(max_length=50)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.IntegerField()

    def __str__(self):
        return self.tier_name

#invoice
class Invoice(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    invoice_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.id}"