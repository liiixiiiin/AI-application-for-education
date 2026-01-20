<template>
  <div class="knowledge-base-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/courses' }">工作区</el-breadcrumb-item>
        <el-breadcrumb-item>知识库上传</el-breadcrumb-item>
      </el-breadcrumb>
      <h1 class="page-title mt-4">知识库上传</h1>
      <p class="page-subtitle">选择课程并上传教学文档，系统将自动完成解析与索引。</p>
    </div>

    <div class="upload-layout">
      <div class="upload-main card">
        <el-form label-position="top">
          <el-form-item label="选择课程">
            <el-select
              v-model="selectedCourse"
              placeholder="请选择课程"
              filterable
              :loading="loadingCourses"
              style="width: 100%"
            >
              <el-option
                v-for="course in courses"
                :key="course.id"
                :label="course.title"
                :value="course.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="切分配置">
            <div class="config-row">
              <el-switch v-model="useLlmChunking" active-text="开启大模型辅助切分" />
              <el-tooltip content="开启后将使用大模型优化语义边界与标题路径，解析速度较慢但质量更高。" placement="top">
                <span class="info-icon-small">?</span>
              </el-tooltip>
            </div>
          </el-form-item>

          <el-form-item label="上传文档">
            <el-upload
              class="upload-box"
              drag
              multiple
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              accept=".pdf,.doc,.docx,.md"
              ref="uploadRef"
            >
              <UploadCloud class="upload-icon" />
              <div class="upload-text">
                <strong>拖拽文件到此处</strong>
                <span>或点击选择文件（PDF / Word / Markdown）</span>
              </div>
            </el-upload>
          </el-form-item>
        </el-form>

        <div class="web-section">
          <div class="section-title">网页上传</div>
          <el-form label-position="top">
            <el-form-item label="网页 URL">
              <el-input
                v-model="webUrls"
                type="textarea"
                :rows="3"
                placeholder="每行一个 URL（http/https）"
              />
              <div class="helper-text">可一次解析多个网页链接。</div>
            </el-form-item>
            <el-form-item label="解析范围（可选）">
              <el-input
                v-model="webParseClasses"
                placeholder="填写 class 名称，逗号分隔（例如 main-left left, title）"
              />
              <div class="helper-text">留空则抓取网页正文内容。</div>
            </el-form-item>
          </el-form>
          <div class="web-actions">
            <el-button
              type="primary"
              :loading="webUploading"
              @click="startWebUpload"
            >
              解析并入库
            </el-button>
          </div>
        </div>

        <div class="text-section">
          <div class="section-title">文本上传</div>
          <el-form label-position="top">
            <el-form-item label="文档名称">
              <el-input v-model="textDocName" placeholder="例如：课程摘要 / 课堂笔记" />
            </el-form-item>
            <el-form-item label="文档类型">
              <el-select v-model="textDocType" placeholder="请选择类型" style="width: 100%">
                <el-option label="纯文本（txt）" value="txt" />
                <el-option label="Markdown（md）" value="md" />
              </el-select>
            </el-form-item>
            <el-form-item label="文档内容">
              <el-input
                v-model="textDocContent"
                type="textarea"
                :rows="6"
                placeholder="粘贴或输入知识内容..."
              />
              <div class="helper-text">支持直接粘贴段落或笔记内容。</div>
            </el-form-item>
          </el-form>
          <div class="text-actions">
            <el-button @click="clearTextUpload">清空内容</el-button>
            <el-button type="primary" :loading="textUploading" @click="startTextUpload">
              提交文本
            </el-button>
          </div>
        </div>

        <div class="file-section">
          <div class="section-title">文件列表</div>
          <el-table v-if="files.length" :data="files" class="custom-table" style="width: 100%">
            <el-table-column prop="name" label="文件名" min-width="220" />
            <el-table-column prop="docType" label="类型" width="120" />
            <el-table-column prop="size" label="大小" width="120" />
            <el-table-column label="状态" width="120">
              <template #default="scope">
                <span class="status-pill" :class="scope.row.status">
                  {{ statusLabel(scope.row.status) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="上传进度" min-width="200">
              <template #default="scope">
                <el-progress
                  :percentage="scope.row.progress"
                  :status="scope.row.status === 'error' ? 'exception' : scope.row.status === 'done' ? 'success' : ''"
                  :stroke-width="8"
                />
              </template>
            </el-table-column>
          </el-table>
          <div v-else class="empty-files">
            暂无文件，请选择课程并添加知识库文档。
          </div>
        </div>

        <div class="file-section">
          <div class="section-title">已上传文档</div>
          <el-table
            v-if="documents.length"
            :data="documents"
            class="custom-table"
            style="width: 100%"
            :loading="loadingDocuments"
          >
            <el-table-column prop="name" label="文件名" min-width="200" />
            <el-table-column label="类型" width="80">
              <template #default="scope">
                <el-tag size="small" effect="light">{{ scope.row.doc_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag
                  size="small"
                  :type="scope.row.status === 'indexed' ? 'success' : 'info'"
                  effect="light"
                >
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="上传时间" width="160">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="scope">
                <div class="action-group">
                  <el-button size="small" @click="openDocumentView(scope.row)">查看</el-button>
                  <el-button size="small" @click="openDocumentEdit(scope.row)">修改</el-button>
                  <el-button size="small" type="danger" plain @click="deleteDocument(scope.row)">
                    删除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div v-else class="empty-files">
            暂无已上传文档。
          </div>
        </div>

        <div class="kp-section">
          <div class="section-header">
            <div class="section-title">课程知识点管理</div>
            <div class="header-actions">
              <el-button
                size="small"
                type="primary"
                plain
                :loading="generatingKp"
                @click="generateKp"
              >
                自动生成知识点
              </el-button>
              <el-button size="small" type="primary" plain @click="openAddKp">
                手动添加
              </el-button>
            </div>
          </div>
          <div v-if="knowledgePoints.length" class="kp-tags">
            <el-tag
              v-for="kp in knowledgePoints"
              :key="kp.id"
              closable
              class="kp-tag"
              @close="deleteKp(kp)"
              @click="editKp(kp)"
            >
              {{ kp.point }}
            </el-tag>
          </div>
          <div v-else class="empty-files">
            暂无知识点。点击“自动生成”或“手动添加”来开始。
          </div>
        </div>

        <div class="form-actions">
          <el-button @click="clearFiles">清空列表</el-button>
          <el-button type="primary" :loading="uploading" @click="startUpload">
            开始上传
          </el-button>
        </div>
      </div>

      <div class="upload-sidebar">
        <div class="info-card">
          <div class="info-icon">
            <Layers :size="18" />
          </div>
          <h3 class="info-title">上传提示</h3>
          <ul class="info-list">
            <li>
              <strong>支持格式</strong>
              <p>PDF / Word / Markdown，单次可上传多份文档。</p>
            </li>
            <li>
              <strong>解析流程</strong>
              <p>系统将自动清洗文本并切分为知识片段。</p>
            </li>
            <li>
              <strong>索引进度</strong>
              <p>上传后可在此查看索引与检索状态。</p>
            </li>
            <li>
              <strong>网页解析</strong>
              <p>支持粘贴网页链接，自动抽取正文并加入知识库。</p>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <el-drawer v-model="viewDrawerVisible" title="知识库内容" size="50%">
      <div v-if="viewChunks.length" class="drawer-content">
        <div v-for="chunk in viewChunks" :key="chunk.chunk_id" class="chunk-card">
          <div class="chunk-title">{{ chunk.title_path }}</div>
          <div class="chunk-content">{{ chunk.content }}</div>
        </div>
      </div>
      <div v-else class="empty-files">暂无内容。</div>
    </el-drawer>

    <el-dialog v-model="editDialogVisible" title="修改知识库文档" width="620px">
      <el-form label-position="top">
        <el-form-item label="文档名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="文档类型">
          <el-input v-model="editForm.doc_type" placeholder="例如 pdf / markdown / web" />
        </el-form-item>
        <el-form-item label="文档内容">
          <el-input v-model="editForm.content" type="textarea" :rows="10" />
        </el-form-item>
        <el-form-item label="切分配置">
          <el-switch v-model="editForm.use_llm_chunking" active-text="重新切分时使用大模型辅助" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editing" @click="submitDocumentEdit">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import { UploadCloud, Layers } from "lucide-vue-next";
import { apiRequest } from "../services/api";
import { ElMessage, ElMessageBox } from "element-plus";

const courses = ref([]);
const loadingCourses = ref(false);
const selectedCourse = ref("");
const useLlmChunking = ref(true);
const files = ref([]);
const uploading = ref(false);
const uploadRef = ref(null);
const documents = ref([]);
const loadingDocuments = ref(false);
const webUrls = ref("");
const webParseClasses = ref("");
const webUploading = ref(false);
const textDocName = ref("");
const textDocType = ref("txt");
const textDocContent = ref("");
const textUploading = ref(false);
const viewDrawerVisible = ref(false);
const viewChunks = ref([]);
const editDialogVisible = ref(false);
const editing = ref(false);
const editForm = ref({ id: "", name: "", doc_type: "", content: "", use_llm_chunking: true });
const knowledgePoints = ref([]);
const generatingKp = ref(false);

const loadCourses = async () => {
  loadingCourses.value = true;
  try {
    courses.value = await apiRequest("/courses");
    if (!selectedCourse.value && courses.value.length) {
      selectedCourse.value = courses.value[0].id;
    }
  } catch (error) {
    ElMessage.error(error.message || "加载课程失败");
  } finally {
    loadingCourses.value = false;
  }
};

const loadDocuments = async () => {
  if (!selectedCourse.value) {
    documents.value = [];
    knowledgePoints.value = [];
    return;
  }
  const courseId = selectedCourse.value;
  loadingDocuments.value = true;
  try {
    const [docs, kps] = await Promise.all([
      apiRequest(`/courses/${courseId}/documents`),
      apiRequest(`/courses/${courseId}/knowledge-points`),
    ]);
    if (selectedCourse.value === courseId) {
      documents.value = docs;
      knowledgePoints.value = kps;
    }
  } catch (error) {
    if (selectedCourse.value === courseId) {
      ElMessage.error(error.message || "加载内容失败");
    }
  } finally {
    if (selectedCourse.value === courseId) {
      loadingDocuments.value = false;
    }
  }
};

const generateKp = async () => {
  if (!selectedCourse.value) return;
  generatingKp.value = true;
  try {
    const payload = await apiRequest(
      `/courses/${selectedCourse.value}/knowledge-points/generate?use_llm=true`
    );
    const points = payload.points || [];
    if (!points.length) {
      ElMessage.warning("未提取到新的知识点");
      return;
    }
    // Sync to backend
    await apiRequest(`/courses/${selectedCourse.value}/knowledge-points/sync`, {
      method: "POST",
      body: JSON.stringify({ points, mode: "append" }),
    });
    ElMessage.success("知识点生成并保存成功");
    await loadDocuments();
  } catch (error) {
    ElMessage.error(error.message || "生成知识点失败");
  } finally {
    generatingKp.value = false;
  }
};

const openAddKp = () => {
  ElMessageBox.prompt("请输入新知识点名称", "手动添加", {
    confirmButtonText: "添加",
    cancelButtonText: "取消",
    inputPattern: /\S+/,
    inputErrorMessage: "名称不能为空",
  })
    .then(async ({ value }) => {
      await apiRequest(`/courses/${selectedCourse.value}/knowledge-points`, {
        method: "POST",
        body: JSON.stringify({ point: value.trim() }),
      });
      ElMessage.success("添加成功");
      await loadDocuments();
    })
    .catch(() => {});
};

const editKp = (kp) => {
  ElMessageBox.prompt("请输入知识点名称", "修改知识点", {
    confirmButtonText: "保存",
    cancelButtonText: "取消",
    inputValue: kp.point,
    inputPattern: /\S+/,
    inputErrorMessage: "名称不能为空",
  })
    .then(async ({ value }) => {
      await apiRequest(`/courses/${selectedCourse.value}/knowledge-points/${kp.id}`, {
        method: "PUT",
        body: JSON.stringify({ point: value.trim() }),
      });
      ElMessage.success("修改成功");
      await loadDocuments();
    })
    .catch(() => {});
};

const deleteKp = async (kp) => {
  try {
    await apiRequest(`/courses/${selectedCourse.value}/knowledge-points/${kp.id}`, {
      method: "DELETE",
    });
    knowledgePoints.value = knowledgePoints.value.filter((item) => item.id !== kp.id);
    ElMessage.success("知识点已移除");
  } catch (error) {
    ElMessage.error(error.message || "移除失败");
  }
};

const deleteDocument = async (doc) => {
  try {
    await ElMessageBox.confirm(
      `确认删除文档「${doc.name}」吗？此操作会同步移除索引片段。`,
      "删除确认",
      { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" }
    );
  } catch {
    return;
  }

  try {
    await apiRequest(`/courses/${selectedCourse.value}/documents/${doc.id}`, {
      method: "DELETE",
    });
    ElMessage.success("文档已删除");
    await loadDocuments();
  } catch (error) {
    ElMessage.error(error.message || "删除失败");
  }
};

const openDocumentView = async (doc) => {
  if (!selectedCourse.value) return;
  viewDrawerVisible.value = true;
  viewChunks.value = [];
  try {
    const payload = await apiRequest(
      `/courses/${selectedCourse.value}/documents/${doc.id}/chunks`
    );
    viewChunks.value = payload;
  } catch (error) {
    ElMessage.error(error.message || "加载文档内容失败");
  }
};

const openDocumentEdit = async (doc) => {
  if (!selectedCourse.value) return;
  editDialogVisible.value = true;
  editForm.value = {
    id: doc.id,
    name: doc.name,
    doc_type: doc.doc_type,
    content: "",
    use_llm_chunking: true,
  };
  try {
    const payload = await apiRequest(
      `/courses/${selectedCourse.value}/documents/${doc.id}/chunks`
    );
    const ordered = [...payload].sort((a, b) => (a.order_index || 0) - (b.order_index || 0));
    editForm.value.content = ordered.map((item) => item.content).join("\n\n");
  } catch (error) {
    ElMessage.error(error.message || "加载文档内容失败");
  }
};

const handleFileChange = (file, fileList) => {
  files.value = fileList.map((item) => {
    const docType = inferDocType(item.name);
    return {
      uid: item.uid,
      name: item.name,
      raw: item.raw,
      docType: docType.label,
      docTypeKey: docType.key,
      size: formatSize(item.size),
      status: "queued",
      progress: 0,
    };
  });
};

const handleFileRemove = (file) => {
  files.value = files.value.filter((item) => item.uid !== file.uid);
};

const inferDocType = (filename) => {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return { label: "PDF", key: "pdf" };
  if (ext === "doc") return { label: "Word", key: "doc" };
  if (ext === "docx") return { label: "Word", key: "docx" };
  if (ext === "md") return { label: "Markdown", key: "markdown" };
  return { label: "未知", key: "unknown" };
};

const formatSize = (size) => {
  if (!size && size !== 0) return "-";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
};

const statusLabel = (status) => {
  const map = {
    queued: "待上传",
    uploading: "上传中",
    done: "已完成",
    error: "失败",
  };
  return map[status] || status;
};

const formatDate = (value) => {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  const pad = (num) => String(num).padStart(2, "0");
  return `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())} ${pad(
    parsed.getHours()
  )}:${pad(parsed.getMinutes())}`;
};

const startUpload = async () => {
  if (!selectedCourse.value) {
    ElMessage.warning("请先选择课程");
    return;
  }
  if (!files.value.length) {
    ElMessage.warning("请先选择上传文件");
    return;
  }
  if (uploading.value) return;

  uploading.value = true;
  files.value = files.value.map((file) => ({
    ...file,
    status: "uploading",
    progress: 0,
  }));

  try {
    const formData = new FormData();
    files.value.forEach((file) => {
      if (file.raw) {
        formData.append("files", file.raw, file.name);
      }
    });
    await apiRequest(`/courses/${selectedCourse.value}/documents/upload?use_llm_chunking=${useLlmChunking.value}`, {
      method: "POST",
      body: formData,
    });
    files.value = files.value.map((file) => ({
      ...file,
      status: "done",
      progress: 100,
    }));
    ElMessage.success("上传完成，已进入检索索引");
    uploadRef.value?.clearFiles();
    files.value = [];
    await loadDocuments();
  } catch (error) {
    files.value = files.value.map((file) => ({
      ...file,
      status: "error",
      progress: 0,
    }));
    ElMessage.error(error.message || "上传失败");
  } finally {
    uploading.value = false;
  }
};

const clearFiles = () => {
  if (uploading.value) return;
  files.value = [];
  uploadRef.value?.clearFiles();
};

const startWebUpload = async () => {
  if (!selectedCourse.value) {
    ElMessage.warning("请先选择课程");
    return;
  }
  const urls = webUrls.value
    .split(/\n|,|;/)
    .map((item) => item.trim())
    .filter(Boolean);
  if (!urls.length) {
    ElMessage.warning("请输入网页 URL");
    return;
  }
  if (webUploading.value) return;
  webUploading.value = true;
  const parseClasses = webParseClasses.value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  try {
    await apiRequest(`/courses/${selectedCourse.value}/documents/web`, {
      method: "POST",
      body: JSON.stringify({
        urls,
        parse_classes: parseClasses.length ? parseClasses : null,
        use_llm_chunking: useLlmChunking.value,
      }),
    });
    ElMessage.success("网页已解析并入库");
    webUrls.value = "";
    webParseClasses.value = "";
    await loadDocuments();
  } catch (error) {
    ElMessage.error(error.message || "网页解析失败");
  } finally {
    webUploading.value = false;
  }
};

const clearTextUpload = () => {
  if (textUploading.value) return;
  textDocName.value = "";
  textDocContent.value = "";
  textDocType.value = "txt";
};

const startTextUpload = async () => {
  if (!selectedCourse.value) {
    ElMessage.warning("请先选择课程");
    return;
  }
  if (!textDocName.value.trim()) {
    ElMessage.warning("请填写文档名称");
    return;
  }
  if (!textDocContent.value.trim()) {
    ElMessage.warning("请填写文档内容");
    return;
  }
  if (textUploading.value) return;

  textUploading.value = true;
  try {
    const name = textDocName.value.trim();
    const ext = textDocType.value || "txt";
    const filename = `${name}.${ext}`;
    const mimeType = ext === "md" ? "text/markdown" : "text/plain";
    const file = new File([textDocContent.value], filename, { type: mimeType });
    const formData = new FormData();
    formData.append("files", file, filename);
    await apiRequest(`/courses/${selectedCourse.value}/documents/upload?use_llm_chunking=${useLlmChunking.value}`, {
      method: "POST",
      body: formData,
    });
    ElMessage.success("文本已入库");
    clearTextUpload();
    await loadDocuments();
  } catch (error) {
    ElMessage.error(error.message || "文本上传失败");
  } finally {
    textUploading.value = false;
  }
};

const submitDocumentEdit = async () => {
  if (!selectedCourse.value) return;
  if (!editForm.value.name?.trim()) {
    ElMessage.warning("请填写文档名称");
    return;
  }
  editing.value = true;
  try {
    await apiRequest(`/courses/${selectedCourse.value}/documents/${editForm.value.id}`, {
      method: "PUT",
      body: JSON.stringify({
        name: editForm.value.name,
        doc_type: editForm.value.doc_type || null,
        content: editForm.value.content || "",
        use_llm_chunking: editForm.value.use_llm_chunking,
      }),
    });
    ElMessage.success("文档已更新");
    editDialogVisible.value = false;
    await loadDocuments();
  } catch (error) {
    ElMessage.error(error.message || "更新失败");
  } finally {
    editing.value = false;
  }
};

onMounted(loadCourses);

watch(selectedCourse, () => {
  loadDocuments();
});
</script>

<style scoped>
.config-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-icon-small {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--color-bg-alt);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 11px;
  cursor: help;
}

.knowledge-base-page {
  max-width: 1100px;
  margin: 0 auto;
}

.mt-4 {
  margin-top: 16px;
}

.upload-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 24px;
  align-items: start;
}

.upload-main {
  padding: 32px;
}

.upload-box {
  width: 100%;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-alt);
  padding: 24px;
}

.upload-icon {
  width: 32px;
  height: 32px;
  color: var(--color-text-main);
}

.upload-text {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--color-text-secondary);
  margin-top: 12px;
}

.file-section {
  margin-top: 24px;
}

.action-group {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.action-group .el-button {
  padding: 4px 10px !important;
  font-size: 12px;
  height: 28px !important;
}

.drawer-content {
  display: grid;
  gap: 16px;
}

.chunk-card {
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  padding: 16px;
  background: var(--color-bg-alt);
}

.chunk-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-main);
  margin-bottom: 8px;
}

