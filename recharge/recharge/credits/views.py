from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from .models import CreditRequest, Transaction
from .serializers import CreditRequestSerializer, AdminCreditRequestSerializer, TransactionSerializer
from accounts.permissions import IsSeller, IsAdminUser
from accounts.models import Seller
from django_filters.rest_framework import DjangoFilterBackend
import uuid
class CreditRequestViewSet(viewsets.ModelViewSet):

    serializer_class = CreditRequestSerializer
    queryset = CreditRequest.objects.all()

    def get_serializer_class(self):
        if self.request.user.is_admin_user:
            return AdminCreditRequestSerializer
        return CreditRequestSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            permission_classes = [IsSeller | IsAdminUser]
        elif self.action in ['update', 'partial_update', 'destroy', 'process']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return CreditRequest.objects.all().order_by('-created_at')
        elif hasattr(user, 'seller_profile'):
            return CreditRequest.objects.filter(seller=user.seller_profile).order_by('-created_at')
        return CreditRequest.objects.none()

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user.seller_profile)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def process(self, request, pk=None):
        credit_request = self.get_object()
        action_type = request.data.get('action', '').lower()

        if credit_request.status != 'pending':
            return Response(
                {"detail": f"This request has already been {credit_request.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if action_type not in ['approve', 'reject']:
            return Response(
                {"detail": "Action must be either 'approve' or 'reject'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # comment for sqlite
                # connection.cursor().execute("SET LOCAL statement_timeout = '5s'")


                credit_request = CreditRequest.objects.select_for_update().get(pk=credit_request.pk)


                if credit_request.status != 'pending':
                    return Response(
                        {"detail": f"This request has already been {credit_request.status} while processing."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                seller = Seller.objects.select_for_update().get(id=credit_request.seller.id)

                if action_type == 'approve':



                    previous_credit = seller.credit
                    new_credit = previous_credit + credit_request.amount


                    credit_request.status = 'approved'
                    credit_request.processed_at = timezone.now()
                    credit_request.save(update_fields=['status', 'processed_at'])


                    transaction_obj = Transaction.objects.create(

                        seller=seller,
                        amount=credit_request.amount,
                        transaction_type='credit_increase',
                        previous_credit=previous_credit,
                        new_credit=new_credit,
                        description=f"Credit increase from request {credit_request.reference_id}",
                        status='successful',
                        completed_at=timezone.now(),
                        content_type=ContentType.objects.get_for_model(CreditRequest),
                        object_id=credit_request.id
                    )


                    seller.credit = new_credit
                    seller.save(update_fields=['credit'])

                    return Response({
                        "detail": "Credit request approved successfully",
                        "transaction": TransactionSerializer(transaction_obj).data
                    })
                else:

                    credit_request.status = 'rejected'
                    credit_request.processed_at = timezone.now()
                    credit_request.save(update_fields=['status', 'processed_at'])

                    return Response({
                        "detail": "Credit request rejected"
                    })
        except CreditRequest.DoesNotExist:
            return Response(
                {"detail": "Credit request not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Seller.DoesNotExist:
            return Response(
                {"detail": "Seller not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"Error processing credit request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsSeller | IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'status']
    search_fields = ['description']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Transaction.objects.all()
        elif hasattr(user, 'seller_profile'):
            return Transaction.objects.filter(seller=user.seller_profile)
        return Transaction.objects.none()