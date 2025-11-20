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

    if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
    }
    objectUrl = URL.createObjectURL(file);

    imagePreview.src = objectUrl;
    imagePreview.hidden = false;
    previewBox.querySelector(".placeholder")?.setAttribute("hidden", "true");
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
        formData.append("image", fileInput.files[0]);

        const response = await fetch(`${API_BASE_URL}/ocr`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const text = await response.text();
            throw new Error(text || `请求失败 (${response.status})`);
        }

        const data = await response.json();
        renderResults(data);
        setStatus("识别完成", "success");
    } catch (error) {
        console.error(error);
        setStatus(`调用接口失败：${error.message}`, "error");
    } finally {
        uploadForm.querySelector("button").disabled = false;
    }
}

function renderResults(data) {
    renderProcessedPreview(data?.pre_processed_image);
    renderJsonView(ocrResultViewer, data?.ocr_result, "未返回 OCR 结果");
    renderJsonView(llmResultViewer, data?.llm_result, "未返回 LLM 结果");
}

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
    fileLabel.textContent = "点击或拖拽图片到此处";
    imagePreview.hidden = true;
    previewBox.querySelector(".placeholder")?.removeAttribute("hidden");
    if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
        objectUrl = undefined;
    }
}

