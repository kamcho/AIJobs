from .models import UserNotification

def notification_count(request):
    if request.user.is_authenticated:
        return {
            'unread_notifications_count': UserNotification.objects.filter(user=request.user, is_read=False).count()
        }
    return {'unread_notifications_count': 0}
