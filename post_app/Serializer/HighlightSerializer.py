from rest_framework import serializers
from post_app.models import HighlightModel,Story
from post_app.Serializer.StorySerializer import StorySerializer

class HighlightSerializer(serializers.ModelSerializer):
    stories = StorySerializer(many=True, read_only=True)
    story_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    cover_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = HighlightModel
        fields = ['id', 'title', 'cover_story','cover_image', 'stories', 'story_ids', 'created_at']
        read_only_fields = ['cover_image']
            

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data.pop('user', None)
        # story_ids = validated_data.pop('story_ids', [])
            
        highlight = HighlightModel.objects.create(user=user, **validated_data)
        # if story_ids:
        #     # highlight.stories.set(Story.objects.filter(id__in=story_ids, user=user))
        #     stories_qs = Story.objects.filter(id__in=story_ids, user=user)
        #     highlight.stories.set(stories_qs)
        return highlight

    # def update(self, instance, validated_data):
    #     story_ids = validated_data.pop('story_ids', None)
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)
    #     if story_ids is not None:
    #         stories_qs = Story.objects.filter(id__in=story_ids, user=instance.user)
    #         instance.stories.set(stories_qs)
    #         stories_qs.update(is_highlighted=True)
    #     instance.save()
    #     return instance


    def update(self, instance, validated_data):
        story_ids = validated_data.pop('story_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if story_ids is not None:
            # Combine current and new story IDs, avoid duplicates
            current_ids = set(instance.stories.values_list('id', flat=True))
            new_ids = set(story_ids)
            combined_ids = list(current_ids | new_ids)
            stories_qs = Story.objects.filter(id__in=combined_ids, user=instance.user)
            instance.stories.set(stories_qs)
            stories_qs.update(is_highlighted=True)
        instance.save()
        return instance