.chunk-content {
  white-space: pre-wrap;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.web-section {
  margin-top: 24px;
  padding: 20px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-bg-alt);
}

.web-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.text-section {
  margin-top: 24px;
  padding: 20px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-bg-alt);
}

.text-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
}

.helper-text {
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.kp-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-soft);
}

.kp-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  background: var(--color-bg-alt);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.kp-tag {
  cursor: pointer;
  padding: 6px 12px;
  font-size: 13px;
  height: auto;
}

.kp-tag:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 12px;
}

.empty-files {
  padding: 20px;
  border-radius: var(--radius-sm);
  background: var(--color-bg-alt);
  color: var(--color-text-muted);
  font-size: 14px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.status-pill.queued {
  background: rgba(15, 23, 42, 0.08);
  color: var(--color-text-secondary);
}

.status-pill.uploading {
  background: rgba(59, 130, 246, 0.12);
  color: var(--color-primary);
}

.status-pill.done {
  background: rgba(34, 197, 94, 0.12);
  color: var(--color-success);
}

.status-pill.error {
  background: rgba(239, 68, 68, 0.12);
  color: var(--color-error);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-soft);
}

.info-card {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 24px;
}

.info-icon {
  width: 32px;
  height: 32px;
  background-color: var(--color-border-soft);
  color: var(--color-text-main);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  margin-bottom: 16px;
}

.info-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-main);
  margin: 0 0 16px 0;
}

.info-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.info-list li {
  margin-bottom: 20px;
}

.info-list strong {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-main);
  margin-bottom: 4px;
}

@media (max-width: 1000px) {
  .upload-layout {
    grid-template-columns: 1fr;
  }
}
</style>
