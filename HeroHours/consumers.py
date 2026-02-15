from djangochannelsrestframework.decorators import action
from djangochannelsrestframework.observer import model_observer
from djangochannelsrestframework.observer.generics import ObserverModelInstanceMixin
from djangochannelsrestframework.permissions import IsAuthenticated
from rest_framework import serializers

from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.mixins import (
    ListModelMixin, RetrieveModelMixin,
)
from django.db.models.expressions import BaseExpression

from .models import Users


class MemberSerializer(serializers.ModelSerializer):
    """Serializer for Users model used in WebSocket communications."""
    class Meta:
        model = Users
        fields = ['User_ID', 'First_Name', 'Last_Name', 'Checked_In', 'Total_Seconds', 'Last_In', 'Last_Out']


class LiveConsumer(ObserverModelInstanceMixin, RetrieveModelMixin, ListModelMixin, GenericAsyncAPIConsumer):
    """
    WebSocket consumer for real-time member updates.
    
    Provides live updates when members check in/out via the update_activity observer.
    Requires authentication to connect.
    """
    queryset = Users.objects.all().order_by('Last_Name','First_Name')
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    @model_observer(Users)
    async def update_activity(
            self,
            message: MemberSerializer,
            observer=None,
            subscribing_request_ids=[],
            **kwargs
    ):
        """
        Observer that sends updates when Users model changes.
        
        Args:
            message: Serialized user data
            observer: Observer instance
            subscribing_request_ids: List of request IDs subscribed to updates
        """
        await self.send_json({'data':message.data, 'request_ids':subscribing_request_ids})

    @update_activity.serializer
    def update_activity(self, instance: Users, action, **kwargs) -> MemberSerializer:
        """
        Serializer for the update_activity observer.
        
        Refreshes instance from database if any field contains F() expressions
        to ensure accurate data is sent to subscribers.
        
        Args:
            instance: Users model instance that changed
            action: Type of change (create, update, delete)
            
        Returns:
            MemberSerializer: Serialized user data
        """
        for field in instance._meta.fields:
            if isinstance(getattr(instance, field.name), BaseExpression):
                instance.refresh_from_db()
                break
        return MemberSerializer(instance)

    @action()
    async def subscribe_all(self, request_id, **kwargs):
        """
        Action to subscribe to all Users model updates.
        
        Args:
            request_id: Unique request identifier for this subscription
        """
        await self.update_activity.subscribe(request_id=request_id)