from django.contrib import admin

from .models import Post, Group


class PostAdmin(admin.ModelAdmin):
    """
    В классе PostAdmin перечисляем поля модели Post, которые необходимы для
    отображения в админке. Далее регистрируем его как источник кофигурации
    для модели Post. Необходимо унаследоваться от admin.ModelAdmin
    """
    list_display = ('pk', 'text', 'pub_date', 'author')
    list_filter = ('pub_date',)
    search_fields = ('text',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    """
    В классе GroupAdmin перечисляем поля модели Group, которые необходимы для
    отображения в админке. Далее регистрируем его как источник кофигурации
    для модели Group. Необходимо унаследоваться от admin.ModelAdmin
    """
    list_display = ('title', 'slug', 'description')
    list_filter = ('slug',)
    prepopulated_fields = {'slug': ('title',)}


# регистрация модели Post и Group и указываем их иточники конфигурации
admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
