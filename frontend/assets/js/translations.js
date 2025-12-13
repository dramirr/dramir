/**
 * ترجمه‌های TalentRadar
 * پشتیبانی برای انگلیسی، عربی و فارسی
 */

const translations = {
    en: {
        // Header
        'header.title': 'TalentRadar',
        'header.subtitle': 'AI-Powered Applicant Tracking System',
        'header.logout': 'Logout',
        'header.connected': 'Connected',
        'header.disconnected': 'Disconnected',
        'header.language': 'Language',

        // Navigation
        'nav.dashboard': '📊 Dashboard',
        'nav.upload': '📤 Upload Resume',
        'nav.results': '📋 Results',
        'nav.candidates': '👥 Candidates',
        'nav.positions': '💼 Positions',

        // Dashboard
        'dashboard.title': 'Dashboard',
        'dashboard.totalResumes': '📊 Total Resumes',
        'dashboard.qualified': '✅ Qualified',
        'dashboard.rejected': '❌ Rejected',
        'dashboard.avgScore': '📈 Avg Score',
        'dashboard.recentApplications': 'Recent Applications',

        // Upload
        'upload.title': 'Upload Resume',
        'upload.selectPosition': 'Select Position',
        'upload.selectPositionPlaceholder': 'Loading positions...',
        'upload.uploadMode': 'Upload Mode',
        'upload.singleResume': 'Single Resume',
        'upload.bulkUpload': 'Bulk Upload',
        'upload.selectFile': 'Select Resume File',
        'upload.selectMultiple': 'Select Multiple Resumes',
        'upload.noFileSelected': 'No file selected',
        'upload.filesSelected': 'file(s) selected',
        'upload.uploadButton': '📤 Upload & Analyze',
        'upload.uploadAllButton': '📤 Upload All',
        'upload.noFile': 'Please select a file',
        'upload.noPosition': 'Please select a position',
        'upload.uploadingMessage': '⏳ Uploading resumes',
        'upload.successMessage': '✅ Resume(s) uploaded successfully!',
        'upload.errorMessage': '❌ Error',
        'upload.totalFilesLabel': 'Total Files',
        'upload.successLabel': 'Successful',
        'upload.failedLabel': 'Failed',
        'upload.uploadedResumesLabel': 'Uploaded Resumes',
        'upload.processingMessage': '⏳ Processing resumes... This may take a few minutes',
        'upload.waitingForResults': 'Waiting for results...',

        // Results
        'results.title': 'All Results',
        'results.allPositions': 'All Positions',
        'results.allStatus': 'All Status',
        'results.completed': '✅ Completed',
        'results.processing': '⏳ Processing',
        'results.pending': '⏳ Pending',
        'results.failed': '❌ Failed',
        'results.scoreRangeFilter': '🎯 Score Range Filter',
        'results.adjustUrgency': 'Adjust urgency level or set custom score range',
        'results.urgencyLevel': '⚡ Urgency Level',
        'results.lowUrgency': 'Low',
        'results.highUrgency': 'High',
        'results.lowUrgencyDesc': 'Low urgency: Only accept high-quality candidates (75%+)',
        'results.mediumUrgencyDesc': 'Medium urgency: Accept candidates with 40%+ score',
        'results.highUrgencyDesc': 'High urgency: Accept all candidates regardless of score',
        'results.or': 'OR',
        'results.customScoreRange': 'Set Custom Score Range',
        'results.minimumScore': 'Minimum Score',
        'results.maximumScore': 'Maximum Score',
        'results.applyFilter': '✓ Apply Filter',
        'results.resetFilter': '↻ Reset',
        'results.candidate': 'Candidate',
        'results.position': 'Position',
        'results.score': 'Score',
        'results.status': 'Status',
        'results.date': 'Date',
        'results.actions': 'Actions',
        'results.view': 'View',
        'results.noResumes': 'No resumes found matching the filters',
        'results.filterApplied': '✅ Filter applied:',

        // Candidates
        'candidates.title': 'Candidates',
        'candidates.search': 'Search by name or phone...',
        'candidates.viewDetails': 'View Details',
        'candidates.noCandidates': 'No candidates found',

        // Positions
        'positions.title': 'Positions',
        'positions.createPosition': '➕ Create Position',
        'positions.noPositions': 'No positions found',

        // Resume Details Modal
        'modal.resumeAnalysis': '📊 Resume Analysis',
        'modal.candidate': '👤',
        'modal.position': 'Position:',
        'modal.phone': 'Phone:',
        'modal.email': 'Email:',
        'modal.uploadDate': 'Upload Date:',
        'modal.overallScore': '📈 Overall Score',
        'modal.statusText': 'Status:',
        'modal.detailedScoring': '🎯 Detailed Scoring',
        'modal.coreCriteria': 'Core Criteria',
        'modal.supplementary': 'Supplementary',
        'modal.extractedValue': 'Extracted Value:',
        'modal.qualified': 'QUALIFIED',
        'modal.rejected': 'REJECTED',

        // Login
        'login.title': 'Login to TalentRadar',
        'login.username': 'Username',
        'login.password': 'Password',
        'login.loginButton': 'Login',
        'login.defaultCredentials': 'Default credentials: admin / admin123',
        'login.failed': 'Login failed',

        // Notifications
        'notification.failedLoadPositions': 'Failed to load positions',
        'notification.failedLoadResults': 'Failed to load results',
        'notification.failedLoadCandidates': 'Failed to load candidates',
        'notification.failedLoadDashboard': 'Failed to load dashboard',
        'notification.failedUpload': 'Failed to upload resume',
        'notification.processingComplete': '✅ Resume processing completed!',
        'notification.processingFailed': '❌ Resume processing failed',
        'notification.processingLongTime': '⏱️ Processing is taking longer than expected',
        'notification.authError': '⚠️ Authentication error. Please login again.',
        'notification.filterReset': '✓ Filter reset',
        'notification.uploadInProgress': '⏳ Upload already in progress',
    },

    ar: {
        // Header
        'header.title': 'تالنت رادار',
        'header.subtitle': 'نظام تتبع المتقدمين المدعوم بالذكاء الاصطناعي',
        'header.logout': 'تسجيل الخروج',
        'header.connected': 'متصل',
        'header.disconnected': 'غير متصل',
        'header.language': 'اللغة',

        // Navigation
        'nav.dashboard': '📊 لوحة التحكم',
        'nav.upload': '📤 تحميل السيرة الذاتية',
        'nav.results': '📋 النتائج',
        'nav.candidates': '👥 المرشحون',
        'nav.positions': '💼 الوظائف',

        // Dashboard
        'dashboard.title': 'لوحة التحكم',
        'dashboard.totalResumes': '📊 إجمالي السيرة الذاتية',
        'dashboard.qualified': '✅ مؤهل',
        'dashboard.rejected': '❌ مرفوض',
        'dashboard.avgScore': '📈 متوسط النقاط',
        'dashboard.recentApplications': 'الطلبات الأخيرة',

        // Upload
        'upload.title': 'تحميل السيرة الذاتية',
        'upload.selectPosition': 'اختر الوظيفة',
        'upload.selectPositionPlaceholder': 'جاري تحميل الوظائف...',
        'upload.uploadMode': 'وضع التحميل',
        'upload.singleResume': 'سيرة ذاتية واحدة',
        'upload.bulkUpload': 'تحميل جماعي',
        'upload.selectFile': 'اختر ملف السيرة الذاتية',
        'upload.selectMultiple': 'اختر عدة سير ذاتية',
        'upload.noFileSelected': 'لم يتم اختيار ملف',
        'upload.filesSelected': 'ملف(ات) محددة',
        'upload.uploadButton': '📤 تحميل وتحليل',
        'upload.uploadAllButton': '📤 تحميل الكل',
        'upload.noFile': 'يرجى اختيار ملف',
        'upload.noPosition': 'يرجى اختيار وظيفة',
        'upload.uploadingMessage': '⏳ جاري تحميل السيرة الذاتية',
        'upload.successMessage': '✅ تم تحميل السيرة الذاتية بنجاح!',
        'upload.errorMessage': '❌ خطأ',
        'upload.totalFilesLabel': 'إجمالي الملفات',
        'upload.successLabel': 'ناجح',
        'upload.failedLabel': 'فشل',
        'upload.uploadedResumesLabel': 'السيرة الذاتية المحملة',
        'upload.processingMessage': '⏳ جاري معالجة السيرة الذاتية... قد يستغرق هذا بعض الوقت',
        'upload.waitingForResults': 'في انتظار النتائج...',

        // Results
        'results.title': 'جميع النتائج',
        'results.allPositions': 'جميع الوظائف',
        'results.allStatus': 'جميع الحالات',
        'results.completed': '✅ مكتمل',
        'results.processing': '⏳ قيد المعالجة',
        'results.pending': '⏳ معلق',
        'results.failed': '❌ فشل',
        'results.scoreRangeFilter': '🎯 مرشح نطاق النقاط',
        'results.adjustUrgency': 'اضبط مستوى الاستعجالية أو عيّن نطاق نقاط مخصص',
        'results.urgencyLevel': '⚡ مستوى الاستعجالية',
        'results.lowUrgency': 'منخفض',
        'results.highUrgency': 'عالي',
        'results.lowUrgencyDesc': 'استعجالية منخفضة: قبول المرشحين عالي الجودة فقط (75%+)',
        'results.mediumUrgencyDesc': 'استعجالية متوسطة: قبول المرشحين بنقاط 40%+',
        'results.highUrgencyDesc': 'استعجالية عالية: قبول جميع المرشحين بغض النظر عن النقاط',
        'results.or': 'أو',
        'results.customScoreRange': 'تعيين نطاق نقاط مخصص',
        'results.minimumScore': 'الحد الأدنى للنقاط',
        'results.maximumScore': 'الحد الأقصى للنقاط',
        'results.applyFilter': '✓ تطبيق المرشح',
        'results.resetFilter': '↻ إعادة تعيين',
        'results.candidate': 'المرشح',
        'results.position': 'الوظيفة',
        'results.score': 'النقاط',
        'results.status': 'الحالة',
        'results.date': 'التاريخ',
        'results.actions': 'الإجراءات',
        'results.view': 'عرض',
        'results.noResumes': 'لم يتم العثور على سير ذاتية تطابق المرشحات',
        'results.filterApplied': '✅ تم تطبيق المرشح:',

        // Candidates
        'candidates.title': 'المرشحون',
        'candidates.search': 'ابحث حسب الاسم أو رقم الهاتف...',
        'candidates.viewDetails': 'عرض التفاصيل',
        'candidates.noCandidates': 'لم يتم العثور على مرشحين',

        // Positions
        'positions.title': 'الوظائف',
        'positions.createPosition': '➕ إنشاء وظيفة',
        'positions.noPositions': 'لم يتم العثور على وظائف',

        // Resume Details Modal
        'modal.resumeAnalysis': '📊 تحليل السيرة الذاتية',
        'modal.candidate': '👤',
        'modal.position': 'الوظيفة:',
        'modal.phone': 'الهاتف:',
        'modal.email': 'البريد الإلكتروني:',
        'modal.uploadDate': 'تاريخ التحميل:',
        'modal.overallScore': '📈 النقاط الإجمالية',
        'modal.statusText': 'الحالة:',
        'modal.detailedScoring': '🎯 النقاط التفصيلية',
        'modal.coreCriteria': 'معايير أساسية',
        'modal.supplementary': 'معايير إضافية',
        'modal.extractedValue': 'القيمة المستخرجة:',
        'modal.qualified': 'مؤهل',
        'modal.rejected': 'مرفوض',

        // Login
        'login.title': 'تسجيل الدخول إلى تالنت رادار',
        'login.username': 'اسم المستخدم',
        'login.password': 'كلمة المرور',
        'login.loginButton': 'تسجيل الدخول',
        'login.defaultCredentials': 'بيانات الاعتماد الافتراضية: admin / admin123',
        'login.failed': 'فشل تسجيل الدخول',

        // Notifications
        'notification.failedLoadPositions': 'فشل تحميل الوظائف',
        'notification.failedLoadResults': 'فشل تحميل النتائج',
        'notification.failedLoadCandidates': 'فشل تحميل المرشحين',
        'notification.failedLoadDashboard': 'فشل تحميل لوحة التحكم',
        'notification.failedUpload': 'فشل تحميل السيرة الذاتية',
        'notification.processingComplete': '✅ اكتمل تحليل السيرة الذاتية!',
        'notification.processingFailed': '❌ فشل تحليل السيرة الذاتية',
        'notification.processingLongTime': '⏱️ المعالجة تستغرق وقتاً أطول من المتوقع',
        'notification.authError': '⚠️ خطأ في المصادقة. يرجى تسجيل الدخول مرة أخرى.',
        'notification.filterReset': '✓ تم إعادة تعيين المرشح',
        'notification.uploadInProgress': '⏳ التحميل جاري بالفعل',
    },

    fa: {
        // Header
        'header.title': 'تالنت رادار',
        'header.subtitle': 'سیستم ردیابی متقاضیان مبتنی بر هوش مصنوعی',
        'header.logout': 'خروج',
        'header.connected': 'متصل',
        'header.disconnected': 'قطع شده',
        'header.language': 'زبان',

        // Navigation
        'nav.dashboard': '📊 داشبورد',
        'nav.upload': '📤 بارگذاری رزومه',
        'nav.results': '📋 نتایج',
        'nav.candidates': '👥 متقاضیان',
        'nav.positions': '💼 موقعیت‌ها',

        // Dashboard
        'dashboard.title': 'داشبورد',
        'dashboard.totalResumes': '📊 کل رزومه‌ها',
        'dashboard.qualified': '✅ واجد شرایط',
        'dashboard.rejected': '❌ رد شده',
        'dashboard.avgScore': '📈 میانگین امتیاز',
        'dashboard.recentApplications': 'درخواست‌های اخیر',

        // Upload
        'upload.title': 'بارگذاری رزومه',
        'upload.selectPosition': 'انتخاب موقعیت',
        'upload.selectPositionPlaceholder': 'در حال بارگذاری موقعیت‌ها...',
        'upload.uploadMode': 'نوع بارگذاری',
        'upload.singleResume': 'یک رزومه',
        'upload.bulkUpload': 'بارگذاری دسته‌ای',
        'upload.selectFile': 'انتخاب فایل رزومه',
        'upload.selectMultiple': 'انتخاب رزومه‌های متعدد',
        'upload.noFileSelected': 'فایلی انتخاب نشد',
        'upload.filesSelected': 'فایل انتخاب شده',
        'upload.uploadButton': '📤 بارگذاری و تحلیل',
        'upload.uploadAllButton': '📤 بارگذاری همه',
        'upload.noFile': 'لطفا یک فایل انتخاب کنید',
        'upload.noPosition': 'لطفا یک موقعیت انتخاب کنید',
        'upload.uploadingMessage': '⏳ در حال بارگذاری رزومه',
        'upload.successMessage': '✅ رزومه با موفقیت بارگذاری شد!',
        'upload.errorMessage': '❌ خطا',
        'upload.totalFilesLabel': 'کل فایل‌ها',
        'upload.successLabel': 'موفق',
        'upload.failedLabel': 'ناموفق',
        'upload.uploadedResumesLabel': 'رزومه‌های بارگذاری شده',
        'upload.processingMessage': '⏳ در حال پردازش رزومه‌ها... این ممکن است چند دقیقه طول بکشد',
        'upload.waitingForResults': 'در انتظار نتایج...',

        // Results
        'results.title': 'تمام نتایج',
        'results.allPositions': 'تمام موقعیت‌ها',
        'results.allStatus': 'تمام وضعیت‌ها',
        'results.completed': '✅ تکمیل شده',
        'results.processing': '⏳ در حال پردازش',
        'results.pending': '⏳ در انتظار',
        'results.failed': '❌ ناموفق',
        'results.scoreRangeFilter': '🎯 فیلتر محدوده امتیاز',
        'results.adjustUrgency': 'تنظیم سطح فوریت یا تعیین محدوده امتیاز دلخواه',
        'results.urgencyLevel': '⚡ سطح فوریت',
        'results.lowUrgency': 'پایین',
        'results.highUrgency': 'بالا',
        'results.lowUrgencyDesc': 'فوریت پایین: فقط متقاضیان با کیفیت بالا را قبول کنید (75%+)',
        'results.mediumUrgencyDesc': 'فوریت متوسط: متقاضیان با امتیاز 40%+ را قبول کنید',
        'results.highUrgencyDesc': 'فوریت بالا: تمام متقاضیان را بدون در نظر گرفتن امتیاز قبول کنید',
        'results.or': 'یا',
        'results.customScoreRange': 'تعیین محدوده امتیاز دلخواه',
        'results.minimumScore': 'حداقل امتیاز',
        'results.maximumScore': 'حداکثر امتیاز',
        'results.applyFilter': '✓ اعمال فیلتر',
        'results.resetFilter': '↻ بازنشانی',
        'results.candidate': 'متقاضی',
        'results.position': 'موقعیت',
        'results.score': 'امتیاز',
        'results.status': 'وضعیت',
        'results.date': 'تاریخ',
        'results.actions': 'اقدامات',
        'results.view': 'نمایش',
        'results.noResumes': 'رزومه‌ای منطبق با فیلترها یافت نشد',
        'results.filterApplied': '✅ فیلتر اعمال شد:',

        // Candidates
        'candidates.title': 'متقاضیان',
        'candidates.search': 'جستجو بر اساس نام یا تلفن...',
        'candidates.viewDetails': 'نمایش جزئیات',
        'candidates.noCandidates': 'متقاضی یافت نشد',

        // Positions
        'positions.title': 'موقعیت‌ها',
        'positions.createPosition': '➕ ایجاد موقعیت',
        'positions.noPositions': 'موقعیتی یافت نشد',

        // Resume Details Modal
        'modal.resumeAnalysis': '📊 تحلیل رزومه',
        'modal.candidate': '👤',
        'modal.position': 'موقعیت:',
        'modal.phone': 'تلفن:',
        'modal.email': 'ایمیل:',
        'modal.uploadDate': 'تاریخ بارگذاری:',
        'modal.overallScore': '📈 امتیاز کل',
        'modal.statusText': 'وضعیت:',
        'modal.detailedScoring': '🎯 امتیازدهی تفصیلی',
        'modal.coreCriteria': 'معیارهای اساسی',
        'modal.supplementary': 'معیارهای تکمیلی',
        'modal.extractedValue': 'مقدار استخراج شده:',
        'modal.qualified': 'واجد شرایط',
        'modal.rejected': 'رد شده',

        // Login
        'login.title': 'ورود به تالنت رادار',
        'login.username': 'نام کاربری',
        'login.password': 'رمز عبور',
        'login.loginButton': 'ورود',
        'login.defaultCredentials': 'اطلاعات پیش‌فرض: admin / admin123',
        'login.failed': 'ورود ناموفق بود',

        // Notifications
        'notification.failedLoadPositions': 'بارگذاری موقعیت‌ها ناموفق',
        'notification.failedLoadResults': 'بارگذاری نتایج ناموفق',
        'notification.failedLoadCandidates': 'بارگذاری متقاضیان ناموفق',
        'notification.failedLoadDashboard': 'بارگذاری داشبورد ناموفق',
        'notification.failedUpload': 'بارگذاری رزومه ناموفق',
        'notification.processingComplete': '✅ تحلیل رزومه تکمیل شد!',
        'notification.processingFailed': '❌ تحلیل رزومه ناموفق',
        'notification.processingLongTime': '⏱️ پردازش بیشتر از حد انتظار طول کشید',
        'notification.authError': '⚠️ خطای تایید. لطفا دوباره وارد شوید.',
        'notification.filterReset': '✓ فیلتر بازنشانی شد',
        'notification.uploadInProgress': '⏳ بارگذاری در حال انجام است',
    }
};

function t(key, lang = getCurrentLanguage()) {
    if (translations[lang] && translations[lang][key]) {
        return translations[lang][key];
    }
    if (translations['en'] && translations['en'][key]) {
        return translations['en'][key];
    }
    return key;
}

function getCurrentLanguage() {
    return localStorage.getItem('language') || 'en';
}

function setLanguage(lang) {
    if (translations[lang]) {
        localStorage.setItem('language', lang);
        const direction = (lang === 'ar' || lang === 'fa') ? 'rtl' : 'ltr';
        document.documentElement.dir = direction;
        document.documentElement.lang = lang;
        updatePageLanguage();
    }
}

function updatePageLanguage() {
    const lang = getCurrentLanguage();
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = t(key, lang);
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            element.placeholder = translation;
        } else {
            element.textContent = translation;
        }
    });
    updateDynamicTranslations(lang);
}

function updateDynamicTranslations(lang) {
    // اختیاری برای بروزرسانی‌های دینامی
}

window.addEventListener('load', () => {
    const lang = getCurrentLanguage();
    setLanguage(lang);
});