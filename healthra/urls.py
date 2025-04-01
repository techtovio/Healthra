from django.contrib import admin
from django.urls import path, include
from django.urls import path
from .views import register, login_form
from django.contrib.auth import views as auth_views
from .forms import PasswordChangeForm, PasswordResetForm, password_validation, SetPasswordForm
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('insurance.urls')),
    path('wallet/', include('wallet.urls')),
    path('accounts/register/', register, name='register'),
    path('accounts/login/', login_form, name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name="logout"),
    path('accounts/password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html', form_class=PasswordResetForm, success_url='/accounts/password-reset/done/'), name="password-reset"), # Passing Success URL to Override default URL, also created password_reset_email.html due to error from our app_name in URL
    path('accounts/password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name="password_reset_done"),
    path('accounts/password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html', form_class=SetPasswordForm, success_url='/accounts/password-reset-complete/'), name="password_reset_confirm"), # Passing Success URL to Override default URL
    path('accounts/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name="password_reset_complete"),
]

# To display images
#if settings.DEBUG:
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
