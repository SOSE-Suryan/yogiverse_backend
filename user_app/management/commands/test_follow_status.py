from django.core.management.base import BaseCommand
from user_app.models import UserModel
from follower_app.models import Follower
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test follow status functionality'

    def handle(self, *args, **options):
        self.stdout.write("Testing follow status functionality...")
        
        # Get some users to test with
        users = UserModel.objects.all()[:3]
        
        if len(users) < 2:
            self.stdout.write(self.style.ERROR("Need at least 2 users to test"))
            return
            
        user1 = users[0]
        user2 = users[1]
        
        self.stdout.write(f"User 1: {user1.username} (ID: {user1.id})")
        self.stdout.write(f"User 2: {user2.username} (ID: {user2.id})")
        
        # Check existing relationships
        existing_follow = Follower.objects.filter(follower=user1, following=user2).first()
        if existing_follow:
            self.stdout.write(f"Existing follow relationship: {existing_follow.status}")
        else:
            self.stdout.write("No existing follow relationship")
            
        # Test the logic from the view
        following_relationship = Follower.objects.filter(
            follower=user1, 
            following=user2
        ).first()
        
        is_following = following_relationship is not None and following_relationship.status == 'approved'
        follow_status = following_relationship.status if following_relationship else None
        
        self.stdout.write(f"Following relationship: {following_relationship}")
        self.stdout.write(f"Is following: {is_following}")
        self.stdout.write(f"Follow status: {follow_status}")
        
        # Test counts
        followers_count = user2.followers.filter(status='approved').count()
        following_count = user2.following.filter(status='approved').count()
        
        self.stdout.write(f"User 2 followers count (approved): {followers_count}")
        self.stdout.write(f"User 2 following count (approved): {following_count}")
        
        self.stdout.write(self.style.SUCCESS("Test completed")) 