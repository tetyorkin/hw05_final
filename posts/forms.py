from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm, Textarea
from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        labels = {
            'group': _('Группа'),
            'text': _('Текст'),
            'image': _('Картинка'),
        }
        help_texts = {
            'group': _('Выберите группу'),
            'text': _('Напишите здесь текст поста'),
        }
        widgets = {
            'text': Textarea(attrs={'cols': 80, 'rows': 20})
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text', ]
        widgets = {
            'text': Textarea()
        }
