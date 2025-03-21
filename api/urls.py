from django.urls import path, include
from . import views
urlpatterns = [
    path('feed/', views.FeedView.as_view()),
    path('user/profile/<str:username>/', views.ProfileView.as_view()),
    path('post/get/<int:id>/', views.PostCreateEditDeleteView.as_view()),
    path('post/create/', views.PostCreateEditDeleteView.as_view()),
    path('post/edit/<int:id>/', views.PostCreateEditDeleteView.as_view()),
    path('post/delete/<int:id>/', views.PostCreateEditDeleteView.as_view()),
    path('post/like/<int:id>/', views.PostLikeView.as_view()),
    path('post/report/<int:id>/', views.PostReportView.as_view()),
    path('user/creator/', views.CreatorView.as_view()),
    # old subscribe without stripe
    path('subscribe/', views.MakeSubscriptionView.as_view()),
    path('subscriptions/', views.SubscriptionsView.as_view()),
    path('subscribe_stripe/', views.CheckoutSessionView.as_view()),
    path('subscription/cancel/', views.SubscriptionCancelView.as_view()),
    path('success/', views.success),
    path('cancel/', views.cancel),
    path('webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
]


