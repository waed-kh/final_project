from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Avg, Q, OuterRef, Subquery

from .models import Book, Author, Category, Borrow, Review, Profile, Contact
from .forms import ProfileForm

# ================= HOME =================
def home(request):
    """عرض الصفحة الرئيسية مع أحدث الكتب وأعلى الكتب تقييماً"""
    latest_books = Book.objects.order_by('-created_at')[:6]
    top_books = Book.objects.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:3]

    context = {
        'latest_books': latest_books,
        'top_books': top_books,
        'books_count': Book.objects.count(),
        'authors_count': Author.objects.count(),
        'students_count': User.objects.count(),
    }
    return render(request, 'library/home.html', context)


# ================= ALL BOOKS =================
def all_books(request):
    """عرض جميع الكتب مع فلترة وفرز وباجينيتور"""
    active_borrow = Borrow.objects.filter(book=OuterRef('pk'), return_date__isnull=True).select_related('student')

    books = Book.objects.annotate(
        avg_rating=Avg('review__rating'),
        borrowed_by=Subquery(active_borrow.values('student__id')[:1])
    )

    query = request.GET.get('q')
    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__name__icontains=query))

    category = request.GET.get('category')
    if category:
        books = books.filter(category_id=category)

    sort = request.GET.get('sort')
    if sort == 'newest':
        books = books.order_by('-created_at')
    elif sort == 'oldest':
        books = books.order_by('created_at')
    elif sort == 'rated':
        books = books.order_by('-avg_rating')

    paginator = Paginator(books, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    borrowed_books_ids = []
    if request.user.is_authenticated:
        borrowed_books_ids = Borrow.objects.filter(student=request.user, return_date__isnull=True).values_list('book_id', flat=True)

    return render(request, 'library/books.html', {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'borrowed_books_ids': borrowed_books_ids,
    })


# ================= BOOK DETAILS =================
def chunk_reviews(reviews, n=3):
    """تقسم قائمة المراجعات إلى قوائم فرعية كل 3 مراجعات"""
    return [reviews[i:i+n] for i in range(0, len(reviews), n)]


def book_details(request, id):
    """عرض تفاصيل كتاب مع المراجعات وحالة الاستعارة"""
    book = get_object_or_404(Book, id=id)
    reviews = Review.objects.filter(book=book).order_by('-created_at')
    review_chunks = chunk_reviews(list(reviews), 3)

    is_borrowed_now = has_borrowed_before = has_reviewed = False

    if request.user.is_authenticated:
        is_borrowed_now = Borrow.objects.filter(student=request.user, book=book, return_date__isnull=True).exists()
        has_borrowed_before = Borrow.objects.filter(student=request.user, book=book).exists()
        has_reviewed = Review.objects.filter(student=request.user, book=book).exists()

    if not request.user.is_authenticated:
        book_status = "visitor"
    elif is_borrowed_now or (has_borrowed_before and not has_reviewed):
        book_status = "can_review"
    elif book.available_copies > 0:
        book_status = "can_borrow"
    else:
        book_status = "fully_borrowed"

    context = {
        "book": book,
        "reviews": reviews,
        "review_chunks": review_chunks,
        "book_status": book_status,
        "is_borrowed_now": is_borrowed_now,
        "has_reviewed": has_reviewed,
    }

    return render(request, "library/book_details.html", context)


# ================= BORROW BOOK =================
@login_required
def borrow_book(request, id):
    """استعارة كتاب إذا كان متاح ولم يتجاوز الحد الأقصى"""
    if request.method != "POST":
        return redirect('book_details', id=id)

    book = get_object_or_404(Book, id=id)

    if Borrow.objects.filter(student=request.user, return_date__isnull=True).count() >= 5:
        messages.error(request, "الحد الأقصى للاستعارة هو 5 كتب فقط.")
        return redirect('book_details', id=id)

    if book.available_copies <= 0 or Borrow.objects.filter(student=request.user, book=book, return_date__isnull=True).exists():
        return redirect('book_details', id=id)

    Borrow.objects.create(student=request.user, book=book, expected_return_date=timezone.now() + timedelta(days=14))
    book.available_copies -= 1
    book.save()

    return redirect('book_details', id=id)


# ================= RETURN BOOK =================
@login_required
def return_book(request, id):
    """إرجاع كتاب وزيادة النسخ المتوفرة"""
    borrow = get_object_or_404(Borrow, student=request.user, book_id=id, return_date__isnull=True)
    borrow.return_date = timezone.now().date()
    borrow.save()

    borrow.book.available_copies += 1
    borrow.book.save()

    messages.success(request, f'تم إرجاع الكتاب "{borrow.book.title}" بنجاح.')
    return redirect('my_books')


# ================= MY BOOKS =================
@login_required
def my_books(request):
    """عرض الكتب المستعارة حاليًا"""
    borrows = Borrow.objects.filter(student=request.user, return_date__isnull=True).select_related('book')
    today = timezone.now().date()

    for borrow in borrows:
        borrow.remaining_days = (borrow.expected_return_date - today).days
        borrow.is_late = borrow.remaining_days < 0

    return render(request, 'library/my_books.html', {'borrows': borrows})


# ================= ADD REVIEW =================
@login_required
def add_review_page(request, id):
    """إضافة مراجعة لكتاب إذا استعاره المستخدم"""
    book = get_object_or_404(Book, id=id)
    student = request.user

    already_reviewed = Review.objects.filter(book=book, student=student).exists()
    borrowed_before = Borrow.objects.filter(student=student, book=book).exists()

    review_errors = {}

    if request.method == 'POST':
        rating_str = request.POST.get('rating', '')
        comment = request.POST.get('comment', '').strip()

        try:
            rating = int(rating_str)
        except (ValueError, TypeError):
            rating = 0

        if already_reviewed:
            messages.warning(request, "لقد قمت بمراجعة هذا الكتاب مسبقًا.")
            return redirect('add_review_page', id=book.id)
        elif not borrowed_before:
            messages.error(request, "لا يمكنك مراجعة كتاب لم تستعره.")
            return redirect('add_review_page', id=book.id)
        elif rating > 0 and comment:
            Review.objects.create(book=book, student=student, rating=rating, comment=comment)
            messages.success(request, "تمت إضافة  التقييم بنجاح!")
            return redirect('add_review_page', id=book.id)
        else:
            if rating == 0: review_errors['rating'] = "الرجاء اختيار تقييم."
            if not comment: review_errors['comment'] = "الرجاء كتابة تعليق."

    reviews = book.review_set.all()
    review_chunks = chunk_reviews(list(reviews), 3)

    context = {
        'book': book,
        'reviews': reviews,
        'review_chunks': review_chunks,
        'review_errors': review_errors,
    }

    return render(request, 'library/add_review_page.html', context)


# ================= AUTHENTICATION =================
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('remember_me') == 'on'

        errors = {}  # قاموس لتخزين الأخطاء لكل حقل

        if not username:
            errors['username'] =  'Username is required'
        if not password:
            errors['password'] = 'Password is required'

        if errors:
            return render(request, 'library/login.html', {'errors': errors})

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if remember_me:
                request.session.set_expiry(1209600)  # أسبوعين
            else:
                request.session.set_expiry(0)
            next_url = request.GET.get('next')
            return redirect(next_url or 'home')
        else:
            errors['general'] = 'Invalid username or password '
            return render(request, 'library/login.html', {'errors': errors})

    return render(request, 'library/login.html')

def register(request):
    """تسجيل مستخدم جديد وإنشاء بروفايل"""
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        error = None

        if not full_name or not username or not email or not password or not password2:
                error = "Please fill in all required fields."
        elif password != password2:
            error = "Passwords do not match."
        elif len(password) < 8:
            error = "Password must be at least 8 characters long."
        elif User.objects.filter(username=username).exists():
            error = "Username already exists."
        elif User.objects.filter(email=email).exists():
            error = "Email already exists."
        else:
            try:
                validate_email(email)
            except ValidationError:
                error = "Enter a valid email address"

        if error:
            return render(request, "library/register.html", {
                "error": error,
                "full_name": full_name,
                "username": username,
                "email": email,
                "phone": phone
            })

        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = full_name
        user.save()
        Profile.objects.create(user=user, phone=phone)
        login(request, user)

        messages.success(request, "Account created successfully!")
        return redirect("home")

    return render(request, "library/register.html")


def user_logout(request):
    """تسجيل خروج المستخدم"""
    logout(request)
    next_url = request.GET.get('next', '/')
    return redirect(next_url)


# ================= PROFILE =================
@login_required
def profile(request):
    """صفحة البروفايل مع عدد الكتب المستعارة"""
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    context = {
        'user': user,
        'profile': profile,
        'currently_borrowed_count': Borrow.objects.filter(student=user, return_date__isnull=True).count(),
        'total_borrowed_count': Borrow.objects.filter(student=user).count(),
    }
    return render(request, 'library/profile.html', context)


@login_required
def edit_profile(request):
    """تعديل بيانات المستخدم والبروفايل"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    errors = {}

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()

        if not full_name: errors['full_name'] = "Full name is required."
        if not email: errors['email'] = "Email is required."
        elif '@' not in email: errors['email'] = "Enter a valid email."
        if not phone: errors['phone'] = "Phone number is required."
        if password and len(password) < 8: errors['password'] = "Password must be at least 8 characters."

        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid() and not errors:
            profile_form.save()
            request.user.first_name = full_name
            request.user.email = email
            if password:
                request.user.set_password(password)
                update_session_auth_hash(request, request.user)
            request.user.save()
            messages.success(request, "Profile updated successfully")
            return redirect('profile')

    else:
        profile_form = ProfileForm(instance=profile)

    context = {
        'profile_form': profile_form,
        'errors': errors,
        'data': {
            'full_name': request.POST.get('full_name', request.user.first_name) if request.method=='POST' else request.user.first_name,
            'email': request.POST.get('email', request.user.email) if request.method=='POST' else request.user.email,
            'phone': request.POST.get('phone', profile.phone if profile else '') if request.method=='POST' else profile.phone if profile else '',
            'password': '',
        }
    }
    return render(request, 'library/edit_profile.html', context)


# ================= CONTACT =================
def contact_view(request):
    """نموذج التواصل مع إدارة الموقع"""
    errors = {}
    data = {}

    if request.method == "POST":
        data['name'] = request.POST.get('name')
        data['email'] = request.POST.get('email')
        data['subject'] = request.POST.get('subject')
        data['message'] = request.POST.get('message')

        for field in ['name', 'email', 'subject', 'message']:
            if not data[field]:
                errors[field] = f"{field.capitalize()} is required"

        if not errors:
            Contact.objects.create(**data)
            messages.success(request, "Message sent successfully ✅")
            return redirect('contact')

    return render(request, 'library/contact.html', {'errors': errors, 'data': data})


# ================= CATEGORIES & AUTHORS =================
def categories(request):
    """عرض كل التصنيفات"""
    return render(request, 'library/categories.html', {'categories': Category.objects.all()})


def authors(request):
    """عرض كل المؤلفين"""
    return render(request, 'library/authors.html', {'authors': Author.objects.all()})


def books_by_category(request, cat_id):
    """عرض كتب تصنيف معين"""
    category = get_object_or_404(Category, id=cat_id)
    books = Book.objects.filter(category=category)
    return render(request, 'library/books_by_category.html', {'category': category, 'books': books})