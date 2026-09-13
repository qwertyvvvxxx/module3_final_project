from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent', 'slug', 'created_at')
    list_display_links = ('id', 'name')
    list_filter = ('parent', 'created_at')
    search_fields = ('name', 'slug')

    prepopulated_fields = {'slug': ('name',)}

    raw_id_fields = ('parent',)
    ordering = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'image_preview',
        'name',
        'category',
        'price',
        'stock',
        'is_active',
        'created_at'
    )
    list_display_links = ('id', 'name')

    list_editable = ('price', 'stock', 'is_active')

    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('name', 'description', 'slug')

    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('category',)
    readonly_fields = ('created_at', 'updated_at', 'image_preview')

    ordering = ('-created_at',)
    list_per_page = 20

    @admin.display(description='Фото')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "Немає фото"