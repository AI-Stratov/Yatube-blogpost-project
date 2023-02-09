from django.core.paginator import Paginator


def paginate_posts(request, posts, posts_per_page):
    paginator = Paginator(posts, posts_per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj
