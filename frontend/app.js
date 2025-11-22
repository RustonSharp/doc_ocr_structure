const API_BASE_URL = window.API_BASE_URL || "http://localhost:8000";

const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const fileLabel = document.getElementById("fileLabel");
const imagePreview = document.getElementById("imagePreview");
const previewBox = document.getElementById("previewBox");
const statusMessage = document.getElementById("statusMessage");
const processedPreview = document.getElementById("processedPreview");
const processedPlaceholder = document.getElementById("processedPlaceholder");
const ocrResultViewer = document.getElementById("ocrResult");
const llmResultViewer = document.getElementById("llmResult");
const langText = document.getElementById("langText");

let objectUrl;

const batchModeCheckbox = document.getElementById("batchMode");

// 语言切换函数
function toggleLanguage() {
    const newLang = currentLang === 'zh' ? 'en' : 'zh';
    setLanguage(newLang);
    if (langText) {
        langText.textContent = newLang === 'zh' ? '中文' : 'English';
    }
}

// 监听语言变化事件
window.addEventListener('languageChanged', () => {
    // 更新动态文本
    updateDynamicTexts();
});

// 更新动态文本
function updateDynamicTexts() {
    if (batchModeCheckbox && batchModeCheckbox.checked) {
        fileLabel.textContent = t('fileLabelBatch');
    } else {
        fileLabel.textContent = t('fileLabel');
    }
}

// 确保元素存在后再添加事件监听
if (batchModeCheckbox) {
    batchModeCheckbox.addEventListener("change", handleBatchModeChange);
}

fileInput.addEventListener("change", handleFileChange);
uploadForm.addEventListener("submit", handleFormSubmit);

// 初始化语言按钮文本
if (langText) {
    langText.textContent = currentLang === 'zh' ? '中文' : 'English';
}

function handleBatchModeChange(event) {
    const isBatch = event.target.checked;
    const fileInputEl = document.getElementById("fileInput");
    
    if (!fileInputEl) return;
    
    if (isBatch) {
        fileInputEl.setAttribute("multiple", "multiple");
        fileLabel.textContent = t('fileLabelBatch');
    } else {
        fileInputEl.removeAttribute("multiple");
        fileLabel.textContent = t('fileLabel');
    }
    
    // 清空文件选择
    fileInputEl.value = "";
    
    // 重置预览
    resetPreview();
}

function handleFileChange(event) {
    const files = event.target.files;
    if (!files || files.length === 0) {
        resetPreview();
        return;
    }

    const isBatch = batchModeCheckbox && batchModeCheckbox.checked;
    
    if (isBatch) {
        // 批量模式：显示文件列表
        const fileList = Array.from(files).map(f => f.name).join(", ");
        fileLabel.textContent = t('fileSelectedBatch', {
            count: files.length,
            list: fileList.substring(0, 100) + (fileList.length > 100 ? "..." : "")
        });
        
        // 隐藏单文件预览
        imagePreview.hidden = true;
        const placeholder = previewBox.querySelector(".placeholder");
        if (placeholder) {
            placeholder.textContent = t('fileSelectedBatchPlaceholder', { count: files.length });
            placeholder.removeAttribute("hidden");
        }
    } else {
        // 单文件模式：显示第一个文件的预览
        const file = files[0];
        fileLabel.textContent = t('fileSelected', { name: file.name });

        // 如果是 PDF 文件，显示提示信息
        if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
            }
            imagePreview.hidden = true;
            const placeholder = previewBox.querySelector(".placeholder");
            if (placeholder) {
                placeholder.textContent = t('pdfPreview');
                placeholder.removeAttribute("hidden");
            }
        } else {
            // 图片文件正常预览
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
            }
            objectUrl = URL.createObjectURL(file);

            imagePreview.src = objectUrl;
            imagePreview.hidden = false;
            previewBox.querySelector(".placeholder")?.setAttribute("hidden", "true");
        }
    }
}

async function handleFormSubmit(event) {
    event.preventDefault();

    const files = fileInput.files;
    if (!files || files.length === 0) {
        setStatus(t('pleaseSelectFile'), "error");
        return;
    }

    const isBatch = batchModeCheckbox && batchModeCheckbox.checked;
    
    console.log("提交表单，批量模式:", isBatch, "文件数量:", files.length); // 调试信息
    
    if (isBatch) {
        // 批量处理
        await handleBatchProcess();
    } else {
        // 单文件处理
        await handleSingleProcess();
    }
}

