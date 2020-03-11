from django.contrib import admin

from .models import Post, Group, Comment


class PostAdmin(admin.ModelAdmin):
    """ Customise display of Posts in Django Admin """

    # display id, text, publication date, author and group
    list_display = ("pk", "text", "pub_date", "author", "related_group")
    # allow search by text
    search_fields = ("text",)
    # allow filter by publication date
    list_filter = ("pub_date",)
    # replace all empty values with "-пусто-"
    empty_value_display = "-пусто-"

    # change display text of group in Posts list view
    def related_group(self, obj):
        if not obj.group is None:
            # if posts belongs to a group, show it's id and title
            return "(id:{}) {}".format(obj.group.id, obj.group.title)
        else:
            # if post does not belong to any group, show "-пусто-"
            return self.empty_value_display
    # set column title = "group"
    related_group.short_description = "group"
    
    # Change display text in the Group dropdown when editing a Post 
    # Taken from https://stackoverflow.com/questions/6836740/django-admin-change-foreignkey-display-text
    def get_form(self, request, obj=None, **kwargs):
        form = super(PostAdmin, self).get_form(request, obj, **kwargs)
        # display group as "<id> <title>"
        form.base_fields['group'].label_from_instance = lambda obj: "{} {}".format(obj.id, obj.title)
        return form

class GroupAdmin(admin.ModelAdmin):
    """ Customise display of Groups in Django Admin """
    # display id, title, slug and description
    list_display = ("pk", "title", "slug", "description",)
    #allow search by title and slug
    search_fields = ("title", "slug")
    # prepopulate slug with title converted to URL-friendly format (all special characters removed, etc.)
    prepopulated_fields = {"slug": ("title",)}

class CommentAdmin(admin.ModelAdmin):
    """ customize display of comments in Django admin site """
    list_display = ('pk', 'text', 'created', 'author', 'post')

# register models
admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)