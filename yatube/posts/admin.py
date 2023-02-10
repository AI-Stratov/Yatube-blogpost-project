from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "text",
        "pub_date",
        "author",
        "group",
    )
    list_editable = ("group",)
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "title",
        "slug",
        "description"
    )
    search_fields = ("title",)
    list_filter = ("title",)


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "author",
        "text",
        "pub_date",
    )
    search_fields = (
        'author',
        'text',
    )


class FollowAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "author",
    )
    search_fields = (
        "user",
        "author",
    )


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