async function handleSingleProcess() {
    setStatus(t('uploading'), "info");
    uploadForm.querySelector("button").disabled = true;

    try {
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        // 检查 API 连接
        try {
            const healthCheck = await fetch(`${API_BASE_URL}/health`, { 
                method: "GET",
                signal: AbortSignal.timeout(3000) // 3秒超时
            });
            if (!healthCheck.ok) {
                throw new Error(t('backendError', { status: healthCheck.status }));
            }
        } catch (healthError) {
            if (healthError.name === "TimeoutError" || 
                healthError.message.includes("Failed to fetch") || 
                healthError.message.includes("NetworkError")) {
                throw new Error(t('connectionError', { url: API_BASE_URL }));
            }
            throw healthError;
        }

        const response = await fetch(`${API_BASE_URL}/ocr`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const text = await response.text();
            let errorMsg = t('requestFailed', { status: response.status });
            try {
                const errorJson = JSON.parse(text);
                errorMsg = errorJson.detail || errorJson.message || errorMsg;
            } catch {
                errorMsg = text || errorMsg;
            }
            throw new Error(errorMsg);
        }

        const data = await response.json();
        
        // 保存文件信息（用于重新生成输出文件）
        const fileName = fileInput.files[0]?.name || "image";
        const baseName = fileName.replace(/\.[^/.]+$/, ""); // 移除扩展名
        currentFileInfo = {
            filename: fileName,
            base_name: baseName,
            output_dir: `output/${baseName}`,
            ocr_result: data.result?.ocr_result || data?.ocr_result,
            is_pdf: false,
            page_number: null
        };
        
        renderResults(data);
        setStatus(t('completed'), "success");
    } catch (error) {
        console.error("详细错误信息：", error);
        let errorMessage = error.message;
        
        // 提供更友好的错误提示
        if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
            errorMessage = t('connectionErrorShort', { url: API_BASE_URL });
        }
        
        setStatus(errorMessage, "error");
    } finally {
        uploadForm.querySelector("button").disabled = false;
    }
}

async function handleBatchProcess() {
    const files = fileInput.files;
    if (!files || files.length === 0) {
        setStatus(t('pleaseSelectFile'), "error");
        return;
    }

    setStatus(t('processing', { count: files.length }), "info");
    uploadForm.querySelector("button").disabled = true;

    try {
        // 检查 API 连接
        try {
            const healthCheck = await fetch(`${API_BASE_URL}/health`, { 
                method: "GET",
                signal: AbortSignal.timeout(3000)
            });
            if (!healthCheck.ok) {
                throw new Error(t('backendError', { status: healthCheck.status }));
            }
        } catch (healthError) {
            if (healthError.name === "TimeoutError" || 
                healthError.message.includes("Failed to fetch") || 
                healthError.message.includes("NetworkError")) {
                throw new Error(t('connectionErrorShort', { url: API_BASE_URL }));
            }
            throw healthError;
        }

        const formData = new FormData();
        // FastAPI 的批量接口期望参数名为 "files"
        for (let i = 0; i < files.length; i++) {
            formData.append("files", files[i]);
        }
        
        console.log("准备上传文件，数量:", files.length); // 调试信息

        const response = await fetch(`${API_BASE_URL}/batch`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const text = await response.text();
            let errorMsg = t('requestFailed', { status: response.status });
            try {
                const errorJson = JSON.parse(text);
                errorMsg = errorJson.detail || errorJson.message || errorMsg;
            } catch {
                errorMsg = text || errorMsg;
            }
            throw new Error(errorMsg);
        }

        const data = await response.json();
        renderBatchResults(data);
        setStatus(t('batchCompleted', { successful: data.successful, failed: data.failed }), "success");
    } catch (error) {
        console.error("批量处理错误：", error);
        let errorMessage = error.message;
        
        if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
            errorMessage = t('connectionErrorShort', { url: API_BASE_URL });
        }
        
        setStatus(errorMessage, "error");
    } finally {
        uploadForm.querySelector("button").disabled = false;
    }
}

