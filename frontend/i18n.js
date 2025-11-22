// 国际化资源文件
const i18n = {
    zh: {
        // 页面标题和描述
        title: "文档 OCR 测试台",
        description: "上传一张发票/文档图片，调用后端 <code>/ocr</code> 接口完成识别及结构化。",
        
        // 上传区域
        batchMode: "批量处理模式（可同时上传多个文件）",
        fileLabel: "点击或拖拽图片/PDF到此处",
        fileLabelBatch: "点击或拖拽多个图片/PDF到此处（批量处理）",
        fileSelected: "已选择: {name}",
        fileSelectedBatch: "已选择 {count} 个文件: {list}",
        fileSelectedBatchPlaceholder: "已选择 {count} 个文件，点击\"开始识别\"进行批量处理",
        pdfPreview: "PDF 文件将在处理完成后显示转换后的图片",
        previewPlaceholder: "选择文件后会显示预览",
        startRecognition: "开始识别",
        
        // 结果面板
        apiResponse: "接口返回",
        apiResponseDesc: "展示 FastAPI <code>POST /ocr</code> 返回的数据。",
        preprocessedImage: "预处理后的图片",
        ocrResult: "OCR 识别结果",
        structuredResult: "结构化结果",
        validationList: "待校验字段清单",
        fieldEditor: "字段修正",
        fieldEditorDesc: "在下方修正字段值后，点击\"重新生成\"按钮",
        regenerate: "重新生成结构化结果",
        batchResults: "批量处理结果",
        
        // 状态消息
        uploading: "正在上传并识别，请稍候...",
        processing: "正在批量处理 {count} 个文件，请稍候...",
        completed: "识别完成",
        batchCompleted: "批量处理完成：成功 {successful} 个，失败 {failed} 个",
        pleaseSelectFile: "请先选择文件",
        waiting: "等待接口返回...",
        noResult: "未返回结构化结果",
        noValidation: "无校验清单",
        allFieldsValid: "所有字段置信度均高于 80%，无需人工校验。",
        
        // 批量处理
        totalFiles: "总文件数:",
        success: "成功:",
        failed: "失败:",
        successRate: "成功率:",
        selectPage: "选择页面:",
        pageInfo: "共 {count} 页",
        pageNumber: "第 {num} 页",
        
        // 字段相关
        fieldName: "字段名",
        fieldValue: "字段值",
        confidence: "置信度",
        dataSource: "数据来源",
        status: "状态",
        needsValidation: "需校验",
        normal: "正常",
        notExtracted: "未提取",
        coverage: "字段覆盖率: {rate}%",
        inputCorrection: "输入修正值",
        currentValue: "当前值",
        correctionValue: "修正值",
        previewTitle: "原始文件预览",
        
        // 错误消息
        requestFailed: "请求失败 ({status})",
        backendError: "后端服务响应异常 ({status})",
        connectionError: "无法连接到后端服务 ({url})\n\n请检查：\n1. 后端服务是否已启动？运行命令：python main.py\n2. 服务地址是否正确？\n3. 如果直接打开 HTML 文件，请使用 HTTP 服务器访问\n\n提示：可以使用 start.bat (Windows) 或 start.sh (Linux/Mac) 一键启动服务",
        connectionErrorShort: "无法连接到后端服务 ({url})\n\n请检查：\n1. 后端服务是否已启动？运行命令：python main.py\n2. 服务地址是否正确？",
        
        // 重新生成相关
        noStructuredData: "没有结构化数据",
        noFileInfo: "没有文件信息，无法重新生成输出文件",
        noCorrections: "没有需要修正的字段",
        regenerating: "正在重新生成输出文件...",
        regenerateSuccess: "输出文件已重新生成",
        regenerateFailed: "重新生成输出文件失败"
    },
    en: {
        // Page titles and descriptions
        title: "Document OCR Test Platform",
        description: "Upload an invoice/document image and call the backend <code>/ocr</code> endpoint to complete recognition and structuring.",
        
        // Upload area
        batchMode: "Batch processing mode (can upload multiple files at once)",
        fileLabel: "Click or drag image/PDF here",
        fileLabelBatch: "Click or drag multiple images/PDFs here (batch processing)",
        fileSelected: "Selected: {name}",
        fileSelectedBatch: "Selected {count} files: {list}",
        fileSelectedBatchPlaceholder: "Selected {count} files, click \"Start Recognition\" for batch processing",
        pdfPreview: "PDF file will display converted image after processing",
        previewPlaceholder: "Preview will be shown after selecting a file",
        startRecognition: "Start Recognition",
        
        // Results panel
        apiResponse: "API Response",
        apiResponseDesc: "Display data returned by FastAPI <code>POST /ocr</code> endpoint.",
        preprocessedImage: "Preprocessed Image",
        ocrResult: "OCR Recognition Result",
        structuredResult: "Structured Result",
        validationList: "Validation List",
        fieldEditor: "Field Correction",
        fieldEditorDesc: "Correct field values below, then click \"Regenerate\" button",
        regenerate: "Regenerate Structured Result",
        batchResults: "Batch Processing Results",
        
        // Status messages
        uploading: "Uploading and recognizing, please wait...",
        processing: "Processing {count} files in batch, please wait...",
        completed: "Recognition completed",
        batchCompleted: "Batch processing completed: {successful} succeeded, {failed} failed",
        pleaseSelectFile: "Please select a file first",
        waiting: "Waiting for API response...",
        noResult: "No structured result returned",
        noValidation: "No validation list",
        allFieldsValid: "All fields have confidence above 80%, no manual validation needed.",
        
        // Batch processing
        totalFiles: "Total Files:",
        success: "Success:",
        failed: "Failed:",
        successRate: "Success Rate:",
        selectPage: "Select Page:",
        pageInfo: "Total {count} pages",
        pageNumber: "Page {num}",
        
        // Field related
        fieldName: "Field Name",
        fieldValue: "Field Value",
        confidence: "Confidence",
        dataSource: "Data Source",
        status: "Status",
        needsValidation: "Needs Validation",
        notExtracted: "Not Extracted",
        coverage: "Field Coverage: {rate}%",
        inputCorrection: "Enter correction value",
        
        // Error messages
        requestFailed: "Request failed ({status})",
        backendError: "Backend service response error ({status})",
        connectionError: "Cannot connect to backend service ({url})\n\nPlease check:\n1. Is the backend service running? Run: python main.py\n2. Is the service address correct?\n3. If opening HTML file directly, please use HTTP server to access\n\nTip: You can use start.bat (Windows) or start.sh (Linux/Mac) to start the service",
        connectionErrorShort: "Cannot connect to backend service ({url})\n\nPlease check:\n1. Is the backend service running? Run: python main.py\n2. Is the service address correct?",
        
        // Regenerate related
        noStructuredData: "No structured data",
        noFileInfo: "No file information, cannot regenerate output files",
        noCorrections: "No fields need correction",
        regenerating: "Regenerating output files...",
        regenerateSuccess: "Output files regenerated successfully",
        regenerateFailed: "Failed to regenerate output files"
    }
};

