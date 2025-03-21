from rest_framework import serializers
from .models import CustomUser
from .models import Post
from .models import Subscription
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'password', 'email')
        extra_kwargs = {'password':{'write_only': True},}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user 
    def update(self, instance, validated_data):
        
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  
        instance.save()
        return instance
 
class PostSerializer(serializers.ModelSerializer):
    likes = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_reported = serializers.SerializerMethodField()
    class Meta:
        model = Post
        fields = "__all__"
        extra_kwargs = {'author':{'read_only': True}, 'reports':{'read_only': True}}
    def get_likes(self, obj):
        return obj.likes.count()   
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.through.objects.filter(post_id=obj.id, customuser_id=request.user.id).exists()
        return False
    def get_is_reported(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reports.through.objects.filter(post_id=obj.id, customuser_id=request.user.id).exists()
        return False

class ProfileSerializer(serializers.ModelSerializer):
    posts = serializers.SerializerMethodField()
    posts_total = serializers.SerializerMethodField()
    posts_paid = serializers.SerializerMethodField()
    subscribers = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ('id','price','subscribers','is_creator','username', 'posts_total','posts_paid', 'posts', 'first_name', 'last_name', 'phone_number', 'profile_picture', 'about', 'background_picture', 'instagram', 'youtube')

    def get_posts(self, obj):
        is_subscribed = self.context.get('is_subscribed')
        # if is_subscribed or self.context.get('my_page'):
        #     posts = obj.posts.order_by('-created')
        # else:
        #     posts = obj.posts.filter(is_paid=False).order_by('-created')
        # return PostSerializer(posts, many=True, context={"request":self.context.get('request')}).data
        posts = obj.posts.order_by('-created')
        serialized_posts = PostSerializer(posts, many=True, context={"request":self.context.get('request')}).data
        if not is_subscribed and not self.context.get('my_page'):
            for post in serialized_posts:
                if post.get('is_paid'):  # Hide content for paid posts
                    post['body'] = None  # Hide body text
                    if post['image']:
                        post['image'] = 'hidden image'
                    else:
                        post['image'] = None  # Hide image (optional)
                    post['title'] = "Locked Content"  # Display lock indicator on frontend                       
        return serialized_posts       
    def get_posts_total(self, obj):
        return obj.posts.count()
    def get_posts_paid(self, obj):
        return obj.posts.filter(is_paid=True).count()
    def get_subscribers(self, obj):
        return obj.subscribers.count()
    def get_price(self, obj):
        if hasattr(obj, 'subscription_plan') and obj.subscription_plan:
            return obj.subscription_plan.price / 100  
        return 0   
class CreatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser      
        fields = ('id', 'first_name', 'last_name', 'phone_number', 'profile_picture', 'about', 'background_picture', 'instagram', 'youtube', 'username')   

class SubscriptionSerializer(serializers.ModelSerializer):
    creator = CreatorSerializer(read_only=True)
    class Meta:
        model = Subscription
        fields = ('id', 'creator', 'subscribed')