function renderBatchResults(data) {
    const batchBlock = document.getElementById("batchResultsBlock");
    const batchSummary = document.getElementById("batchSummary");
    const batchDetails = document.getElementById("batchDetails");
    
    batchBlock.style.display = "block";
    
    // 显示统计信息
    const total = data.total_files || 0;
    const successful = data.successful || 0;
    const failed = data.failed || 0;
    const successRate = total > 0 ? ((successful / total) * 100).toFixed(1) : 0;
    
    batchSummary.innerHTML = `
        <div class="batch-stats">
            <div class="stat-item">
                <span class="stat-label">${t('totalFiles')}</span>
                <span class="stat-value">${total}</span>
            </div>
            <div class="stat-item success">
                <span class="stat-label">${t('success')}</span>
                <span class="stat-value">${successful}</span>
            </div>
            <div class="stat-item error">
                <span class="stat-label">${t('failed')}</span>
                <span class="stat-value">${failed}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">${t('successRate')}</span>
                <span class="stat-value">${successRate}%</span>
            </div>
        </div>
    `;
    
    // 显示详细信息（折叠列表）
    let detailsHtml = '<div class="batch-details-list">';
    const results = data.results || [];
    
    results.forEach((result, index) => {
        const isSuccess = result.status === "success";
        const statusClass = isSuccess ? "success" : "error";
        const statusIcon = isSuccess ? "✓" : "✗";
        const itemId = `batch-item-${index}`;
        const contentId = `batch-content-${index}`;
        
        detailsHtml += `
            <div class="batch-item ${statusClass}">
                <div class="batch-item-header" onclick="toggleBatchItem('${contentId}')">
                    <span class="batch-item-status">${statusIcon}</span>
                    <span class="batch-item-name">${result.filename || `文件 ${index + 1}`}</span>
                    ${result.page ? `<span class="batch-item-page">${t('pageNumber', { num: result.page })}</span>` : ""}
                    <span class="batch-item-toggle" id="toggle-${contentId}">▼</span>
                </div>
                <div class="batch-item-content collapsed" id="${contentId}">
        `;
        
        if (isSuccess && result.result) {
            // 展示完整结果（像单文件一样）
            const fullResult = result.result;
            detailsHtml += renderBatchItemDetails(fullResult, index);
        } else if (result.error) {
            detailsHtml += `
                <div class="error-message">错误: ${result.error}</div>
            `;
        }
        
        detailsHtml += `
                </div>
            </div>
        `;
    });
    
    detailsHtml += '</div>';
    batchDetails.innerHTML = detailsHtml;
    
    // 存储批量结果数据
    window.batchResultsData = results;
}

function renderBatchItemDetails(fullResult, index) {
    const structuredResult = fullResult.structured_result || fullResult;
    const ocrResult = fullResult.ocr_result;
    const preProcessedImage = fullResult.pre_processed_image;
    
    let html = '';
    
    // 1. 预处理后的图片
    if (preProcessedImage) {
        const normalized = normalizeImageData(preProcessedImage);
        if (normalized) {
            html += `
                <div class="batch-detail-section">
                    <h4>预处理后的图片</h4>
                    <div class="batch-image-preview">
                        <img src="${normalized}" alt="预处理图片" style="max-width: 100%; height: auto; border-radius: 8px;">
                    </div>
                </div>
            `;
        }
    }
    
    // 2. OCR 识别结果
    if (ocrResult) {
        html += `
            <div class="batch-detail-section">
                <h4>OCR 识别结果</h4>
                <pre class="batch-json-viewer">${JSON.stringify(ocrResult, null, 2)}</pre>
            </div>
        `;
    }
    
    // 3. 结构化结果
    if (structuredResult && structuredResult.structured_data) {
        html += renderStructuredResultForBatch(structuredResult, `batch-${index}`);
    }
    
    return html;
}

