# 🎬 Video Demo Script
## Purchase Management System - نظام إدارة المشتريات

---

**Video Duration:** ~8-10 minutes
**Style:** Screen Recording + Voice Over
**Background:** Dark theme (as seen in the system)
**Language:** Arabic (can be translated to English)

---

## 🎯 Scene 1: Opening - "المشكلة" (0:00 - 1:15)

### Screen: Black screen or Login Page (voiceover starts before clicking anything)

### 🛠️ **التقنيات والأدوات في هذه الصفحة:**
- **Django Authentication** - نظام تسجيل الدخول بالبريد الإلكتروني وكلمة المرور
- **Session Management** - إدارة جلسات المستخدم
- **Role-Based Access Control** - التحكم بالصلاحيات حسب الدور (Admin, Approver, PO, Requester)

### 🎙️ **Script (Arabic) - "كيف كانت العملية قبل؟":**

> "قبل وجود هذا النظام... شلون كانت تتم عملية الشراء في المؤسسات؟
>
> الموظف اللي يحتاج مواد... يكتب طلب على ورق أو إكسل
> ويطبع نسخة ورقية ويمشي بها لمكتب المسؤول عشان يوافق
>
> المسؤول... يشوف الطلب ويوافق أو يرفض
> لكن الطلب ممكن يضيع بالبريد الداخلي، أو يتأخر أيام على مكتب المسؤول وهو مش فاضي
>
> بعد الموافقة، تبدأ رحلة البحث عن موردين:
> - يكتب إيميل لكل مورد على حدة
> - يرفق صورة الطلب أو PDF
> - وينتظر... يمكن يوم، يمكن أسبوع
>
> ولما تجيه عروض الأسعار:
> - يفتح إكسل جديد
> - يدخل البيانات يدويًا
> - يقارن بين الأسعار... بالعين!
> - والغالب يختار أرخص سعر بدون ما يقيم الجودة أو مدة التوريد
>
> والأهم... وين سجلت العملية؟ وين الشفافية؟ وين التقارير للمراجعة؟"

---

## 🎯 Scene 2: "الحل" - Login & Dashboard (1:15 - 2:30)


**Action:**
1. Enter admin email: `admin@purchasesys.com`
2. Enter password
3. Click login
4. Dashboard loads with stats and charts

### 🛠️ **التقنيات والأدوات في هذه الصفحة:**
- **Django ORM Aggregation** - استعلامات تجميعية لحساب الإحصائيات (Count, Sum)
- **Chart.js** - مكتبة JavaScript للرسوم البيانية (Doughnut, Bar)
- **AJAX / JSON Response** - تحميل الإحصائيات dynamically بدون تحديث الصفحة
- **Bootstrap / Tailwind CSS Grid** - تنسيق البطاقات (Cards) بشكل شبكي responsive
- **Django Template Tags** - عرض البيانات بشكل ديناميكي في القوالب
- **RESTful API Endpoint** - نقطة نهاية API لجلب الإحصائيات (`/api/stats/`)

### 🎙️ **Script (Arabic) - "الحل":**

> "من هنا جاء دور **نظام إدارة المشتريات**...
>
> نفس العملية اللي قلناها... لكن **بطريقة ذكية ومؤتمتة بالكامل.**
>
> 🟢 **إنشاء طلب شراء:** ببضع نقرات، اختار المواد من القائمة، حدد الكميات، وقدم الطلب
> 🟢 **الموافقة:** بنقرة زر، بدون ورق، بدون انتظار، وكل شيء مسجل بتاريخه
> 🟢 **إرسال طلبات العروض:** النظام يبحث عن الموردين المناسبين آليًا ويرسل PDF احترافي
> 🟢 **المقارنة:** خوارزمية ذكية تقارن السعر ومدة التوريد والتقييم وتقترح أفضل مورد
> 🟢 **التقارير:** لوحة تحكم تفاعلية مع رسوم بيانية وتقارير PDF جاهزة
>
> **كل هذا في نظام واحد متكامل. خلونا ندخل ونشوف كيف...**
>
> *(هنا يدخل admin@purchasesys.com ويسجل دخول)*
>
> "نظامنا يعتمد على تسجيل الدخول بالبريد الإلكتروني.
> المستخدمين مقسمين إلى 4 أدوار: Requester، Approver، Purchasing Officer، Admin.
>
> الـ Dashboard يعرض:
> - إحصائيات شاملة لجميع الطلبات
> - رسم بياني يوضح توزيع الطلبات حسب الحالة
> - رسم بياني شهري لمتابعة الأداء
> - آخر الطلبات المضافة
> - إجراءات سريعة للوصول للوظائف الأكثر استخدامًا"

