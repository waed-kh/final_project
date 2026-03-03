from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Author, Book, Borrow, Review, Profile, Contact

# ================== لوحة تحكم Contact ==================
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject')
    list_per_page = 10

    def name(self, obj):
        return obj.name
    name.short_description = 'الاسم'

    def email(self, obj):
        return obj.email
    email.short_description = 'البريد الإلكتروني'

    def subject(self, obj):
        return obj.subject
    subject.short_description = 'الموضوع'

    def created_at(self, obj):
        return obj.created_at
    created_at.short_description = 'تاريخ الإنشاء'


# ================== لوحة تحكم Borrow ==================
@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'borrow_date', 'expected_return_date', 'return_date')
    list_filter = ('borrow_date', 'return_date')
    search_fields = ('student__username', 'book__title')
    list_per_page = 10

    def student(self, obj):
        return obj.student.username
    student.short_description = 'الطالب'

    def book(self, obj):
        return obj.book.title
    book.short_description = 'الكتاب'

    def borrow_date(self, obj):
        return obj.borrow_date
    borrow_date.short_description = 'تاريخ الاستعارة'

    def expected_return_date(self, obj):
        return obj.expected_return_date
    expected_return_date.short_description = 'تاريخ الإرجاع المتوقع'

    def return_date(self, obj):
        return obj.return_date
    return_date.short_description = 'تاريخ الإرجاع'


# ================== لوحة تحكم Review ==================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('student__username', 'book__title')
    list_per_page = 10

    def student(self, obj):
        return obj.student.username
    student.short_description = 'الطالب'

    def book(self, obj):
        return obj.book.title
    book.short_description = 'الكتاب'

    def rating(self, obj):
        return obj.rating
    rating.short_description = 'التقييم'

    def created_at(self, obj):
        return obj.created_at
    created_at.short_description = 'تاريخ التقييم'


# ================== لوحة تحكم Author ==================
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'num_books')
    search_fields = ('name',)
    list_per_page = 10

    def name(self, obj):
        return obj.name
    name.short_description = 'الاسم'

    def num_books(self, obj):
        return obj.book_set.count()
    num_books.short_description = 'عدد الكتب'


# ================== لوحة تحكم Book ==================
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_name', 'category_name', 'total_copies', 'available_copies', 'status', 'created_at')
    search_fields = ('title', 'author__name', 'category__name')
    list_filter = ('category', 'author', 'publication_year')
    list_per_page = 10

    def title(self, obj):
        return obj.title
    title.short_description = 'العنوان'

    def author_name(self, obj):
        return obj.author.name
    author_name.short_description = 'المؤلف'

    def category_name(self, obj):
        return obj.category.name
    category_name.short_description = 'التصنيف'

    def total_copies(self, obj):
        return obj.total_copies
    total_copies.short_description = 'عدد النسخ الكلي'

    def available_copies(self, obj):
        return obj.available_copies
    available_copies.short_description = 'عدد النسخ المتاحة'

    def status(self, obj):
        if obj.available_copies > 0:
            return format_html('<span style="color:green;">متاح</span>')
        return format_html('<span style="color:red;">مستعار</span>')
    status.short_description = 'حالة الكتاب'

    def created_at(self, obj):
        return obj.created_at
    created_at.short_description = 'تاريخ الإضافة'


# ================== لوحة تحكم Profile ==================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'phone')
    search_fields = ('user__username', 'phone')
    list_per_page = 10

    def user_name(self, obj):
        return obj.user.username
    user_name.short_description = 'اسم المستخدم'


# ================== لوحة تحكم Category ==================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_per_page = 10


# ================== تخصيص لوحة الإدارة ==================
admin.site.site_header = "نظام إدارة المكتبة"
admin.site.site_title = "لوحة إدارة المكتبة"
admin.site.index_title = "مرحبًا بك في لوحة تحكم المكتبة"