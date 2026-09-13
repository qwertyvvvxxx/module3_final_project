from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ('product',)
    readonly_fields = ('price',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at', 'updated_at')
    list_display_links = ('id', 'user')

    list_editable = ('status',)

    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('id', 'user__username', 'user__email', 'shipping_address')

    ordering = ('-created_at',)

    raw_id_fields = ('user',)

    inlines = [OrderItemInline]

    readonly_fields = ('created_at', 'updated_at')

    list_per_page = 20


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price')
    list_filter = ('order__status',)
    search_fields = ('order__id', 'product__name')
    raw_id_fields = ('order', 'product')