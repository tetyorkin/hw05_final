from django.contrib import admin

from .models import Post, Group


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author')
    list_filter = ('pub_date',)
    search_fields = ('text',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'description')
    list_filter = ('slug',)


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
