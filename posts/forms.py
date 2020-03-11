from django import forms
from posts.models import Post, Comment


class PostForm(forms.ModelForm):
    """ form for adding a new post """
    class Meta:
        """ bind form to Post model and add fields 'text' and 'group' """
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст записи', 'group':'Сообщество', 'image': 'Картинка'}
        widgets = {'text': forms.Textarea()}


class CommentForm(forms.ModelForm):
    """ form for adding a comment to a post """
    class Meta:
        """ bind form to Comment model and add field 'text' """
        model = Comment
        fields = ('text',)
        labels = {'text': 'Комментарий',}
        widgets = {'text': forms.Textarea({'rows': 3})}