## 🎯 Scene 3: Manage Users (2:30 - 3:15)

### Screen: Navigate to Users List

**Action:**
1. Click "Users" in sidebar
2. Show users table with different roles
3. Click "Add User" button
4. Fill form briefly

### 🎙️ **Script (Arabic):**

> "من هنا يمكن للمسؤول إدارة المستخدمين في النظام.
> يمكن إضافة مستخدمين جدد، تحديد دور كل مستخدم،
> وتفعيل أو تعطيل الحسابات حسب الحاجة.
> هذه الميزة متاحة فقط للمسؤول (Admin) حفاظًا على أمان النظام."

---

## 🎯 Scene 4: Create Purchase Request (3:15 - 4:30)

### Screen: Sidebar → Purchase Requests → Create New Request

**Action:**
1. Click "Purchase Requests" in sidebar
2. Click "New Request" button
3. Fill title
4. Add materials from dropdown
5. Enter quantities
6. Save Draft / Submit for Approval

### 🎙️ **Script (Arabic) - "الطلب":**

> "الحين راح نشوف شلون ننشيء طلب شراء جديد.
>
> نضغط Purchase Requests > New Request.
>
> أول شي: نكتب عنوان الطلب... خلينا نقول 'مواد خام للإنتاج'.
>
> بعدين نختار المواد المطلوبة... شفتوا؟
> كل المواد موجودة مسبقًا بقاعدة بيانات موحدة.
> كل مادة مرتبطة بوحدة قياسها: كجم، لتر، قطعة... تضمن دقة البيانات.
>
> نحدد الكمية... أسهل من الإكسل والورق، صح؟
>
> بالنهاية عندنا خيارين:
> - **Save Draft:** نحفظ مسودة نعدل عليها لاحقًا
> - **Submit for Approval:** نرسل للموافقة مباشرة"

---

## 🎯 Scene 5: Submit for Approval (4:30 - 5:15)

### Screen: Request Detail → Click "Submit for Approval"

**Action:**
1. Show request detail page
2. Click "Submit for Approval" button
3. Status changes to "Pending Approval"

### 🎙️ **Script (Arabic) - "الإرسال":**

> "نضغط Submit for Approval... خلص!
> - تسجل في سجل الموافقات
> - تتغير الحالة لـ Pending Approval
> - وتصير متاحة للموافق يشوفها
>
> كل هذا بدون ورق ولا مشي، وكل شيء مسجل."

---

## 🎯 Scene 6: Approve/Reject Request (5:15 - 6:00)

### Screen: Logout → Login as Approver → Approve/Reject

**Action:**
1. Logout → Login as Approver
2. Navigate to pending request
3. Click "Approve"
4. OR click "Reject" + add reason

### 🎙️ **Script (Arabic) - "الموافقة":**

> "الحين من وجهة نظر الـ Approver. نسجل دخول بحساب الموافق.
>
> الـ Dashboard يظهر له كل الطلبات المعلقة.
>
> يدخل على الطلب... إذا كل شيء تمام، يضغط **Approve**... خلاص! تمت الموافقة. ✅
>
> إذا في شي غلط، يضغط **Reject** ويكتب سبب الرفض.
>
> **كل الإجراءات مسجلة بتاريخها.** شفافية كاملة."

---

## 🎯 Scene 7: PDF Export (6:00 - 6:30)

### Screen: Request Detail → Export PDF

**Action:**
1. Click "Export PDF" button
2. Show PDF opening/downloading
3. Briefly show PDF content

### 🎙️ **Script (Arabic) - "التقارير":**

> "ميزة حلوة... تصدير طلب الشراء كـ PDF احترافي.
>
> نضغط **Export PDF**... يولد النظام مستند متكامل:
> - معلومات الطلب
> - جدول المواد
> - حالة الموافقة
>
> PDF جاهز للطباعة أو الإرسال للموردين مباشرة."

---

## 🎯 Scene 8: Send RFQ via Email (6:30 - 7:15)

### Screen: Request Detail → Send to Supplier Modal

**Action:**
1. Click "Send to Supplier"
2. Show modal with supplier list
3. Select a supplier (show preview)
4. Click "Send Email"

### 🎙️ **Script (Arabic) - "RFQ":**

> "تذكروا أول لما قلنا إن الموظف كان يكتب إيميل لكل مورد على حدة؟
>
> هنا الحل! نضغط **Send to Supplier**.
> تظهر نافذة فيها قائمة الموردين اللي يوردون المواد المطلوبة بالضبط.
>
> نختار المورد... نشوف معاينة لمعلوماته.
> ونضغط **Send Email**.
>
> النظام يرسل PDF احترافي على بريد المورد... آليًا. 📧"

