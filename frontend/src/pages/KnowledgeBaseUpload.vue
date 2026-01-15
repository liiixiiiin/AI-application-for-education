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
            >
              <UploadCloud class="upload-icon" />
              <div class="upload-text">
                <strong>拖拽文件到此处</strong>
                <span>或点击选择文件（PDF / Word / Markdown）</span>
              </div>
            </el-upload>
          </el-form-item>
        </el-form>

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

        <div class="form-actions">
          <el-button @click="clearFiles">清空列表</el-button>
          <el-button type="primary" :loading="uploading" @click="simulateUpload">
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
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from "vue";
import { UploadCloud, Layers } from "lucide-vue-next";
import { apiRequest } from "../services/api";
import { ElMessage } from "element-plus";

const courses = ref([]);
const loadingCourses = ref(false);
const selectedCourse = ref("");
const files = ref([]);
const uploading = ref(false);
let uploadTimer = null;

const loadCourses = async () => {
  loadingCourses.value = true;
  try {
    courses.value = await apiRequest("/courses");
  } catch (error) {
    ElMessage.error(error.message || "加载课程失败");
  } finally {
    loadingCourses.value = false;
  }
};

const handleFileChange = (file, fileList) => {
  files.value = fileList.map((item) => ({
    uid: item.uid,
    name: item.name,
    docType: inferDocType(item.name),
    size: formatSize(item.size),
    status: "queued",
    progress: 0,
  }));
};

const handleFileRemove = (file) => {
  files.value = files.value.filter((item) => item.uid !== file.uid);
};

const inferDocType = (filename) => {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "PDF";
  if (ext === "doc" || ext === "docx") return "Word";
  if (ext === "md") return "Markdown";
  return "未知";
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

const simulateUpload = () => {
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

  let progress = 0;
  uploadTimer = setInterval(() => {
    progress += 12;
    files.value = files.value.map((file) => ({
      ...file,
      progress: Math.min(progress, 100),
      status: progress >= 100 ? "done" : "uploading",
    }));
    if (progress >= 100) {
      clearInterval(uploadTimer);
      uploadTimer = null;
      uploading.value = false;
      ElMessage.success("上传完成（占位）");
    }
  }, 180);
};

const clearFiles = () => {
  if (uploading.value) return;
  files.value = [];
};

onMounted(loadCourses);

onBeforeUnmount(() => {
  if (uploadTimer) {
    clearInterval(uploadTimer);
  }
});
</script>

<style scoped>
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
