from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser, Post, Subscription, SubscriptionPlan
from rest_framework.generics import CreateAPIView
from .serializers import CustomUserSerializer, PostSerializer, ProfileSerializer, CreatorSerializer, SubscriptionSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timezone, timedelta

stripe.api_key = settings.STRIPE_SECRET_KEY

# base views below
class FeedView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        subscriptions = Subscription.objects.filter(subscriber=request.user).values_list('creator', flat=True)
        posts = Post.objects.filter(author__in=subscriptions).order_by('-created')
        serializer = PostSerializer(posts, many=True, context={"request":request})
        return Response(serializer.data, status=status.HTTP_200_OK) 
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, username):
        profile = get_object_or_404(CustomUser, username=username)
        is_subscribed = Subscription.objects.filter(creator=profile, subscriber=request.user).exists()
        serializer = ProfileSerializer(profile, context={'is_subscribed': is_subscribed, 'my_page': profile.id == request.user.id, "request":request,}) 
        return Response({"profile":serializer.data, "my_page": profile.id == request.user.id, "is_subscribed": is_subscribed})
# stripe subscription plan registrationg below in post request
class CreatorView(APIView):
    # become a creator or update page
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        if not user.is_creator:
            return Response({"error":"You are not a creator!"}, status=status.HTTP_403_FORBIDDEN)
        serializer = CreatorSerializer(user)    
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        # create a subscription plan
        if SubscriptionPlan.objects.filter(creator=request.user).exists():
            return Response({"error":"You already have a subscription plan"}, status=400)
        price = request.data.get('price')
        if not price:
            return Response({"error": "Price is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            price = int(price)
        except ValueError:
            return Response({"error": "Price must be a number"}, status=status.HTTP_400_BAD_REQUEST)
        name = f'Subscription Plan for {request.user.username}'
        try:
            stripe_price = stripe.Price.create(
                unit_amount=int(price * 100),
                currency="usd",
                recurring={"interval": "month"},
                product_data={"name": name}
            )
            # create in the db
            subscription = SubscriptionPlan.objects.create(
                creator=request.user,
                price=price*100,
                stripe_price_id=stripe_price.id
            )
            user = request.user
            user.is_creator = True
            user.save()
            return Response({
                'message': 'Subscription plan created successfully',
                'subscription_id': subscription.stripe_price_id,
                'stripe_price_id': stripe_price.id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({"error":"Server Error"}, status=500)  

    def put(self, request, *args, **kwargs):
        serialiser = CreatorSerializer(data=request.data, instance=request.user, partial=True)
        if serialiser.is_valid():
            serialiser.save(is_creator=True)
        return Response(serialiser.data, status=status.HTTP_200_OK)

class PostCreateEditDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        post = get_object_or_404(Post, id=id)
        if request.user != post.author:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = PostSerializer(post, context={"request": request})
        return Response(serializer.data)
    def post(self, request):
        # create
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, id):
        # edit
        post = get_object_or_404(Post, id=id)
        if post.author != request.user:
            return Response({"error": "You do not have permission to edit this post."}, status=status.HTTP_403_FORBIDDEN)
        serializer = PostSerializer(instance=post, data=request.data, partial=True)    
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, id):
        post = get_object_or_404(Post, id=id)
        if request.user != post.author:
            return Response({"error": "You do not have permission to delete this post."}, status=status.HTTP_403_FORBIDDEN)
        post_title = post.title    
        post.delete()
        return Response({"message":f"Post '{post_title}' is deleted"}, status=status.HTTP_200_OK)
class PostLikeView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, id):
        post = get_object_or_404(Post, id=id)
        user = request.user
        if user in post.likes.all():
            # If the user already liked the post, remove their like (unlike)
            post.likes.remove(user)
            return Response({'message': 'Post unliked'}, status=200)
        else:
            # If the user hasn't liked the post, add their like
            post.likes.add(user)
            return Response({'message': 'Post liked'}, status=200)
        
class PostReportView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, id):
        post = get_object_or_404(Post, id=id)
        user = request.user
        if user not in post.reports.all():
            post.reports.add(user)
            return Response({'message':'Post reported'}, status=status.HTTP_200_OK)
        else:
            return Response({'error':'Post is already reported'}, status=status.HTTP_400_BAD_REQUEST)
        


class MakeSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        creator_username = request.data.get('username')
        if not creator_username:
            return Response({"error":"creator_username is missing"}, status=status.HTTP_400_BAD_REQUEST)
        creator = get_object_or_404(CustomUser, username=creator_username)
        if Subscription.objects.filter(creator=creator, subscriber=request.user).exists():
            return Response({"error":"You are already subscribed"}, status=status.HTTP_400_BAD_REQUEST)
        new_subscription = Subscription(creator=creator, subscriber=request.user)
        new_subscription.save()
        return Response(status=status.HTTP_201_CREATED)
class SubscriptionsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        subscriptions = user.subscriptions.all()
        serializer = SubscriptionSerializer(subscriptions, many=True)
        # print(user.subscriptions)
        return Response(serializer.data, status=status.HTTP_200_OK)

# authentication below 
class CreateUserView(APIView): 
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = CustomUserSerializer(data=request.data)      
        if serializer.is_valid():
            serializer.save()
            # or get token immediately  
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response({"error":"All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(username=username, password=password)
        if not user or not user.is_active:
            return Response({"error": "Invalid credentials or inactive account"}, status=status.HTTP_400_BAD_REQUEST)
        refresh = RefreshToken.for_user(user)
        expiration = datetime.now(timezone.utc) + timedelta(seconds=60*60*24*1)
        # res = {"refresh": str(refresh), "access": str(refresh.access_token)}
        response = Response({"response": "You're logged in!", "is_creator":user.is_creator, "user":user.username, "expiration": expiration}, status=status.HTTP_200_OK)
        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            httponly=True,  # Makes it only accessible via HTTP, not JavaScript
            secure=False,  # Set to True for production to ensure cookie is sent over HTTPS
            samesite='Lax',  # Helps prevent CSRF attacks
            max_age=60*60*24*1
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=60*60*24*60
            # max_age=20
        )
        return response
class LogoutView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        response = Response({"response": "You're logged out!"}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
class RefreshTokenView(APIView):
    permission_classes = [AllowAny] 
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        print(refresh_token)
        if not refresh_token:
            response = Response({"error":"Refresh token was not provided"}, status=status.HTTP_400_BAD_REQUEST)
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return response
        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
            expiration = datetime.now(timezone.utc) + timedelta(seconds=60*60*24*1)
            user_id = refresh.payload.get("user_id")
            user = CustomUser.objects.get(id=user_id)
            is_creator = user.is_creator  
            response = Response({"message":"Access token is updated", "is_creator": is_creator, "user": user.username, "expiration": expiration}, status=status.HTTP_200_OK)
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=60*60*24*1,
            )
            return response
        except Exception as e:
            print(e)
            response = Response({"error":"Refresh token is invalid"}, status=status.HTTP_400_BAD_REQUEST) 
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return response

class CheckAuthenticationView(APIView):
    # Checking if authenticated or not (for the front end to show pages)
    permission_classes = [AllowAny]
    def get(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        access_token = request.COOKIES.get('access_token')
        if not refresh_token:
            return Response({"is_authenticated": False, "is_creator": False, "user": ""}, status=status.HTTP_200_OK)
        if not access_token:    
            try:
                refresh = RefreshToken(refresh_token)
                print("successfully refreshed acces token")
                new_access_token = str(refresh.access_token)
                user_id = refresh.payload.get('user_id')
                user = CustomUser.objects.get(id=user_id)
                response = Response({"is_authenticated": True, "is_creator": user.is_creator, "user": user.username}, status=status.HTTP_200_OK)
                response.set_cookie(
                    key="access_token",
                    value=new_access_token,
                    httponly=True,
                    secure=False,
                    samesite='Lax',
                    max_age=60*60*24*1,
                )
                return response
            except (TokenError, CustomUser.DoesNotExist):
                response = Response({"is_authenticated": False, "is_creator": False, "user": ""}, status=status.HTTP_200_OK)
                response.delete_cookie("access_token")
                response.delete_cookie("refresh_token")
                return response
        try:
            access = AccessToken(access_token)
            user_id = access.payload.get('user_id')
            user = CustomUser.objects.get(id=user_id)
            return Response({"is_authenticated": True, "is_creator": user.is_creator, "user": user.username}, status=status.HTTP_200_OK)
        except (TokenError, CustomUser.DoesNotExist):
            return Response({"is_authenticated": False, "is_creator": False, "user": ""}, status=status.HTTP_200_OK)    
        


# stripe
class CheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]  

    def post(self, request):
        username = request.data.get("username")
        creator = get_object_or_404(CustomUser, username=username)
        user = request.user
        YOUR_DOMAIN = 'http://127.0.0.1:8000/api/'
        stripe_price_id = None
        if Subscription.objects.filter(creator=creator, subscriber=user).exists():
            return Response({"error":"You already subscribed"}, status=status.HTTP_400_BAD_REQUEST)
        if hasattr(creator, 'subscription_plan') and creator.subscription_plan:
            stripe_price_id = creator.subscription_plan.stripe_price_id
        else:
            return Response({"error":"No subscription plan for this user"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': stripe_price_id,
                        'quantity': 1,
                    },
                ],
                metadata={
                "creator": creator.username,
                "subscriber": user.username 
                },
                mode='subscription',
                success_url=YOUR_DOMAIN +
                f'success/',
                cancel_url=YOUR_DOMAIN + 'cancel/',
            )
            return Response({"checkout_url": checkout_session.url}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message":"Server error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)  

class SubscriptionCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        creator_username = request.data.get("creator_username")
        creator = get_object_or_404(CustomUser, username=creator_username)
        user = request.user
        subscription = Subscription.objects.filter(creator=creator, subscriber=user).first()
        if not subscription:
            return Response({"error":"No such subscription"}, status=status.HTTP_400_BAD_REQUEST)
        stripe.Subscription.cancel(subscription.stripe_subscription_id)    
        # subscription.is_active = False
        # subscription.save()
        return Response({"response":"Subscription was cancelled!"})    
        
# redirect after successful payment
def success(request):
    return render(request, "api/success.html")
# if any issue
def cancel(request):
    return render(request, "api/cancel.html")

# alter my database based on stripe 
@csrf_exempt
def stripe_webhook(request):
    print("WEBHOOK -----------------------------------------------------")
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    event_type = event['type']
    session = event['data']['object']
    metadata = session["metadata"]
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        # Access the metadata from the session
        creator_username = session['metadata']['creator']
        subscriber_username = session['metadata']['subscriber']
        # Retrieve Subscription ID from the session
        subscription_id = session.get('subscription') 
        print(subscription_id)
        # Process the metadata and other session information
        print(f"Creator: {creator_username}, Subscriber: {subscriber_username}")
        creator = get_object_or_404(CustomUser, username=creator_username)
        subscriber = get_object_or_404(CustomUser, username=subscriber_username)
        new_subscription = Subscription(creator=creator, subscriber=subscriber, stripe_subscription_id=subscription_id)
        new_subscription.save()
        print("Subscription was created!")
        return HttpResponse(status=201)
    elif event_type == 'customer.subscription.trial_will_end':
        # send email probably
        print('Subscription trial will end')
    elif event_type == 'customer.subscription.deleted':
        subscription_id = event['data']['object']['id']
        # Subscription.objects.filter(stripe_subscription_id=subscription_id).update(is_active=False)
        sub = get_object_or_404(Subscription, stripe_subscription_id=subscription_id)
        sub.delete()
        print("Subscription was deleted!")
        # return HttpResponse(status=200)
    return HttpResponse(status=200)