from django.core.management.base import BaseCommand
from user_app.models import UserModel
from follower_app.models import Follower
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Debug follow relationships and status'

    def handle(self, *args, **options):
        self.stdout.write("=== DEBUGGING FOLLOW RELATIONSHIPS ===")
        
        # Get all users
        users = UserModel.objects.all()
        self.stdout.write(f"Total users: {users.count()}")
        
        # Get all follower relationships
        followers = Follower.objects.all()
        self.stdout.write(f"Total follower relationships: {followers.count()}")
        
        if followers.exists():
            self.stdout.write("\n=== ALL FOLLOWER RELATIONSHIPS ===")
            for f in followers:
                self.stdout.write(f"ID: {f.id} | {f.follower.username} -> {f.following.username} | Status: {f.status}")
        
        # Test with first two users if they exist
        if users.count() >= 2:
            user1 = users[0]
            user2 = users[1]
            
            self.stdout.write(f"\n=== TESTING WITH USERS ===")
            self.stdout.write(f"User 1: {user1.username} (ID: {user1.id})")
            self.stdout.write(f"User 2: {user2.username} (ID: {user2.id})")
            
            # Check if relationship exists
            relationship = Follower.objects.filter(follower=user1, following=user2).first()
            if relationship:
                self.stdout.write(f"Relationship found: {relationship}")
                self.stdout.write(f"Status: {relationship.status}")
                self.stdout.write(f"Status type: {type(relationship.status)}")
            else:
                self.stdout.write("No relationship found between these users")
                
                # Create a test relationship
                self.stdout.write("Creating a test relationship with 'pending' status...")
                test_rel = Follower.objects.create(
                    follower=user1,
                    following=user2,
                    status='pending'
                )
                self.stdout.write(f"Created: {test_rel} with status: {test_rel.status}")
                
                # Test the query again
                relationship = Follower.objects.filter(follower=user1, following=user2).first()
                if relationship:
                    self.stdout.write(f"After creation - Status: {relationship.status}")
                    
        self.stdout.write(self.style.SUCCESS("Debug completed")) 