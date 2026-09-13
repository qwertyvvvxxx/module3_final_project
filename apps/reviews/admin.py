from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user', 'display_rating', 'created_at')

    list_display_links = ('id', 'product')

    list_filter = ('rating', 'created_at')

    search_fields = ('product__name', 'user__username', 'comment')

    ordering = ('-created_at',)

    raw_id_fields = ('product', 'user')

    list_per_page = 25

    @admin.display(description='Рейтинг', ordering='rating')
    def display_rating(self, obj):
        return "★" * obj.rating + "☆" * (5 - obj.rating)
