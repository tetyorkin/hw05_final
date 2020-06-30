from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


@cache_page(1 * 20)
def index(request):
    post_list = Post.objects.select_related('group').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:12]
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {
            'group': group,
            'posts': posts,
            'paginator': paginator,
            'page': page
        }
    )


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, 'new_post.html', {'form': form,
                                                 'msg': 'Новый пост'})
    form = PostForm()
    return render(request, 'new_post.html', {'form': form,
                                             'msg': 'Новый пост'})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get('page')
    count = paginator.count
    page = paginator.get_page(page_number)
    if request.user.is_authenticated:
        following = (
            Follow.objects.filter(
                user=request.user,
                author=User.objects.get(username=username)).all()
        )
    else:
        following = False
    context = {
        'page': page,
        'paginator': paginator,
        'author': author,
        'count': count,
        'following': following,
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.filter(post=post_id)
    form = CommentForm()
    context = {
        'author': author,
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'post.html', context)


@login_required()
def post_edit(request, username, post_id):
    user = request.user
    post = get_object_or_404(Post, id=post_id)
    if user != post.author:
        return redirect('post', username=username, post_id=post_id)
    form = (
        PostForm(
            request.POST or None, files=request.FILES or None, instance=post
        )
    )
    if form.is_valid():
        post.save()
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(instance=post)
    return render(request, 'new_post.html', {'form': form,
                                             'post': post,
                                             'msg': 'Редактирование поста'})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path}, status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required()
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('post', username=username, post_id=post_id)
    return redirect('post', username=post.author.username, post_id=post_id)


@login_required()
def follow_index(request):
    following = Follow.objects.filter(user=request.user).all()
    post_list = Post.objects.filter(author__following__in=following)
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'paginator': paginator,
    }
    return render(request, 'follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username)
