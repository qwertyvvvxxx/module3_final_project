from django.contrib import admin
from django.db.models import QuerySet

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "stock", "is_active"]
    list_filter = ["is_active", "category"]
    list_editable = ["price", "stock", "is_active"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}
    actions = ["hide_products", "show_products"]

    @admin.action(description="Приховати обрані з каталогу")
    def hide_products(self, request, queryset: QuerySet[Product]) -> None:
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Приховано: {updated} товарів.")

    @admin.action(description="Показати обрані в каталозі")
    def show_products(self, request, queryset: QuerySet[Product]) -> None:
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Показано: {updated} товарів.")
