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

let objectUrl;

const batchModeCheckbox = document.getElementById("batchMode");

// 确保元素存在后再添加事件监听
if (batchModeCheckbox) {
    batchModeCheckbox.addEventListener("change", handleBatchModeChange);
}

fileInput.addEventListener("change", handleFileChange);
uploadForm.addEventListener("submit", handleFormSubmit);

function handleBatchModeChange(event) {
    const isBatch = event.target.checked;
    const fileInputEl = document.getElementById("fileInput");
    
    if (!fileInputEl) return;
    
    if (isBatch) {
        fileInputEl.setAttribute("multiple", "multiple");
        fileLabel.textContent = "点击或拖拽多个图片/PDF到此处（批量处理）";
    } else {
        fileInputEl.removeAttribute("multiple");
        fileLabel.textContent = "点击或拖拽图片/PDF到此处";
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
        fileLabel.textContent = `已选择 ${files.length} 个文件: ${fileList.substring(0, 100)}${fileList.length > 100 ? "..." : ""}`;
        
        // 隐藏单文件预览
        imagePreview.hidden = true;
        const placeholder = previewBox.querySelector(".placeholder");
        if (placeholder) {
            placeholder.textContent = `已选择 ${files.length} 个文件，点击"开始识别"进行批量处理`;
            placeholder.removeAttribute("hidden");
        }
    } else {
        // 单文件模式：显示第一个文件的预览
        const file = files[0];
        fileLabel.textContent = `已选择: ${file.name}`;

        // 如果是 PDF 文件，显示提示信息
        if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
            }
            imagePreview.hidden = true;
            const placeholder = previewBox.querySelector(".placeholder");
            if (placeholder) {
                placeholder.textContent = "PDF 文件将在处理完成后显示转换后的图片";
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
        setStatus("请先选择文件", "error");
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
    setStatus("正在上传并识别，请稍候...", "info");
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
                throw new Error(`后端服务响应异常 (${healthCheck.status})`);
            }
        } catch (healthError) {
            if (healthError.name === "TimeoutError" || 
                healthError.message.includes("Failed to fetch") || 
                healthError.message.includes("NetworkError")) {
                throw new Error(`无法连接到后端服务 (${API_BASE_URL})\n\n请检查：\n1. 后端服务是否已启动？运行命令：python main.py\n2. 服务地址是否正确？\n3. 如果直接打开 HTML 文件，请使用 HTTP 服务器访问\n\n提示：可以使用 start.bat (Windows) 或 start.sh (Linux/Mac) 一键启动服务`);
            }
            throw healthError;
        }

        const response = await fetch(`${API_BASE_URL}/ocr`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const text = await response.text();
            let errorMsg = `请求失败 (${response.status})`;
            try {
                const errorJson = JSON.parse(text);
                errorMsg = errorJson.detail || errorJson.message || errorMsg;
            } catch {
                errorMsg = text || errorMsg;
            }
            throw new Error(errorMsg);
        }

        const data = await response.json();
        renderResults(data);
        setStatus("识别完成", "success");
    } catch (error) {
        console.error("详细错误信息：", error);
        let errorMessage = error.message;
        
        // 提供更友好的错误提示
        if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
            errorMessage = `无法连接到后端服务 (${API_BASE_URL})\n\n请检查：\n1. 后端服务是否已启动？运行命令：python main.py\n2. 服务地址是否正确？\n3. 如果直接打开 HTML 文件，请使用 HTTP 服务器访问`;
        }
        
        setStatus(errorMessage, "error");
    } finally {
        uploadForm.querySelector("button").disabled = false;
    }
}

async function handleBatchProcess() {
    const files = fileInput.files;
    if (!files || files.length === 0) {
        setStatus("请先选择文件", "error");
        return;
    }

    setStatus(`正在批量处理 ${files.length} 个文件，请稍候...`, "info");
    uploadForm.querySelector("button").disabled = true;

    try {
        // 检查 API 连接
        try {
            const healthCheck = await fetch(`${API_BASE_URL}/health`, { 
                method: "GET",
                signal: AbortSignal.timeout(3000)
            });
            if (!healthCheck.ok) {
                throw new Error(`后端服务响应异常 (${healthCheck.status})`);
            }
        } catch (healthError) {
            if (healthError.name === "TimeoutError" || 
                healthError.message.includes("Failed to fetch") || 
                healthError.message.includes("NetworkError")) {
                throw new Error(`无法连接到后端服务 (${API_BASE_URL})\n\n请检查：\n1. 后端服务是否已启动？运行命令：python main.py\n2. 服务地址是否正确？`);
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
            let errorMsg = `请求失败 (${response.status})`;
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
        setStatus(`批量处理完成：成功 ${data.successful} 个，失败 ${data.failed} 个`, "success");
    } catch (error) {
        console.error("批量处理错误：", error);
        let errorMessage = error.message;
        
        if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
            errorMessage = `无法连接到后端服务 (${API_BASE_URL})\n\n请检查：\n1. 后端服务是否已启动？运行命令：python main.py\n2. 服务地址是否正确？`;
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
                <span class="stat-label">总文件数:</span>
                <span class="stat-value">${total}</span>
            </div>
            <div class="stat-item success">
                <span class="stat-label">成功:</span>
                <span class="stat-value">${successful}</span>
            </div>
            <div class="stat-item error">
                <span class="stat-label">失败:</span>
                <span class="stat-value">${failed}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">成功率:</span>
                <span class="stat-value">${successRate}%</span>
            </div>
        </div>
    `;
    
    // 显示详细信息
    let detailsHtml = '<div class="batch-details-list">';
    const results = data.results || [];
    
    results.forEach((result, index) => {
        const isSuccess = result.status === "success";
        const statusClass = isSuccess ? "success" : "error";
        const statusIcon = isSuccess ? "✓" : "✗";
        
        detailsHtml += `
            <div class="batch-item ${statusClass}">
                <div class="batch-item-header">
                    <span class="batch-item-status">${statusIcon}</span>
                    <span class="batch-item-name">${result.filename || `文件 ${index + 1}`}</span>
                    ${result.page ? `<span class="batch-item-page">第 ${result.page} 页</span>` : ""}
                </div>
        `;
        
        if (isSuccess && result.result) {
            detailsHtml += `
                <div class="batch-item-content">
                    <button class="view-detail-btn" onclick="viewBatchItemDetail(${index})">
                        查看详情
                    </button>
                    <div class="batch-item-detail" id="detail-${index}" style="display:none;">
                        <div class="detail-section">
                            <h4>结构化数据</h4>
                            <div class="detail-data">${JSON.stringify(result.result.structured_result || result.result, null, 2)}</div>
                        </div>
                    </div>
                </div>
            `;
        } else if (result.error) {
            detailsHtml += `
                <div class="batch-item-content">
                    <div class="error-message">错误: ${result.error}</div>
                </div>
            `;
        }
        
        detailsHtml += '</div>';
    });
    
    detailsHtml += '</div>';
    batchDetails.innerHTML = detailsHtml;
    
    // 存储批量结果数据，供查看详情使用
    window.batchResultsData = results;
}

// 查看批量处理项的详情
window.viewBatchItemDetail = function(index) {
    const detailDiv = document.getElementById(`detail-${index}`);
    if (detailDiv) {
        detailDiv.style.display = detailDiv.style.display === "none" ? "block" : "none";
    }
};

let currentStructuredData = null;
let pdfResults = null; // 存储 PDF 多页结果
let currentPageIndex = 0; // 当前显示的页面索引

function renderResults(data) {
    console.log("收到数据:", data); // 调试信息
    
    // 处理 PDF 多页结果
    if (data.file_type === "pdf" && data.results) {
        console.log("检测到 PDF 文件，总页数:", data.total_pages); // 调试信息
        pdfResults = data.results;
        currentPageIndex = 0;
        
        // 显示页面选择器
        renderPdfPageSelector(data.total_pages);
        
        // 显示第一页结果
        renderPdfPage(0);
    } else if (data.result) {
        // 单图片结果
        // 隐藏 PDF 页面选择器
        const selector = document.getElementById("pdfPageSelector");
        if (selector) selector.style.display = "none";
        
        renderProcessedPreview(data.result?.pre_processed_image);
        renderJsonView(ocrResultViewer, data.result?.ocr_result, "未返回 OCR 结果");
        renderStructuredResult(data.result?.structured_result);
        currentStructuredData = data.result?.structured_result;
    } else {
        // 兼容旧格式
        // 隐藏 PDF 页面选择器
        const selector = document.getElementById("pdfPageSelector");
        if (selector) selector.style.display = "none";
        
        renderProcessedPreview(data?.pre_processed_image);
        renderJsonView(ocrResultViewer, data?.ocr_result, "未返回 OCR 结果");
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
            option.textContent = `第 ${i} 页`;
            pageSelect.appendChild(option);
        }
        
        pageSelect.value = 0;
        pageInfo.textContent = `共 ${totalPages} 页`;
        
        // 添加页面切换事件
        pageSelect.onchange = function() {
            const pageIndex = parseInt(this.value);
            renderPdfPage(pageIndex);
        };
    } else {
        // 单页 PDF：只显示页面信息，隐藏选择器
        pageSelect.style.display = "none";
        pageInfo.textContent = `共 ${totalPages} 页`;
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
    
    // 显示该页的图片和数据
    renderProcessedPreview(pageResult?.pre_processed_image);
    renderJsonView(ocrResultViewer, pageResult?.ocr_result, "未返回 OCR 结果");
    renderStructuredResult(pageResult?.structured_result);
    currentStructuredData = pageResult?.structured_result;
}

function renderStructuredResult(structuredData) {
    const container = document.getElementById("structuredResult");
    const validationContainer = document.getElementById("validationList");
    const editorContainer = document.getElementById("editableFields");
    const regenerateBtn = document.getElementById("regenerateBtn");
    
    if (!structuredData || !structuredData.structured_data) {
        container.textContent = "未返回结构化结果";
        validationContainer.textContent = "无校验清单";
        return;
    }
    
    const fields = structuredData.structured_data.fields || {};
    const validationList = structuredData.structured_data.validation_list || [];
    const coverage = structuredData.structured_data.coverage || 0;
    
    // 渲染结构化数据（带置信度）
    let html = `<div class="coverage-info">字段覆盖率: <strong>${coverage.toFixed(2)}%</strong></div>`;
    html += '<table class="fields-table"><thead><tr><th>字段名</th><th>字段值</th><th>置信度</th><th>数据来源</th><th>状态</th></tr></thead><tbody>';
    
    for (const [fieldName, fieldInfo] of Object.entries(fields)) {
        const confidence = fieldInfo.confidence || 0;
        const value = fieldInfo.value !== null && fieldInfo.value !== undefined ? String(fieldInfo.value) : "";
        const source = fieldInfo.source || "unknown";
        const needsValidation = fieldInfo.needs_validation || false;
        const statusClass = needsValidation ? "needs-validation" : "valid";
        const statusText = needsValidation ? "需校验" : "正常";
        
        html += `<tr class="${statusClass}">
            <td><strong>${fieldName}</strong></td>
            <td>${value || "<em>未提取</em>"}</td>
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
                <strong>${fieldName}</strong>: ${fieldInfo.value || "<em>未提取</em>"} 
                (置信度: ${(fieldInfo.confidence || 0).toFixed(2)}%)
            </li>`;
        }
        validationHtml += '</ul>';
        validationContainer.innerHTML = validationHtml;
    } else {
        validationContainer.innerHTML = '<p class="no-validation">所有字段置信度均高于 80%，无需人工校验。</p>';
    }
    
    // 渲染可编辑字段
    let editorHtml = '<table class="editor-table"><thead><tr><th>字段名</th><th>当前值</th><th>修正值</th></tr></thead><tbody>';
    for (const [fieldName, fieldInfo] of Object.entries(fields)) {
        const currentValue = fieldInfo.value !== null && fieldInfo.value !== undefined ? String(fieldInfo.value) : "";
        editorHtml += `<tr>
            <td><strong>${fieldName}</strong></td>
            <td>${currentValue || "<em>未提取</em>"}</td>
            <td><input type="text" data-field="${fieldName}" value="${currentValue}" placeholder="输入修正值"></td>
        </tr>`;
    }
    editorHtml += '</tbody></table>';
    editorContainer.innerHTML = editorHtml;
    regenerateBtn.style.display = "block";
}

// 重新生成结构化结果
document.getElementById("regenerateBtn")?.addEventListener("click", async function() {
    if (!currentStructuredData) return;
    
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
        setStatus("没有需要修正的字段", "info");
        return;
    }
    
    setStatus("正在重新生成...", "info");
    
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
    
    // 重新渲染
    renderStructuredResult(updatedData);
    currentStructuredData = updatedData;
    setStatus("修正已应用", "success");
});

function renderProcessedPreview(imageData) {
    const normalized = normalizeImageData(imageData);
    if (normalized) {
        processedPreview.src = normalized;
        processedPreview.hidden = false;
        processedPlaceholder.textContent = "";
        processedPlaceholder.hidden = true;
    } else {
        processedPreview.hidden = true;
        processedPlaceholder.hidden = false;
        processedPlaceholder.textContent = "等待接口返回...";
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
    fileLabel.textContent = "点击或拖拽图片/PDF到此处";
    imagePreview.hidden = true;
    const placeholder = previewBox.querySelector(".placeholder");
    if (placeholder) {
        placeholder.textContent = "选择文件后会显示预览";
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

