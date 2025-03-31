/**
 * RSEO - لوحة تحكم تفاعلية
 * 
 * ملف JavaScript الرئيسي للوحة التحكم التفاعلية باستخدام React
 */

// تهيئة React
const { useState, useEffect, useRef } = React;

// مكون التطبيق الرئيسي
const App = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [url, setUrl] = useState('');
  const [error, setError] = useState(null);
  const [settings, setSettings] = useState({
    depth: 3,
    maxPages: 50,
    autoFix: false,
    respectRobots: true,
    crawlImages: true,
    singlePage: false,
    includeSubdomains: false
  });

  // تغيير التبويب النشط
  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  // تغيير الإعدادات
  const handleSettingsChange = (setting, value) => {
    setSettings({
      ...settings,
      [setting]: value
    });
  };

  // بدء التحليل
  const startAnalysis = async () => {
    if (!url) {
      setError('الرجاء إدخال رابط للتحليل');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          url,
          ...settings
        })
      });

      if (!response.ok) {
        throw new Error(`فشل الطلب بالحالة ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
      setActiveTab('results');
    } catch (err) {
      setError(`حدث خطأ: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // مكون الشريط الجانبي
  const Sidebar = () => (
    <div className="sidebar">
      <div className="logo">
        <img src="/static/images/logo.png" alt="RSEO Logo" />
        <h1>RSEO</h1>
      </div>
      <nav>
        <ul>
          <li className={activeTab === 'dashboard' ? 'active' : ''} onClick={() => handleTabChange('dashboard')}>
            <i className="fas fa-home"></i> الرئيسية
          </li>
          <li className={activeTab === 'results' ? 'active' : ''} onClick={() => handleTabChange('results')}>
            <i className="fas fa-chart-bar"></i> النتائج
          </li>
          <li className={activeTab === 'settings' ? 'active' : ''} onClick={() => handleTabChange('settings')}>
            <i className="fas fa-cog"></i> الإعدادات
          </li>
          <li className={activeTab === 'history' ? 'active' : ''} onClick={() => handleTabChange('history')}>
            <i className="fas fa-history"></i> السجل
          </li>
          <li className={activeTab === 'help' ? 'active' : ''} onClick={() => handleTabChange('help')}>
            <i className="fas fa-question-circle"></i> المساعدة
          </li>
        </ul>
      </nav>
    </div>
  );

  // مكون لوحة القيادة
  const Dashboard = () => (
    <div className="dashboard-content">
      <h2>أداة تحليل وتحسين السيو</h2>
      <div className="url-form">
        <input 
          type="text" 
          value={url} 
          onChange={(e) => setUrl(e.target.value)} 
          placeholder="أدخل رابط الموقع للتحليل"
        />
        <button onClick={startAnalysis} disabled={isLoading}>
          {isLoading ? <i className="fas fa-spinner fa-spin"></i> : <i className="fas fa-search"></i>} تحليل
        </button>
      </div>
      {error && <div className="error-alert">{error}</div>}
      <div className="quick-settings">
        <div className="setting">
          <input 
            type="checkbox" 
            id="singlePage" 
            checked={settings.singlePage} 
            onChange={(e) => handleSettingsChange('singlePage', e.target.checked)} 
          />
          <label htmlFor="singlePage">تحليل صفحة واحدة فقط</label>
        </div>
        <div className="setting">
          <input 
            type="checkbox" 
            id="autoFix" 
            checked={settings.autoFix} 
            onChange={(e) => handleSettingsChange('autoFix', e.target.checked)} 
          />
          <label htmlFor="autoFix">إصلاح المشاكل تلقائياً</label>
        </div>
      </div>
      <div className="tools-shortcuts">
        <h3>أدوات سريعة</h3>
        <div className="tools-grid">
          <div className="tool-card" onClick={() => handleTabChange('on-page')}>
            <i className="fas fa-file-alt"></i>
            <h4>تحليل الصفحة</h4>
            <p>تحليل عناصر السيو داخل الصفحة</p>
          </div>
          <div className="tool-card" onClick={() => handleTabChange('technical')}>
            <i className="fas fa-code"></i>
            <h4>تحليل تقني</h4>
            <p>فحص العناصر التقنية للموقع</p>
          </div>
          <div className="tool-card" onClick={() => handleTabChange('keywords')}>
            <i className="fas fa-key"></i>
            <h4>تحليل الكلمات المفتاحية</h4>
            <p>تحليل الكلمات المفتاحية واقتراح التحسينات</p>
          </div>
          <div className="tool-card" onClick={() => handleTabChange('competitors')}>
            <i className="fas fa-users"></i>
            <h4>تحليل المنافسين</h4>
            <p>مقارنة موقعك مع المنافسين</p>
          </div>
        </div>
      </div>
    </div>
  );

  // مكون النتائج
  const Results = () => {
    if (!results) {
      return (
        <div className="no-results">
          <i className="fas fa-search"></i>
          <h3>لا توجد نتائج</h3>
          <p>قم بتحليل موقع لعرض النتائج هنا</p>
        </div>
      );
    }

    const { url, analysis_time, overall_score, issues, on_page, technical, performance } = results;

    return (
      <div className="results-content">
        <div className="results-header">
          <h2>نتائج تحليل: {url}</h2>
          <div className="analysis-meta">
            <span><i className="fas fa-clock"></i> تاريخ التحليل: {new Date(analysis_time * 1000).toLocaleString()}</span>
            <button className="export-btn"><i className="fas fa-download"></i> تصدير PDF</button>
          </div>
        </div>
        
        <div className="score-overview">
          <div className="score-card overall">
            <div className="score-circle" style={{ background: `conic-gradient(#4CAF50 ${overall_score}%, #f3f3f3 0)` }}>
              <span>{overall_score}%</span>
            </div>
            <h3>الدرجة الإجمالية</h3>
          </div>
          <div className="score-card">
            <div className="score-circle" style={{ background: `conic-gradient(#2196F3 ${on_page.score}%, #f3f3f3 0)` }}>
              <span>{on_page.score}%</span>
            </div>
            <h3>On-Page SEO</h3>
          </div>
          <div className="score-card">
            <div className="score-circle" style={{ background: `conic-gradient(#FF9800 ${technical.score}%, #f3f3f3 0)` }}>
              <span>{technical.score}%</span>
            </div>
            <h3>Technical SEO</h3>
          </div>
          <div className="score-card">
            <div className="score-circle" style={{ background: `conic-gradient(#E91E63 ${performance.score}%, #f3f3f3 0)` }}>
              <span>{performance.score}%</span>
            </div>
            <h3>الأداء</h3>
          </div>
        </div>
        
        <div className="issues-summary">
          <h3>ملخص المشاكل</h3>
          <div className="issues-chart">
            <div className="issue-level critical" style={{ width: `${issues.critical.length * 5}%` }}>
              <span>{issues.critical.length}</span>
            </div>
            <div className="issue-level warnings" style={{ width: `${issues.warnings.length * 5}%` }}>
              <span>{issues.warnings.length}</span>
            </div>
            <div className="issue-level notices" style={{ width: `${issues.notices.length * 5}%` }}>
              <span>{issues.notices.length}</span>
            </div>
          </div>
          <div className="issue-legend">
            <div><span className="dot critical"></span> حرجة</div>
            <div><span className="dot warnings"></span> تحذيرات</div>
            <div><span className="dot notices"></span> ملاحظات</div>
          </div>
        </div>
        
        <div className="results-tabs">
          <ul>
            <li className="active">نظرة عامة</li>
            <li>On-Page SEO</li>
            <li>Technical SEO</li>
            <li>Core Web Vitals</li>
            <li>الروابط</li>
            <li>المحتوى</li>
            <li>الصور</li>
          </ul>
          
          <div className="tab-content">
            <div className="issues-list">
              <h3>المشاكل الحرجة ({issues.critical.length})</h3>
              <ul>
                {issues.critical.map((issue, index) => (
                  <li key={`critical-${index}`} className="issue critical">
                    <i className="fas fa-times-circle"></i>
                    <div>
                      <h4>{issue.title}</h4>
                      <p>{issue.description}</p>
                      {issue.canFix && <button className="fix-btn">إصلاح تلقائي</button>}
                    </div>
                  </li>
                ))}
              </ul>
              
              <h3>التحذيرات ({issues.warnings.length})</h3>
              <ul>
                {issues.warnings.map((issue, index) => (
                  <li key={`warning-${index}`} className="issue warning">
                    <i className="fas fa-exclamation-triangle"></i>
                    <div>
                      <h4>{issue.title}</h4>
                      <p>{issue.description}</p>
                      {issue.canFix && <button className="fix-btn">إصلاح تلقائي</button>}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // مكون الإعدادات
  const Settings = () => (
    <div className="settings-content">
      <h2>إعدادات التحليل</h2>
      <div className="settings-form">
        <div className="setting-group">
          <h3>إعدادات الزحف</h3>
          <div className="setting-row">
            <label htmlFor="depth">عمق الزحف:</label>
            <input 
              type="number" 
              id="depth" 
              min="1" 
              max="10" 
              value={settings.depth} 
              onChange={(e) => handleSettingsChange('depth', parseInt(e.target.value))} 
            />
          </div>
          <div className="setting-row">
            <label htmlFor="maxPages">أقصى عدد للصفحات:</label>
            <input 
              type="number" 
              id="maxPages" 
              min="1" 
              max="500" 
              value={settings.maxPages} 
              onChange={(e) => handleSettingsChange('maxPages', parseInt(e.target.value))} 
            />
          </div>
          <div className="setting-row checkbox">
            <input 
              type="checkbox" 
              id="respectRobots" 
              checked={settings.respectRobots} 
              onChange={(e) => handleSettingsChange('respectRobots', e.target.checked)} 
            />
            <label htmlFor="respectRobots">احترام robots.txt</label>
          </div>
          <div className="setting-row checkbox">
            <input 
              type="checkbox" 
              id="crawlImages" 
              checked={settings.crawlImages} 
              onChange={(e) => handleSettingsChange('crawlImages', e.target.checked)} 
            />
            <label htmlFor="crawlImages">زحف وتحليل الصور</label>
          </div>
          <div className="setting-row checkbox">
            <input 
              type="checkbox" 
              id="includeSubdomains" 
              checked={settings.includeSubdomains} 
              onChange={(e) => handleSettingsChange('includeSubdomains', e.target.checked)} 
            />
            <label htmlFor="includeSubdomains">تضمين النطاقات الفرعية</label>
          </div>
        </div>
        
        <div className="setting-group">
          <h3>إعدادات التحليل</h3>
          <div className="setting-row checkbox">
            <input 
              type="checkbox" 
              id="autoFix" 
              checked={settings.autoFix} 
              onChange={(e) => handleSettingsChange('autoFix', e.target.checked)} 
            />
            <label htmlFor="autoFix">إصلاح المشاكل تلقائياً</label>
          </div>
          <div className="setting-row checkbox">
            <input 
              type="checkbox" 
              id="singlePage" 
              checked={settings.singlePage} 
              onChange={(e) => handleSettingsChange('singlePage', e.target.checked)} 
            />
            <label htmlFor="singlePage">تحليل صفحة واحدة فقط</label>
          </div>
        </div>
        
        <div className="setting-group">
          <h3>إعدادات التقارير</h3>
          <div className="setting-row checkbox">
            <input 
              type="checkbox" 
              id="generatePdf" 
              checked={settings.generatePdf} 
              onChange={(e) => handleSettingsChange('generatePdf', e.target.checked)} 
            />
            <label htmlFor="generatePdf">توليد تقرير PDF</label>
          </div>
        </div>
        
        <button className="save-settings">حفظ الإعدادات</button>
      </div>
    </div>
  );

  // مكون السجل
  const History = () => (
    <div className="history-content">
      <h2>سجل التحليلات</h2>
      <table className="history-table">
        <thead>
          <tr>
            <th>التاريخ</th>
            <th>الرابط</th>
            <th>الدرجة</th>
            <th>المشاكل</th>
            <th>الإجراءات</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>2025-03-29 14:30</td>
            <td>https://example.com</td>
            <td>78%</td>
            <td>
              <span className="badge critical">5</span>
              <span className="badge warning">12</span>
            </td>
            <td>
              <button className="view-btn"><i className="fas fa-eye"></i></button>
              <button className="export-btn"><i className="fas fa-download"></i></button>
              <button className="delete-btn"><i className="fas fa-trash"></i></button>
            </td>
          </tr>
          <tr>
            <td>2025-03-28 09:15</td>
            <td>https://blog.example.com</td>
            <td>92%</td>
            <td>
              <span className="badge critical">1</span>
              <span className="badge warning">4</span>
            </td>
            <td>
              <button className="view-btn"><i className="fas fa-eye"></i></button>
              <button className="export-btn"><i className="fas fa-download"></i></button>
              <button className="delete-btn"><i className="fas fa-trash"></i></button>
            </td>
          </tr>
          <tr>
            <td>2025-03-25 16:45</td>
            <td>https://store.example.com</td>
            <td>65%</td>
            <td>
              <span className="badge critical">8</span>
              <span className="badge warning">15</span>
            </td>
            <td>
              <button className="view-btn"><i className="fas fa-eye"></i></button>
              <button className="export-btn"><i className="fas fa-download"></i></button>
              <button className="delete-btn"><i className="fas fa-trash"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );

  // مكون المساعدة
  const Help = () => (
    <div className="help-content">
      <h2>مركز المساعدة</h2>
      <div className="faq-section">
        <h3>الأسئلة الشائعة</h3>
        <div className="faq-item">
          <div className="faq-question">
            <h4>ما هي أداة RSEO؟</h4>
            <i className="fas fa-chevron-down"></i>
          </div>
          <div className="faq-answer">
            <p>RSEO هي أداة شاملة لتحليل وتحسين السيو (SEO) للمواقع الإلكترونية. تقوم الأداة بفحص العديد من عوامل السيو وتقديم توصيات محددة لتحسين ترتيب موقعك في محركات البحث.</p>
          </div>
        </div>
        <div className="faq-item">
          <div className="faq-question">
            <h4>كيف يمكنني إصلاح مشاكل السيو تلقائياً؟</h4>
            <i className="fas fa-chevron-down"></i>
          </div>
          <div className="faq-answer">
            <p>يمكنك تفعيل خيار "إصلاح المشاكل تلقائياً" في الإعدادات. ستقوم الأداة بإصلاح المشاكل التي يمكن إصلاحها تلقائياً مثل تحسين الصور وإضافة العلامات الوصفية المفقودة.</p>
          </div>
        </div>
        <div className="faq-item">
          <div className="faq-question">
            <h4>ما هي مؤشرات Core Web Vitals؟</h4>
            <i className="fas fa-chevron-down"></i>
          </div>
          <div className="faq-answer">
            <p>Core Web Vitals هي مجموعة من المؤشرات التي تقيس تجربة المستخدم على موقعك الإلكتروني. تشمل هذه المؤشرات: Largest Contentful Paint (LCP)، First Input Delay (FID)، و Cumulative Layout Shift (CLS). هذه المؤشرات تؤثر على ترتيب موقعك في محركات البحث.</p>
          </div>
        </div>
      </div>
      <div className="help-links">
        <h3>روابط مفيدة</h3>
        <ul>
          <li><a href="#"><i className="fas fa-book"></i> دليل المستخدم</a></li>
          <li><a href="#"><i className="fas fa-video"></i> فيديوهات تعليمية</a></li>
          <li><a href="#"><i className="fas fa-graduation-cap"></i> مركز تعليم السيو</a></li>
          <li><a href="#"><i className="fas fa-envelope"></i> اتصل بنا</a></li>
        </ul>
      </div>
    </div>
  );

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'results' && <Results />}
        {activeTab === 'settings' && <Settings />}
        {activeTab === 'history' && <History />}
        {activeTab === 'help' && <Help />}
      </div>
    </div>
  );
};

// عرض التطبيق في DOM
ReactDOM.render(<App />, document.getElementById('root'));
