from django.contrib import admin
from django.db.models import QuerySet

from .models import Order, OrderItem
from .services import CheckoutError, cancel_order


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "payment_method", "total_price", "created_at"]
    list_filter = ["status", "payment_method", "delivery_type"]
    search_fields = ["id", "last_name", "first_name", "email", "phone"]
    inlines = [OrderItemInline]
    actions = ["mark_as_paid", "mark_as_shipped", "cancel_orders"]

    @admin.action(description="Позначити обрані як «Оплачено»")
    def mark_as_paid(self, request, queryset: QuerySet[Order]) -> None:
        updated = queryset.exclude(
            status__in=[Order.OrderStatus.SHIPPED, Order.OrderStatus.DELIVERED]
        ).update(status=Order.OrderStatus.PAID)
        self.message_user(request, f"Оплачено: {updated} замовлень.")

    @admin.action(description="Позначити обрані як «Відправлено»")
    def mark_as_shipped(self, request, queryset: QuerySet[Order]) -> None:
        updated = queryset.filter(status=Order.OrderStatus.PAID).update(
            status=Order.OrderStatus.SHIPPED
        )
        self.message_user(request, f"Відправлено: {updated} замовлень.")

    @admin.action(description="Скасувати обрані (повернути товар на склад)")
    def cancel_orders(self, request, queryset: QuerySet[Order]) -> None:
        cancelled = 0
        for order in queryset:
            try:
                cancel_order(order)
                cancelled += 1
            except CheckoutError as error:
                self.message_user(request, f"Замовлення №{order.pk}: {error}", level="error")
        self.message_user(request, f"Скасовано: {cancelled} замовлень.")
