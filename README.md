# پروژه مصاحبه صرافی تبدیل

## صورت پروژه:

در این پروژه قرار است یک نرم افزار فروش شارژ B2B داشته باشیم.

در این سامانه تعدادی فروشنده داریم که هر فروشنده مقداری اعتبار دارد.
فروشنده یک درخواست افزایش اعتبار ثبت می‌کنه و با تایید درخواست از طریق ادمین این اعتبار به فروشنده تخصیص داده می‌شود.

در این سامانه تعدادی شماره تلفن نیز وجود دارد.
بعدها صدا زدن به API Post این فروشنده باید بتواند به شماره تلفن رو به میزان خاصی شارژ کند و به همون میزان از اعتبارش کم می‌شود.

طبیعتا اعتبار فروشنده هیچوقت نباید منفی شود.
حسابداری سیستم حتما باید همخوانی داشته باشد. یعنی این که هر عملیاتی که اعتبار کاربر رو کم و زیاد کرده باید ثبت شده باشه و وقتی record ها رو با همدیگر جمع می‌کنیم باید اعتبار نهایی فروشنده با چیزی که جمع کردیم مطابقت داشته باشد (مثال: حساب فروشنده ۱ میلیون شارژ شده و ۶۰ تا شارژ ۵۰۰۰ تومانی فروخته، پس باید در حسابش ۷۰۰ هزار تومان اعتبار مانده باشد).

طبیعتا record هر تراکنش باید به طور مناسبی ثبت شود (هم افزایش اعتبارها هم فروش ها)

انتظارداریم که نرم افزار زیر بار موازی سنگین هم بتونه خوب و دقیق عمل کند.
شیوه تست API به طور موازی هم به خود فرد سپرده می‌شد.

## تحویل دادنی‌های پروژه:

* معماری و تعریف مدل‌ها
* کارکردصحیح مدل افزایش اعتبار (فقط یک بار شارژ میکند) با ذخیره سازی مجدد کار نمی‌کند.
* ایجادصحیح log مربوط به فروش شارژ
* منفی نشدن اعتبار در فروش شارژ
* منفی نشدن اعتبار در افزایش(کاهش) اعتبار
* کد باید در برابر خطراتی مانند race condition و double spending مقاوم باشد. همچنین باید قفل و انتقال‌ها به صورت اتمیک انجام شود.
* Test Case ساده باید نوشته شده باشد شامل حداقل دو فروشنده، ۱۰ افزایش اعتبار و ۱۰۰۰ فروش شارژ و در نهایت اعتبار فروشنده‌ها درست سنجی شود.
* تست موازی برای درست سنجی سیستم حسابداری تحت لود زیاد و موازی
* فهم تمایز بین multi thread و multi process مخصوصا در پایتون

---

# Interview Project (Exchange Tabdeal)

## Project Scope:

In this project, we are going to develop a B2B charge sales software.

In this system, we have multiple sellers, each with a certain amount of credit.
A seller submits a credit increase request, and upon approval by the admin, this credit is allocated to the seller.

There are also several phone numbers in this system.
Later, by calling the seller's API Post, they should be able to charge a phone number by a specific amount, and their credit will be reduced by the same amount.

Naturally, the seller's credit should never be negative.
The system's accounting must be consistent. This means that any operation that increases or decreases user credit must be recorded, and when we add up all the records, the final credit of the seller should match what we've calculated (Example: The seller's account has been charged 1 million, and they've sold sixty 5,000 Toman charges, so they should have 700,000 Tomans of credit remaining).

Of course, the record of each transaction should be properly recorded (both credit increases and sales).

We expect the software to perform well and accurately under heavy parallel load.
The method of testing the API in parallel is also left to the individual.

## Project Deliverables:

* Architecture and model definitions
* Correct functioning of the credit increase model (charges only once) - doesn't work with repeated saves
* Creating accurate logs related to charge sales
* Preventing negative credit in charge sales
* Preventing negative credit in credit increases/decreases
* The code must be resistant to hazards such as race conditions and double spending. Also, locks and transfers must be done atomically.
* A simple Test Case must be written, including at least two sellers, 10 credit increases, and 1000 charge sales, and ultimately verify the sellers' credit correctly.
* Parallel testing for validating the accounting system under high and parallel load
* Understanding the distinction between multi-thread and multi-process, especially in Python
