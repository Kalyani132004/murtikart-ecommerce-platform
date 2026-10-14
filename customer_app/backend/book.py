from decimal import Decimal
import json
import razorpay

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.db.models import Q
from django.conf import settings

from admin_app.models import Product, Order, OrderItem, Payment, Invoice, Discount
from admin_app.razorpay_client import get_razorpay_client
from murtikart_project.decorators import role_required


@role_required('customer')
@login_required
def check_validation(request):
    if request.method == "POST":
        product_id = request.POST.get('model_id')

        try:
            qty_val = request.POST.get('quantity', '0')
            adv_val = request.POST.get('advance_paid', '0')

            requested_qty = int(qty_val)
            advance_paid = int(adv_val)

            product = Product.objects.get(model_number=product_id)

            if requested_qty > product.stock:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Insufficient stock. Only {product.stock} items left.'
                })

            total_price = product.price * requested_qty

            if advance_paid > total_price:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Advance (₹{advance_paid}) cannot be more than the total price (₹{total_price}).'
                })

            if advance_paid < 500 and not product.price < 500:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please pay at least ₹500 as an advance.'
                })

            return JsonResponse({'status': 'success'})

        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': f'Product {product_id} not found in database.'})
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Value Error: {str(e)} | Qty received: {request.POST.get("quantity")} | Adv received: {request.POST.get("advance_paid")}'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'System error: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid Request Method'})


@role_required('customer')
@login_required
def book(request):
    book_id = request.GET.get('id')
    products = Product.objects.filter(visibility__in=['customer', 'both'])
    actual_model = get_object_or_404(Product, model_number=book_id) if book_id else None
    discounts = Discount.objects.all().order_by('min_price')

    if request.method == 'POST':
        selected_model_id = request.POST.get('model_id', book_id)
        payment_type = request.POST.get('payment_type', 'advance')

        try:
            quantity = int(request.POST.get('quantity', 1))
            advance_paid = Decimal(request.POST.get('advance_paid', 0) or '0')
            address = request.POST.get('address')
            delivery_date = request.POST.get('delivery_date')

            product = Product.objects.get(model_number=selected_model_id)

            # --- server-side stock check, don't rely on the separate validation endpoint alone ---
            if quantity > product.stock:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Insufficient stock. Only {product.stock} items left.'
                }, status=400)

            subtotal = product.price * Decimal(quantity)

            discount_tier = Discount.objects.filter(
                min_price__lte=subtotal
            ).filter(
                Q(max_price__gte=subtotal) | Q(max_price__isnull=True)
            ).order_by('-discount_percent').first()

            discount_amount = Decimal('0.00')
            if discount_tier:
                discount_amount = (subtotal * Decimal(discount_tier.discount_percent)) / Decimal('100')

            final_total = subtotal - discount_amount
            amount_to_pay = final_total if payment_type == 'full' else advance_paid

            # --- server-side advance validation ---
            if payment_type == 'advance':
                if advance_paid > final_total:
                    return JsonResponse({'status': 'error', 'message': 'Advance cannot exceed total price.'}, status=400)
                if advance_paid < 500 and final_total >= 500:
                    return JsonResponse({'status': 'error', 'message': 'Please pay at least ₹500 as an advance.'}, status=400)

            order = Order.objects.create(
                user=request.user,
                total_amount=final_total,
                paid_amount=0,
                status='pending',   # fixed — was 'pending_payment', not a valid choice
                delivery_address=address,
                delivery_date=delivery_date if delivery_date else None
            )

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

            payment = Payment.objects.create(
                order=order,
                total_amount=final_total,
                paid=0,
                pending=final_total,
                payment_type=payment_type,
                payment_status='created'
            )

            Invoice.objects.create(order=order, user=request.user)

            client = get_razorpay_client()
            razorpay_order = client.order.create({
                'amount': int(amount_to_pay * 100),
                'currency': 'INR',
                'receipt': f'order_rcptid_{order.id}',
                'payment_capture': 1
            })

            payment.razorpay_order_id = razorpay_order['id']
            payment.save()

            return JsonResponse({
                'status': 'success',
                'razorpay_order_id': razorpay_order['id'],
                'amount': int(amount_to_pay * 100),
                'currency': 'INR',
                'key_id': settings.RAZORPAY_KEY_ID,
                'order_id': order.id,
                'payment_id': payment.id,
                'name': request.user.full_name,
                'email': request.user.email,
                'contact': getattr(request.user, 'mobile', ''),
            })

        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    products_list = [{'id': p.model_number, 'name': p.name, 'price': float(p.price)} for p in products]
    discounts_list = [
        {
            'min_price': float(d.min_price),
            'max_price': float(d.max_price) if d.max_price else 9999999,
            'discount_percent': d.discount_percent
        } for d in discounts
    ]

    return render(request, 'customer/book.html', {
        'products': products,
        'actual_model': actual_model,
        'products_list': products_list,
        'discounts_json': json.dumps(discounts_list),
    })


@role_required('customer')
@login_required
def verify_payment(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

    data = json.loads(request.body)
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    client = get_razorpay_client()

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })

        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        order = payment.order

        if order.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

        rzp_payment = client.payment.fetch(razorpay_payment_id)
        amount_paid = Decimal(rzp_payment['amount']) / 100

        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.paid = amount_paid
        payment.pending = payment.total_amount - amount_paid
        payment.payment_status = 'paid'
        payment.save()

        order.paid_amount = amount_paid
        order.status = 'confirmed' if payment.pending <= 0 else 'pending'
        order.save()

        # fixed — was order.orderitem_set.first(), correct related_name is 'items'
        for item in order.items.all():
            item.product.stock -= item.quantity
            item.product.save()

        return JsonResponse({'status': 'success', 'redirect_url': reverse('customer:bookings')})

    except razorpay.errors.SignatureVerificationError:
        payment = Payment.objects.filter(razorpay_order_id=razorpay_order_id).first()
        if payment:
            payment.payment_status = 'failed'
            payment.save()
        return JsonResponse({'status': 'error', 'message': 'Payment verification failed.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)