---

## 🎯 Scene 9: Supplier Management (7:15 - 8:00)

### Screen: Sidebar → Suppliers → Supplier Detail

**Action:**
1. Navigate to Suppliers
2. Show supplier cards (ratings, status)
3. Click a supplier → show details
4. Show materials + quotations

### 🎙️ **Script (Arabic) - "الموردين":**

> "قسم إدارة الموردين.
>
> كل مورد مع:
> - تقييمه (1-5 نجوم)
> - حالة النشاط
> - عدد الطلبات السابقة
>
> ندخل على التفاصيل... نشوف:
> - معلومات التواصل
> - المواد اللي يوردها مع مدة التوريد
> - عروض الأسعار السابقة
>
> كل مورد مربوط بمواد محددة... عشان البحث يكون سهل."

---

## 🎯 Scene 10: Material Management (8:00 - 8:30)

### Screen: Sidebar → Materials → Material Detail

**Action:**
1. Navigate to Materials
2. Show materials table
3. Show categories
4. Click a material → supplier prices

### 🎙️ **Script (Arabic) - "المواد":**

> "قسم المواد الخام... مخزن مركزي لكل المواد.
>
> كل مادة لها: اسم، وصف، وحدة قياس، وتصنيف.
>
> ونقدر نربط كل مادة بعدة موردين مع أسعارهم المرجعية
> ومدة التوريد. كل شيء مركزي ومنظم."

---

## 🎯 Scene 11: Adding Quotations - إدخال عروض الأسعار (8:30 - 9:15)

### Screen: Request Detail (approved) → Click "Add Quotation" → Quotation Form Page

**Action:**
1. Login as **Admin** or **Purchasing Officer**
2. Navigate to an approved request
3. Click "Add Quotation" button (الموجود في الـ header)
4. Quotation form page opens: select supplier, delivery days
5. Enter unit prices for each material (system auto-calculates totals)
6. Click "Submit Quotation"
7. Repeat for 2nd supplier quotation

### 🎙️ **Script (Arabic) - "إدخال العروض":**

> "الحين... بعد ما تمت الموافقة على الطلب،
> ننتقل لمرحلة جمع عروض الأسعار من الموردين.
>
> **هذي المهمة خاصة بـ Admin أو Purchasing Officer.**
>
> أول شي: نضغط **Add Quotation** اللي ظهرت بعد الموافقة.
> بتنفتح صفحة إدخال عرض السعر.
>
> نختار المورد اللي قدم لنا عرض...
> نحدد مدة التوريد بالأيام...
> وندخل سعر الوحدة لكل مادة.
>
> شفتوا؟ **النظام يحسب آليًا المجموع الإجمالي** لكل مادة والمجموع الكامل.
>
> نضغط **Submit Quotation**... وخلاص! عرض السعر الأول دخل.
>
> نعيد نفس الخطوات لإدخال عرض تاني من مورد ثاني...
> وبكذا عندنا عروض أسعار جاهزة للمقارنة."

---

## 🎯 Scene 12: Quotation Comparison & Best Supplier (9:15 - 10:00)

### Screen: Request Detail → Click "Compare Offers" → Comparison Page

**Action:**
1. Navigate to request (after entering 2+ quotations)
2. Click "Compare Offers" button
3. Show comparison page: table + cards
4. Click "Suggest Best Supplier"
5. Show winner highlighted in green glow

### 🎙️ **Script (Arabic) - "المقارنة":**

> "الحين عندنا عروض من أكثر من مورد...
> **كيف نقارن بينهم ونختار الأفضل؟** 🤔
>
> هنا أقوى ميزة في النظام! **مقارنة عروض الأسعار بخوارزمية ذكية** 😍
>
> تذكروا أول لما قلنا الموظف كان يقارن العروض بالعين؟
> هنا **النظام يسويها آليًا**.
>
> نضغط **Compare Offers**... نشوف جميع العروض جنب بعضها:
> - جدول مقارنة كامل
> - بطاقات تفصيلية لكل عرض
> - تقييم المورد، السعر، مدة التوريد
>
> نضغط **Suggest Best Supplier**...
> الخوارزمية تطبق 3 معايير بوزن محدد:
> 🟦 **السعر:** 50% (الأقل أفضل)
> 🟩 **مدة التوريد:** 30% (الأقل أفضل)
> ⭐ **تقييم المورد:** 20% (الأعلى أفضل)
>
> المورد بأقل مجموع نقاط هو الأفضل.
> يظهر متميزًا باللون الأخضر مع تأثير متحرك... مباشرة! 🏆"

