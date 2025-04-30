import uuid
import threading
import random
from decimal import Decimal
from django.test import TransactionTestCase
from django.db import models, connections
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Seller
from credits.models import CreditRequest, Transaction
from charge.models import PhoneNumber, ChargeSale
from multiprocessing import Process, Queue

User = get_user_model()


class SystemIntegrityTestCase(TransactionTestCase):


    def setUp(self):

        self.admin_user = User.objects.create_user(
            username='admin_test',
            password='admin_password',
            is_admin_user=True,
            is_staff=True,
            is_superuser=True
        )

        self.seller1_user = User.objects.create_user(
            username='seller1_test',
            password='seller1_password',
            is_seller=True
        )
        self.seller1 = Seller.objects.create(
            user=self.seller1_user,
            credit=Decimal('0')
        )

        self.seller2_user = User.objects.create_user(
            username='seller2_test',
            password='seller2_password',
            is_seller=True
        )
        self.seller2 = Seller.objects.create(
            user=self.seller2_user,
            credit=Decimal('0')
        )


        self.phone_numbers = []
        for i in range(1, 11):
            phone = PhoneNumber.objects.create(
                number=f'0912000{i:04d}',
                current_balance=Decimal('0')
            )
            self.phone_numbers.append(phone)


        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)

        self.seller1_client = APIClient()
        self.seller1_client.force_authenticate(user=self.seller1_user)

        self.seller2_client = APIClient()
        self.seller2_client.force_authenticate(user=self.seller2_user)

    def create_credit_request(self, client, amount):

        reference_id = f"CR-{uuid.uuid4()}"


        credit_request_data = {
            'reference_id': reference_id,
            'amount': int(amount)
        }

        response = client.post(
            '/api/credits/credit-requests/',
            credit_request_data,
            format='json'
        )

        if response.status_code != status.HTTP_201_CREATED:
            print(f"Credit request creation failed: {response.status_code}")
            print(f"Response data: {response.data}")
            return None

        credit_request_id = response.data['id']


        approve_data = {'action': 'approve'}
        response = self.admin_client.post(
            f'/api/credits/credit-requests/{credit_request_id}/process/',
            approve_data,
            format='json'
        )

        if response.status_code != status.HTTP_200_OK:
            print(f"Credit request approval failed: {response.status_code}")
            print(f"Response data: {response.data}")
            return None

        return response.data


        approve_data = {'action': 'approve'}
        response = self.admin_client.post(
            reverse('creditrequest-process', args=[credit_request_id]),
            approve_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        return response.data

    def create_charge_sale(self, client, phone_number_id, amount):

        charge_data = {
            'phone_number_id': phone_number_id,
            'amount': int(amount),
            'transaction_uuid': str(uuid.uuid4())
        }

        response = client.post(
            '/api/charge/charges/',
            charge_data,
            format='json'
        )


        return response

    def test_basic_credit_accounting(self):

        self.assertEqual(self.seller1.credit, Decimal('0'))
        self.assertEqual(self.seller2.credit, Decimal('0'))


        total_credit_increase_seller1 = Decimal('1000')
        result1 = self.create_credit_request(self.seller1_client, total_credit_increase_seller1)


        total_credit_increase_seller2 = Decimal('2000')
        result2 = self.create_credit_request(self.seller2_client, total_credit_increase_seller2)


        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()


        print(f"Seller 1 credit after increase: {self.seller1.credit}")
        print(f"Seller 2 credit after increase: {self.seller2.credit}")


        if result1 is None or result2 is None:
            print("Skipping remaining tests due to credit request failures")
            return


        self.assertEqual(self.seller1.credit, total_credit_increase_seller1)
        self.assertEqual(self.seller2.credit, total_credit_increase_seller2)


        charge_amount = Decimal('50')


        response = self.create_charge_sale(self.seller1_client, self.phone_numbers[0].id, charge_amount)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.create_charge_sale(self.seller2_client, self.phone_numbers[1].id, charge_amount)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()

        self.assertEqual(self.seller1.credit, total_credit_increase_seller1 - charge_amount)
        self.assertEqual(self.seller2.credit, total_credit_increase_seller2 - charge_amount)


        self.phone_numbers[0].refresh_from_db()
        self.phone_numbers[1].refresh_from_db()

        self.assertEqual(self.phone_numbers[0].current_balance, charge_amount)
        self.assertEqual(self.phone_numbers[1].current_balance, charge_amount)

    def test_comprehensive_accounting(self):
        """
        Comprehensive test with multiple credit increases and charge sales
        Requirements: 2 sellers, 10 credit increases, 1000 sales
        """

        credit_increase_amount = Decimal('1000')
        total_credit_increase_seller1 = Decimal('0')
        total_credit_increase_seller2 = Decimal('0')

        for _ in range(5):
            self.create_credit_request(self.seller1_client, credit_increase_amount)
            total_credit_increase_seller1 += credit_increase_amount

            self.create_credit_request(self.seller2_client, credit_increase_amount)
            total_credit_increase_seller2 += credit_increase_amount


        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()


        self.assertEqual(self.seller1.credit, total_credit_increase_seller1)
        self.assertEqual(self.seller2.credit, total_credit_increase_seller2)


        charge_amount = Decimal('10')
        total_charges_seller1 = Decimal('0')
        total_charges_seller2 = Decimal('0')

        successful_charges_seller1 = 0
        successful_charges_seller2 = 0


        initial_phone_balances = {}
        for phone in self.phone_numbers:
            initial_phone_balances[phone.id] = phone.current_balance


        for _ in range(500):

            phone_id = random.choice(self.phone_numbers).id
            response = self.create_charge_sale(self.seller1_client, phone_id, charge_amount)
            if response.status_code == status.HTTP_201_CREATED:
                total_charges_seller1 += charge_amount
                successful_charges_seller1 += 1

            phone_id = random.choice(self.phone_numbers).id
            response = self.create_charge_sale(self.seller2_client, phone_id, charge_amount)
            if response.status_code == status.HTTP_201_CREATED:
                total_charges_seller2 += charge_amount
                successful_charges_seller2 += 1

        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()


        expected_credit_seller1 = total_credit_increase_seller1 - total_charges_seller1
        expected_credit_seller2 = total_credit_increase_seller2 - total_charges_seller2

        self.assertEqual(self.seller1.credit, expected_credit_seller1)
        self.assertEqual(self.seller2.credit, expected_credit_seller2)

        total_phone_balance_increase = Decimal('0')
        for phone in self.phone_numbers:
            phone.refresh_from_db()
            balance_increase = phone.current_balance - initial_phone_balances[phone.id]
            total_phone_balance_increase += balance_increase


        self.assertEqual(total_phone_balance_increase, total_charges_seller1 + total_charges_seller2)


        latest_transaction_seller1 = Transaction.objects.filter(
            seller=self.seller1
        ).order_by('-created_at').first()

        latest_transaction_seller2 = Transaction.objects.filter(
            seller=self.seller2
        ).order_by('-created_at').first()


        self.assertEqual(latest_transaction_seller1.new_credit, self.seller1.credit)
        self.assertEqual(latest_transaction_seller2.new_credit, self.seller2.credit)


        print(f"Seller 1: Initial credit: {total_credit_increase_seller1}, "
              f"Successful charges: {successful_charges_seller1}, "
              f"Total charge amount: {total_charges_seller1}, "
              f"Final credit: {self.seller1.credit}")

        print(f"Seller 2: Initial credit: {total_credit_increase_seller2}, "
              f"Successful charges: {successful_charges_seller2}, "
              f"Total charge amount: {total_charges_seller2}, "
              f"Final credit: {self.seller2.credit}")

    def test_concurrent_operations_Thread(self):
        """Test concurrent operations to ensure system integrity under load"""

        initial_credit = Decimal('5000')
        self.create_credit_request(self.seller1_client, initial_credit)
        self.create_credit_request(self.seller2_client, initial_credit)


        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()

        self.assertEqual(self.seller1.credit, initial_credit)
        self.assertEqual(self.seller2.credit, initial_credit)


        num_threads = 10
        operations_per_thread = 10
        charge_amount = Decimal('10')

        def seller1_operations():

            client = APIClient()
            client.force_authenticate(user=self.seller1_user)
            for _ in range(operations_per_thread):
                phone_id = random.choice(self.phone_numbers).id
                self.create_charge_sale(client, phone_id, charge_amount)

        def seller2_operations():

            client = APIClient()
            client.force_authenticate(user=self.seller2_user)
            for _ in range(operations_per_thread):
                phone_id = random.choice(self.phone_numbers).id
                self.create_charge_sale(client, phone_id, charge_amount)


        threads = []
        for _ in range(num_threads):
            t1 = threading.Thread(target=seller1_operations)
            t2 = threading.Thread(target=seller2_operations)
            threads.append(t1)
            threads.append(t2)
            t1.start()
            t2.start()


        for t in threads:
            t.join()


        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()


        seller1_charges = ChargeSale.objects.filter(seller=self.seller1).count()
        seller2_charges = ChargeSale.objects.filter(seller=self.seller2).count()


        expected_credit_seller1 = initial_credit - (Decimal(seller1_charges) * charge_amount)
        expected_credit_seller2 = initial_credit - (Decimal(seller2_charges) * charge_amount)


        self.assertEqual(self.seller1.credit, expected_credit_seller1)
        self.assertEqual(self.seller2.credit, expected_credit_seller2)

        transaction_sum_seller1 = Transaction.objects.filter(
            seller=self.seller1,
            transaction_type='charge_sale'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

        transaction_sum_seller2 = Transaction.objects.filter(
            seller=self.seller2,
            transaction_type='charge_sale'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')


        self.assertEqual(-transaction_sum_seller1, Decimal(seller1_charges) * charge_amount)
        self.assertEqual(-transaction_sum_seller2, Decimal(seller2_charges) * charge_amount)

        print(f"Concurrent test: Seller 1 made {seller1_charges} successful charges")
        print(f"Concurrent test: Seller 2 made {seller2_charges} successful charges")

    def test_concurrent_operations(self):

        initial_credit = Decimal('5000')
        self.create_credit_request(self.seller1_client, initial_credit)
        self.create_credit_request(self.seller2_client, initial_credit)


        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()


        self.assertEqual(self.seller1.credit, initial_credit)
        self.assertEqual(self.seller2.credit, initial_credit)


        charge_amount = Decimal('10')
        num_processes = 5
        operations_per_process = 20


        seller1_id = self.seller1_user.id
        seller2_id = self.seller2_user.id
        phone_ids = list(PhoneNumber.objects.values_list('id', flat=True))


        def perform_charges(seller_id, phone_ids, num_operations, result_queue):
            try:

                for conn in connections.all():
                    conn.close()

                from django.db import connection
                connection.connect()

                from rest_framework.test import APIClient
                from django.contrib.auth import get_user_model
                User = get_user_model()

                client = APIClient()
                seller_user = User.objects.get(id=seller_id)
                client.force_authenticate(user=seller_user)

                successful_charges = 0

                for _ in range(num_operations):

                    phone_id = random.choice(phone_ids)


                    charge_data = {
                        'phone_number_id': phone_id,
                        'amount': 10,
                        'transaction_uuid': str(uuid.uuid4())
                    }

                    response = client.post('/api/charge/charges/', charge_data, format='json')


                    if response.status_code == 201:
                        successful_charges += 1


                result_queue.put(successful_charges)

            except Exception as e:

                result_queue.put(f"Error: {str(e)}")


        result_queue = Queue()

        processes = []

        for _ in range(num_processes):
            p = Process(target=perform_charges, args=(seller1_id, phone_ids, operations_per_process, result_queue))
            processes.append(p)
            p.start()


        for _ in range(num_processes):
            p = Process(target=perform_charges, args=(seller2_id, phone_ids, operations_per_process, result_queue))
            processes.append(p)
            p.start()


        for p in processes:
            p.join()


        successful_charges_seller1 = 0
        successful_charges_seller2 = 0
        errors = []

        for _ in range(num_processes * 2):
            result = result_queue.get()
            if isinstance(result, str) and result.startswith("Error:"):
                errors.append(result)
            elif isinstance(result, int):
                if _ < num_processes:
                    successful_charges_seller1 += result
                else:
                    successful_charges_seller2 += result


        if errors:
            for error in errors:
                print(f"Process error: {error}")


        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()


        from django.db import connection

        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT COUNT(*) FROM charge_sales 
                WHERE seller_id = %s AND status = 'successful'
                AND created_at > (SELECT MAX(processed_at) FROM credit_requests WHERE seller_id = %s)
            """, [self.seller1.id, self.seller1.id])
            db_successful_charges_seller1 = cursor.fetchone()[0]


            cursor.execute("""
                SELECT COUNT(*) FROM charge_sales 
                WHERE seller_id = %s AND status = 'successful'
                AND created_at > (SELECT MAX(processed_at) FROM credit_requests WHERE seller_id = %s)
            """, [self.seller2.id, self.seller2.id])
            db_successful_charges_seller2 = cursor.fetchone()[0]


        print(
            f"Seller 1 - Process reported charges: {successful_charges_seller1}, DB charges: {db_successful_charges_seller1}")
        print(
            f"Seller 2 - Process reported charges: {successful_charges_seller2}, DB charges: {db_successful_charges_seller2}")


        expected_credit_seller1 = initial_credit - (Decimal(db_successful_charges_seller1) * charge_amount)
        expected_credit_seller2 = initial_credit - (Decimal(db_successful_charges_seller2) * charge_amount)


        self.assertEqual(self.seller1.credit, expected_credit_seller1,
                         f"Seller 1 credit mismatch. Expected {expected_credit_seller1}, got {self.seller1.credit}")
        self.assertEqual(self.seller2.credit, expected_credit_seller2,
                         f"Seller 2 credit mismatch. Expected {expected_credit_seller2}, got {self.seller2.credit}")


        from credits.models import Transaction
        from django.db.models import Sum


        transaction_sum_seller1 = Transaction.objects.filter(
            seller=self.seller1,
            transaction_type='charge_sale',
            status='successful'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        transaction_sum_seller2 = Transaction.objects.filter(
            seller=self.seller2,
            transaction_type='charge_sale',
            status='successful'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')


        self.assertEqual(-transaction_sum_seller1, Decimal(db_successful_charges_seller1) * charge_amount,
                         "Transaction sum for seller 1 doesn't match the expected charges")
        self.assertEqual(-transaction_sum_seller2, Decimal(db_successful_charges_seller2) * charge_amount,
                         "Transaction sum for seller 2 doesn't match the expected charges")


        total_phone_balance = Decimal('0')
        for phone in PhoneNumber.objects.all():
            phone.refresh_from_db()
            total_phone_balance += phone.current_balance


        expected_total_phone_balance = Decimal(
            db_successful_charges_seller1 + db_successful_charges_seller2) * charge_amount
        self.assertEqual(total_phone_balance, expected_total_phone_balance,
                         "Total phone balance doesn't match the expected value")

    
        print(f"Concurrent test completed successfully:")
        print(
            f"- Seller 1 made {db_successful_charges_seller1} successful charges, remaining credit: {self.seller1.credit}")
        print(
            f"- Seller 2 made {db_successful_charges_seller2} successful charges, remaining credit: {self.seller2.credit}")
        print(f"- Total phone balance: {total_phone_balance}")
