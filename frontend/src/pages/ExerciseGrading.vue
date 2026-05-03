<template>
  <div class="grade-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/courses' }">工作区</el-breadcrumb-item>
        <el-breadcrumb-item>练习评测</el-breadcrumb-item>
      </el-breadcrumb>
      <h1 class="page-title mt-4">练习评测</h1>
      <p class="page-subtitle">选择课程与练习批次，进入沉浸式做题模式。</p>
    </div>

    <div class="grade-layout">
      <div class="grade-main card">
        <el-form label-position="top">
          <div class="form-grid-3">
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

            <el-form-item label="选择练习批次">
              <el-select
                v-model="selectedBatchId"
                placeholder="请选择批次"
                filterable
                :loading="loadingBatches"
                :disabled="!selectedCourse"
                style="width: 100%"
              >
                <el-option
                  v-for="batch in batches"
                  :key="batch.batch_id"
                  :label="batch.title"
                  :value="batch.batch_id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="操作">
              <el-button type="primary" :disabled="!selectedBatchId" @click="startSession">
                开始练习
              </el-button>
            </el-form-item>
          </div>
        </el-form>

        <div v-if="batches.length" class="batch-list-section mt-8">
          <div class="section-title">可用练习批次</div>
          <el-table :data="batches" class="custom-table" style="width: 100%">
            <el-table-column prop="title" label="批次名称" min-width="200" />
            <el-table-column prop="count" label="题目数" width="100" />
            <el-table-column label="生成时间" width="180">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="scope">
                <el-button size="small" type="primary" plain @click="startSessionWithBatch(scope.row.batch_id)">
                  开始
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-else-if="selectedCourse && !loadingBatches" class="empty-result">
          该课程暂无练习批次，请先在"练习生成"中创建。
        </div>
        <div v-else class="empty-result">
          请先选择课程以查看可用的练习批次。
        </div>
      </div>

      <div class="grade-sidebar">
        <div class="info-card">
          <div class="info-icon">
            <ClipboardCheck :size="18" />
          </div>
          <h3 class="info-title">评测提示</h3>
          <ul class="info-list">
            <li>
              <strong>沉浸式做题</strong>
              <p>点击"开始练习"进入全屏做题模式，每次专注一道题目。</p>
            </li>
            <li>
              <strong>即时反馈</strong>
              <p>提交后立即看到评测结果、正确答案与详细解析。</p>
            </li>
            <li>
              <strong>进度导航</strong>
              <p>底部进度条支持题目切换，左右方向键也可快速导航。</p>
            </li>
            <li>
              <strong>练习总结</strong>
              <p>完成所有题目后查看正确率统计与薄弱知识点分析。</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ClipboardCheck } from "lucide-vue-next";
import { ElMessage } from "element-plus";
import { apiRequest } from "../services/api";

const router = useRouter();

const courses = ref([]);
const loadingCourses = ref(false);
const selectedCourse = ref("");

const batches = ref([]);
const loadingBatches = ref(false);
const selectedBatchId = ref("");

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

const loadBatches = async () => {
  if (!selectedCourse.value) {
    batches.value = [];
    return;
  }
  loadingBatches.value = true;
  try {
    batches.value = await apiRequest(`/courses/${selectedCourse.value}/exercises/batches`);
  } catch (error) {
    ElMessage.error(error.message || "加载批次失败");
  } finally {
    loadingBatches.value = false;
  }
};

const startSession = () => {
  if (!selectedCourse.value || !selectedBatchId.value) return;
  router.push({
    path: "/exercises/session",
    query: { courseId: selectedCourse.value, batchId: selectedBatchId.value },
  });
};

const startSessionWithBatch = (batchId) => {
  router.push({
    path: "/exercises/session",
    query: { courseId: selectedCourse.value, batchId },
  });
};

const formatDate = (value) => {
  if (!value) return "-";
  return new Date(value).toLocaleString();
};

watch(selectedCourse, () => {
  loadBatches();
  selectedBatchId.value = "";
});

onMounted(loadCourses);
</script>

<style scoped>
.grade-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.grade-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 24px;
}

.grade-main {
  padding: 28px;
}

.grade-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 120px;
  gap: 16px;
  align-items: flex-end;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}

.mt-8 {
  margin-top: 32px;
}

.empty-result {
  padding: 24px;
  text-align: center;
  color: #9ca3af;
  border: 1px dashed #e5e7eb;
  border-radius: 16px;
}

@media (max-width: 1024px) {
  .grade-layout {
    grid-template-columns: 1fr;
  }
  .grade-sidebar {
    order: -1;
  }
}

@media (max-width: 720px) {
  .form-grid-3 {
    grid-template-columns: 1fr;
  }
}
</style>