---

## 🎯 Scene 13: Award Supplier (10:00 - 10:20)

### Screen: Comparison Page → Click "Award to this supplier" button

**Action:**
1. Click "Award to this supplier" button
2. Status changes to "Awarded"
3. Supplier name + badge appears on PR

### 🎙️ **Script (Arabic) - "الترسية":**

> "نضغط **Award to this supplier**... وخلاص! تمت الترسية. 🏆
> الحالة تتغير لـ Awarded والمورد الفائز مسجل بالطلب.
>
> **شفافية كاملة من البداية للنهاية.**"

---


## 🎯 Scene 14: Dashboard & Analytics (10:20 - 11:00)

### Screen: Back to Dashboard

**Action:**
1. Navigate back to Dashboard
2. Show updated stats (Awarded count increased)
3. Show doughnut chart
4. Show bar chart (monthly)
5. Show recent requests table

### 🎙️ **Script (Arabic) - "التحليل":**

> "نرجع للـ Dashboard نشوف الصورة الكاملة.
>
> الإحصائيات تحدثت... الآن عندنا طلبات بدأت Draft ووصلت Awarded.
>
> الرسوم البيانية:
> - رسمة Doughnut توضح توزيع الطلبات حسب الحالة
> - رسمة Bar للطلبات الشهرية
>
> وجدول آخر الطلبات للمتابعة السريعة.
>
> **كل هذا في شاشة واحدة.**"

---

## 🎯 Scene 16: Profile & Activity Log (11:00 - 11:30)

### Screen: Profile Page → Activity Log (admin)

**Action:**
1. Navigate to Profile
2. Show user info (read-only)
3. Show change password form
4. Show recent activity section
5. Navigate to Activity Log (admin only)
6. Show filters (user, action type) + pagination

### 🎙️ **Script (Arabic) - "الملف الشخصي":**

> "كل مستخدم عنده صفحة ملف شخصي:
> - يشوف معلومات حسابه
> - يغير كلمة المرور
> - يراقب آخر نشاطاته
>
> والمسؤول عنده صلاحية الوصول لـ **Activity Log**...
> سجل كامل لكل الإجراءات اللي صارت في النظام مع فلترة
> حسب المستخدم ونوع الإجراء.
>
> **للتدقيق والشفافية الكاملة.**"

---
## 🎯 Scene 17: Closing (11:30 - 12:00)

### Screen: Dashboard → zoom out

### 🎙️ **Script (Arabic) - "الختام":**

> "بهذا نكون استعرضنا **نظام إدارة المشتريات**.
>
> **قبل النظام:**
> ❌ ورق وإكسل وإيميلات متفرقة
> ❌ ضياع طلبات وتأخير بالموافقات
> ❌ إدخال عروض بإكسل ومقارنة بالعين
> ❌ لا شفافية ولا تقارير
>
> **بعد النظام:**
> ✅ نظام متكامل ومؤتمت بالكامل
> ✅ إنشاء طلب بنقرة، موافقة بنقرة
> ✅ **إدخال عروض الأسعار ومقارنتها بخوارزمية ذكية**
> ✅ تقارير PDF ولوحة تحكم تفاعلية
> ✅ سجل نشاطات كامل للتدقيق
>
> **شكرًا لمتابعتكم.** 🚀"

---

## 📋 Technical Notes for Recording

### Recording Settings
| Setting | Value |
|---|---|
| Screen Resolution | 1920x1080 (Full HD) |
| Frame Rate | 30 fps |
| Recording Software | OBS Studio / Screen Recorder |
| Audio | Microphone + Noise Reduction |

### Pre-Recording Checklist
- [ ] Clear database with demo data
- [ ] Have at least:
  - 3 users (admin, approver, requester)
  - 5+ materials
  - 3+ suppliers with linked materials
  - 2+ purchase requests in different statuses
  - 2+ quotations from suppliers
- [ ] Clean browser cache
- [ ] Close unnecessary tabs
- [ ] Open recording software

### Post-Production
- Add intro/outro music (fade in/out)
- Add captions/subtitles
- Add zoom effects on important elements
- Speed up repetitive actions (optional)

---

## 🔑 Demo Accounts

| Role | Email | Password |
|---|---|---|
| Admin | admin@purchasesys.com | admin123 |
| Approver | approver@purchasesys.com | approver123 |
| Requester | requester@purchasesys.com | requester123 |
| Purchasing Officer | po@purchasesys.com | po123 |

---

*Script Version: 1.0.0*
*Last Updated: 2024*