// 当前语言，默认中文
let currentLang = localStorage.getItem('language') || 'zh';

// 翻译函数
function t(key, params = {}) {
    const translation = i18n[currentLang][key] || key;
    
    // 替换参数
    if (Object.keys(params).length > 0) {
        return translation.replace(/\{(\w+)\}/g, (match, paramKey) => {
            return params[paramKey] !== undefined ? params[paramKey] : match;
        });
    }
    
    return translation;
}

// 切换语言
function setLanguage(lang) {
    if (i18n[lang]) {
        currentLang = lang;
        localStorage.setItem('language', lang);
        updatePageLanguage();
    }
}

// 更新页面语言
function updatePageLanguage() {
    // 更新 HTML lang 属性
    document.documentElement.lang = currentLang === 'zh' ? 'zh-CN' : 'en';
    
    // 更新所有带有 data-i18n 属性的元素
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const params = element.dataset.i18nParams ? JSON.parse(element.dataset.i18nParams) : {};
        
        if (element.tagName === 'INPUT' && element.type === 'text') {
            element.placeholder = t(key, params);
        } else if (element.tagName === 'INPUT' && element.type === 'button') {
            element.value = t(key, params);
        } else {
            element.textContent = t(key, params);
        }
    });
    
    // 更新所有带有 data-i18n-html 属性的元素（支持HTML）
    document.querySelectorAll('[data-i18n-html]').forEach(element => {
        const key = element.getAttribute('data-i18n-html');
        const params = element.dataset.i18nParams ? JSON.parse(element.dataset.i18nParams) : {};
        element.innerHTML = t(key, params);
    });
    
    // 更新标题
    document.title = t('title');
    
    // 触发自定义事件，通知其他脚本更新
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang: currentLang } }));
}

// 初始化语言
updatePageLanguage();