function renderStructuredResultForBatch(structuredData, prefix) {
    if (!structuredData || !structuredData.structured_data) {
        return `<div class="batch-detail-section"><p>${t('noResult')}</p></div>`;
    }
    
    const fields = structuredData.structured_data.fields || {};
    const validationList = structuredData.structured_data.validation_list || [];
    const coverage = structuredData.structured_data.coverage || 0;
    
    let html = `
        <div class="batch-detail-section">
            <h4>结构化结果</h4>
            <div class="coverage-info">字段覆盖率: <strong>${coverage.toFixed(2)}%</strong></div>
            <table class="fields-table">
                <thead>
                    <tr>
                        <th>字段名</th>
                        <th>字段值</th>
                        <th>置信度</th>
                        <th>数据来源</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    for (const [fieldName, fieldInfo] of Object.entries(fields)) {
        const confidence = fieldInfo.confidence || 0;
        const value = fieldInfo.value !== null && fieldInfo.value !== undefined ? String(fieldInfo.value) : "";
        const source = fieldInfo.source || "unknown";
        const needsValidation = fieldInfo.needs_validation || false;
        const statusClass = needsValidation ? "needs-validation" : "valid";
        const statusText = needsValidation ? "需校验" : "正常";
        
        html += `
            <tr class="${statusClass}">
                <td><strong>${fieldName}</strong></td>
                <td>${escapeHtml(value) || "<em>未提取</em>"}</td>
                <td><span class="confidence ${confidence <= 80 ? 'low' : confidence <= 90 ? 'medium' : 'high'}">${confidence.toFixed(2)}%</span></td>
                <td>${source}</td>
                <td>${statusText}</td>
            </tr>
        `;
    }
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    // 4. 待校验字段清单
    if (validationList.length > 0) {
        html += `
            <div class="batch-detail-section">
                <h4>待校验字段清单</h4>
                <ul class="validation-list">
        `;
        for (const fieldName of validationList) {
            const fieldInfo = fields[fieldName] || {};
            html += `
                <li>
                    <strong>${fieldName}</strong>: ${escapeHtml(String(fieldInfo.value || "未提取"))} 
                    (置信度: ${(fieldInfo.confidence || 0).toFixed(2)}%)
                </li>
            `;
        }
        html += `
                </ul>
            </div>
        `;
    } else {
        html += `
            <div class="batch-detail-section">
                <h4>待校验字段清单</h4>
                <p class="no-validation">所有字段置信度均高于 80%，无需人工校验。</p>
            </div>
        `;
    }
    
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 切换批量处理项的展开/折叠
window.toggleBatchItem = function(contentId) {
    const contentDiv = document.getElementById(contentId);
    const toggleIcon = document.getElementById(`toggle-${contentId}`);
    
    if (contentDiv) {
        const isCollapsed = contentDiv.classList.contains("collapsed");
        if (isCollapsed) {
            contentDiv.classList.remove("collapsed");
            if (toggleIcon) toggleIcon.textContent = "▲";
        } else {
            contentDiv.classList.add("collapsed");
            if (toggleIcon) toggleIcon.textContent = "▼";
        }
    }
};

let currentStructuredData = null;
let pdfResults = null; // 存储 PDF 多页结果
let currentPageIndex = 0; // 当前显示的页面索引
let currentFileInfo = null; // 存储当前处理的文件信息（用于重新生成输出文件）

function renderResults(data) {
    console.log("收到数据:", data); // 调试信息
    
    // 处理 PDF 多页结果
    if (data.file_type === "pdf" && data.results) {
        console.log("检测到 PDF 文件，总页数:", data.total_pages); // 调试信息
        pdfResults = data.results;
        currentPageIndex = 0;
        
        // 保存文件信息（用于重新生成输出文件）
        const fileName = fileInput.files[0]?.name || "pdf";
        const baseName = fileName.replace(/\.[^/.]+$/, ""); // 移除扩展名
        currentFileInfo = {
            filename: fileName,
            base_name: baseName,
            output_dir: `output/${baseName}_page_1`,
            ocr_result: data.results[0]?.ocr_result,
            is_pdf: true,
            page_number: 1
        };
        
        // 显示页面选择器
        renderPdfPageSelector(data.total_pages);
        
        // 显示第一页结果
        renderPdfPage(0);
    } else if (data.result) {
        // 单图片结果
        // 隐藏 PDF 页面选择器
        const selector = document.getElementById("pdfPageSelector");
        if (selector) selector.style.display = "none";
        
        // 保存文件信息（用于重新生成输出文件）
        const fileName = fileInput.files[0]?.name || "image";
        const baseName = fileName.replace(/\.[^/.]+$/, ""); // 移除扩展名
        currentFileInfo = {
            filename: fileName,
            base_name: baseName,
            output_dir: `output/${baseName}`,
            ocr_result: data.result?.ocr_result,
            is_pdf: false,
            page_number: null
        };
        
        renderProcessedPreview(data.result?.pre_processed_image);
        renderJsonView(ocrResultViewer, data.result?.ocr_result, t('noResult'));
        renderStructuredResult(data.result?.structured_result);
        currentStructuredData = data.result?.structured_result;
    } else {
        // 兼容旧格式
        // 隐藏 PDF 页面选择器
        const selector = document.getElementById("pdfPageSelector");
        if (selector) selector.style.display = "none";
        
        // 保存文件信息（用于重新生成输出文件）
        const fileName = fileInput.files[0]?.name || "image";
        const baseName = fileName.replace(/\.[^/.]+$/, ""); // 移除扩展名
        currentFileInfo = {
            filename: fileName,
            base_name: baseName,
            output_dir: `output/${baseName}`,
            ocr_result: data?.ocr_result,
            is_pdf: false,
            page_number: null
        };
        
        renderProcessedPreview(data?.pre_processed_image);
        renderJsonView(ocrResultViewer, data?.ocr_result, t('noResult'));
        renderStructuredResult(data?.structured_result || data?.structured_ocr_result);
        currentStructuredData = data?.structured_result || data?.structured_ocr_result;
    }
}

function renderPdfPageSelector(totalPages) {
    const selector = document.getElementById("pdfPageSelector");
    const pageSelect = document.getElementById("pageSelect");
    const pageInfo = document.getElementById("pageInfo");
    
    if (!selector || !pageSelect || !pageInfo) {
        console.error("页面选择器元素不存在");
        return;
    }
    
    // 显示页面选择器区域（即使只有一页也显示）
    selector.style.display = "block";
    
    if (totalPages > 1) {
        // 多页 PDF：显示下拉选择器
        pageSelect.style.display = "inline-block";
        pageSelect.innerHTML = "";
        for (let i = 1; i <= totalPages; i++) {
            const option = document.createElement("option");
            option.value = i - 1;
            option.textContent = t('pageNumber', { num: i });
            pageSelect.appendChild(option);
        }
        
        pageSelect.value = 0;
        pageInfo.textContent = t('pageInfo', { count: totalPages });
        
        // 添加页面切换事件
        pageSelect.onchange = function() {
            const pageIndex = parseInt(this.value);
            renderPdfPage(pageIndex);
        };
    } else {
        // 单页 PDF：只显示页面信息，隐藏选择器
        pageSelect.style.display = "none";
        pageInfo.textContent = t('pageInfo', { count: totalPages });
    }
}

function renderPdfPage(pageIndex) {
    if (!pdfResults || !pdfResults[pageIndex]) {
        console.error("PDF 页面数据不存在，pageIndex:", pageIndex);
        return;
    }
    
    console.log("渲染 PDF 页面:", pageIndex, pdfResults[pageIndex]); // 调试信息
    
    currentPageIndex = pageIndex;
    const pageResult = pdfResults[pageIndex];
    
    // 更新页面选择器
    const pageSelect = document.getElementById("pageSelect");
    if (pageSelect) {
        pageSelect.value = pageIndex;
    }
    
    // 更新文件信息（用于重新生成输出文件）
    if (currentFileInfo && currentFileInfo.is_pdf) {
        const pageNumber = pageResult?.page_number || (pageIndex + 1);
        const baseName = currentFileInfo.filename.replace(/\.[^/.]+$/, ""); // 移除扩展名
        currentFileInfo.page_number = pageNumber;
        currentFileInfo.base_name = `${baseName}_page_${pageNumber}`;
        currentFileInfo.output_dir = `output/${currentFileInfo.base_name}`;
        currentFileInfo.ocr_result = pageResult?.ocr_result;
    }
    
    // 显示该页的图片和数据
    renderProcessedPreview(pageResult?.pre_processed_image);
    renderJsonView(ocrResultViewer, pageResult?.ocr_result, t('noResult'));
    renderStructuredResult(pageResult?.structured_result);
    currentStructuredData = pageResult?.structured_result;
}

function renderStructuredResult(structuredData) {
    const container = document.getElementById("structuredResult");
    const validationContainer = document.getElementById("validationList");
    const editorContainer = document.getElementById("editableFields");
    const regenerateBtn = document.getElementById("regenerateBtn");
    
    if (!structuredData || !structuredData.structured_data) {
        container.textContent = t('noResult');
        validationContainer.textContent = t('noValidation');
        return;
    }
    
    const fields = structuredData.structured_data.fields || {};
    const validationList = structuredData.structured_data.validation_list || [];
    const coverage = structuredData.structured_data.coverage || 0;
    
    // 渲染结构化数据（带置信度）
    let html = `<div class="coverage-info">${t('coverage', { rate: coverage.toFixed(2) })}</div>`;
    html += `<table class="fields-table"><thead><tr><th>${t('fieldName')}</th><th>${t('fieldValue')}</th><th>${t('confidence')}</th><th>${t('dataSource')}</th><th>${t('status')}</th></tr></thead><tbody>`;
    
    for (const [fieldName, fieldInfo] of Object.entries(fields)) {
        const confidence = fieldInfo.confidence || 0;
        const value = fieldInfo.value !== null && fieldInfo.value !== undefined ? String(fieldInfo.value) : "";
        const source = fieldInfo.source || "unknown";
        const needsValidation = fieldInfo.needs_validation || false;
        const statusClass = needsValidation ? "needs-validation" : "valid";
        const statusText = needsValidation ? t('needsValidation') : t('normal');
        
        html += `<tr class="${statusClass}">
            <td><strong>${fieldName}</strong></td>
            <td>${value || `<em>${t('notExtracted')}</em>`}</td>
            <td><span class="confidence ${confidence <= 80 ? 'low' : confidence <= 90 ? 'medium' : 'high'}">${confidence.toFixed(2)}%</span></td>
            <td>${source}</td>
            <td>${statusText}</td>
        </tr>`;
    }
    
    html += '</tbody></table>';
    container.innerHTML = html;
    
    // 渲染校验清单
    if (validationList.length > 0) {
        let validationHtml = '<ul class="validation-list">';
        for (const fieldName of validationList) {
            const fieldInfo = fields[fieldName] || {};
            validationHtml += `<li>
                <strong>${fieldName}</strong>: ${fieldInfo.value || `<em>${t('notExtracted')}</em>`} 
                (${t('confidence')}: ${(fieldInfo.confidence || 0).toFixed(2)}%)
            </li>`;
        }
        validationHtml += '</ul>';
        validationContainer.innerHTML = validationHtml;
    } else {
        validationContainer.innerHTML = `<p class="no-validation">${t('allFieldsValid')}</p>`;
    }
    
    // 渲染可编辑字段
    let editorHtml = `<table class="editor-table"><thead><tr><th>${t('fieldName')}</th><th>${t('currentValue')}</th><th>${t('correctionValue')}</th></tr></thead><tbody>`;
    for (const [fieldName, fieldInfo] of Object.entries(fields)) {
        const currentValue = fieldInfo.value !== null && fieldInfo.value !== undefined ? String(fieldInfo.value) : "";
        editorHtml += `<tr>
            <td><strong>${fieldName}</strong></td>
            <td>${currentValue || `<em>${t('notExtracted')}</em>`}</td>
            <td><input type="text" data-field="${fieldName}" value="${currentValue}" placeholder="${t('inputCorrection')}"></td>
        </tr>`;
    }
    editorHtml += '</tbody></table>';
    editorContainer.innerHTML = editorHtml;
    regenerateBtn.style.display = "block";
}

// 重新生成结构化结果
document.getElementById("regenerateBtn")?.addEventListener("click", async function() {
    if (!currentStructuredData) {
        setStatus(t('noStructuredData'), "error");
        return;
    }
    
    if (!currentFileInfo) {
        setStatus(t('noFileInfo'), "error");
        return;
    }
    
    const inputs = document.querySelectorAll("#editableFields input[data-field]");
    const corrections = {};
    inputs.forEach(input => {
        const fieldName = input.dataset.field;
        const correctedValue = input.value.trim();
        if (correctedValue && correctedValue !== String(currentStructuredData.structured_data.fields[fieldName]?.value || "")) {
            corrections[fieldName] = correctedValue;
        }
    });
    
    if (Object.keys(corrections).length === 0) {
        setStatus(t('noCorrections'), "info");
        return;
    }
    
    setStatus(t('regenerating'), "info");
    const regenerateBtn = document.getElementById("regenerateBtn");
    if (regenerateBtn) regenerateBtn.disabled = true;
    
    try {
        // 应用修正
        const updatedData = JSON.parse(JSON.stringify(currentStructuredData));
        for (const [fieldName, correctedValue] of Object.entries(corrections)) {
            if (updatedData.structured_data.fields[fieldName]) {
                updatedData.structured_data.fields[fieldName].value = correctedValue;
                updatedData.structured_data.fields[fieldName].confidence = 100.0; // 人工修正后置信度为 100%
                updatedData.structured_data.fields[fieldName].source = "manual";
                updatedData.structured_data.fields[fieldName].needs_validation = false;
            }
        }
        
        // 更新校验清单
        updatedData.structured_data.validation_list = Object.entries(updatedData.structured_data.fields)
            .filter(([_, info]) => info.needs_validation)
            .map(([name, _]) => name);
        
        // 调用后端API重新生成输出文件
        const response = await fetch(`${API_BASE_URL}/regenerate`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                structured_result: updatedData,
                output_dir: currentFileInfo.output_dir,
                base_name: currentFileInfo.base_name,
                ocr_result: currentFileInfo.ocr_result,
            }),
        });
        
        if (!response.ok) {
            let errorMsg = t('regenerateFailed');
            try {
                const errorText = await response.text();
                if (errorText) {
                    try {
                        const errorJson = JSON.parse(errorText);
                        errorMsg = errorJson.detail || errorJson.message || errorMsg;
                    } catch {
                        // 如果不是JSON，直接使用文本
                        errorMsg = errorText;
                    }
                }
            } catch (e) {
                console.error("解析错误响应失败:", e);
                errorMsg = t('regenerateFailed') + ` (${response.status})`;
            }
            throw new Error(errorMsg);
        }
        
        const result = await response.json();
        console.log("重新生成成功:", result);
        
        // 重新渲染
        renderStructuredResult(updatedData);
        currentStructuredData = updatedData;
        setStatus(t('regenerateSuccess'), "success");
    } catch (error) {
        console.error("重新生成失败:", error);
        setStatus(t('regenerateFailed') + ": " + error.message, "error");
    } finally {
        const regenerateBtn = document.getElementById("regenerateBtn");
        if (regenerateBtn) regenerateBtn.disabled = false;
    }
});

function renderProcessedPreview(imageData) {
    const normalized = normalizeImageData(imageData);
    if (normalized) {
        processedPreview.src = normalized;
        processedPreview.hidden = false;
        processedPlaceholder.textContent = t('waiting');
        processedPlaceholder.hidden = true;
    } else {
        processedPreview.hidden = true;
        processedPlaceholder.hidden = false;
        processedPlaceholder.textContent = t('waiting');
    }
}

function renderJsonView(targetEl, value, fallback) {
    if (!value) {
        targetEl.textContent = fallback;
        return;
    }
    try {
        const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
        const parsed = typeof value === "string" ? JSON.parse(value) : value;
        targetEl.textContent = JSON.stringify(parsed, null, 2);
    } catch {
        targetEl.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    }
}

function normalizeImageData(raw) {
    if (!raw || typeof raw !== "string") {
        return null;
    }
    const trimmed = raw.trim();
    if (!trimmed) return null;
    if (trimmed.startsWith("data:")) {
        return trimmed;
    }
    const base64Text = trimmed.replace(/\s/g, "");
    const base64Pattern = /^[A-Za-z0-9+/=]+$/;
    if (base64Pattern.test(base64Text)) {
        return `data:image/png;base64,${base64Text}`;
    }
    return trimmed;
}

function setStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type || ""}`;
}

function resetPreview() {
    fileLabel.textContent = t('fileLabel');
    imagePreview.hidden = true;
    const placeholder = previewBox.querySelector(".placeholder");
    if (placeholder) {
        placeholder.textContent = t('previewPlaceholder');
        placeholder.removeAttribute("hidden");
    }
    if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
        objectUrl = undefined;
    }
    
    // 重置 PDF 相关状态
    pdfResults = null;
    currentPageIndex = 0;
    document.getElementById("pdfPageSelector").style.display = "none";
}

