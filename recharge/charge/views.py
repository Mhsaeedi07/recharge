from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from .models import PhoneNumber, ChargeSale
from .serializers import PhoneNumberSerializer, ChargeSaleSerializer
from credits.models import Transaction
from accounts.permissions import IsSeller, IsAdminUser
from accounts.models import Seller
import uuid
class PhoneNumberViewSet(viewsets.ModelViewSet):

    queryset = PhoneNumber.objects.all()
    serializer_class = PhoneNumberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class ChargeSaleViewSet(viewsets.ModelViewSet):
    serializer_class = ChargeSaleSerializer
    permission_classes = [IsSeller | IsAdminUser]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return ChargeSale.objects.all().order_by('-created_at')
        elif hasattr(user, 'seller_profile'):
            return ChargeSale.objects.filter(seller=user.seller_profile).order_by('-created_at')
        return ChargeSale.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number_id = serializer.validated_data.get('phone_number').id
        amount = serializer.validated_data.get('amount')
        transaction_uuid = serializer.validated_data.get('transaction_uuid')

        seller = request.user.seller_profile


        if ChargeSale.objects.filter(transaction_uuid=transaction_uuid).exists():
            return Response(
                {"detail": "Transaction with this UUID already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # comment for sqlite
                # connection.cursor().execute("SET LOCAL statement_timeout = '5s'")


                phone_number = PhoneNumber.objects.select_for_update().get(id=phone_number_id)
                seller = Seller.objects.select_for_update().get(id=seller.id)


                if ChargeSale.objects.filter(transaction_uuid=transaction_uuid).exists():
                    return Response(
                        {"detail": "Transaction with this UUID already exists (concurrent)."},
                        status=status.HTTP_400_BAD_REQUEST
                    )


                if seller.credit < amount:
                    return Response(
                        {"detail": "Insufficient credit for this transaction."},
                        status=status.HTTP_400_BAD_REQUEST
                    )


                previous_seller_credit = seller.credit
                phone_initial_balance = phone_number.current_balance


                new_seller_credit = previous_seller_credit - amount
                phone_final_balance = phone_initial_balance + amount


                charge_sale = ChargeSale.objects.create(
                    transaction_uuid=transaction_uuid,
                    seller=seller,
                    phone_number=phone_number,
                    amount=amount,
                    phone_initial_balance=phone_initial_balance,
                    phone_final_balance=phone_final_balance,
                    status='successful',
                    created_at=timezone.now()
                )


                idempotency_key = f"charge_sale_{transaction_uuid}_{uuid.uuid4()}"

                transaction_obj = Transaction.objects.create(
                    idempotency_key=idempotency_key,
                    seller=seller,
                    amount=-amount,
                    transaction_type='charge_sale',
                    previous_credit=previous_seller_credit,
                    new_credit=new_seller_credit,
                    description=f"Charge sale for phone {phone_number.number}",
                    status='successful',
                    completed_at=timezone.now(),
                    content_type=ContentType.objects.get_for_model(ChargeSale),
                    object_id=charge_sale.id
                )


                seller.credit = new_seller_credit
                seller.save(update_fields=['credit'])

                phone_number.current_balance = phone_final_balance
                phone_number.last_charge_date = timezone.now()
                phone_number.save(update_fields=['current_balance', 'last_charge_date'])

                return Response(
                    self.get_serializer(charge_sale).data,
                    status=status.HTTP_201_CREATED
                )

        except PhoneNumber.DoesNotExist:
            return Response(
                {"detail": "Phone number not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Seller.DoesNotExist:
            return Response(
                {"detail": "Seller profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"Error processing charge: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )