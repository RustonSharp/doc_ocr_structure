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

fileInput.addEventListener("change", handleFileChange);
uploadForm.addEventListener("submit", handleFormSubmit);

function handleFileChange(event) {
    const file = event.target.files?.[0];
    if (!file) {
        resetPreview();
        return;
    }

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

async function handleFormSubmit(event) {
    event.preventDefault();

    if (!fileInput.files?.length) {
        setStatus("请先选择一张图片", "error");
        return;
    }

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

