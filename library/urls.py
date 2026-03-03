from django.urls import path
from . import views  # لازم يكون موجود

urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.all_books, name='all_books'),
    path('categories/', views.categories, name='categories'),
    path('authors/', views.authors, name='authors'),
    path('contact/', views.contact_view, name='contact'),
    path('category/<int:cat_id>/', views.books_by_category, name='books_by_category'),
    path('my-books/', views.my_books, name='my_books'),
    path('book/<int:id>/return/', views.return_book, name='return_book'),
    path('book/<int:id>/', views.book_details, name='book_details'),
    path('book/<int:id>/borrow/', views.borrow_book, name='borrow_book'),
    path('book/<int:id>/review/', views.add_review_page, name='add_review_page'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]