<template>
  <div class="outline-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/courses' }">工作区</el-breadcrumb-item>
        <el-breadcrumb-item>讲解提纲</el-breadcrumb-item>
      </el-breadcrumb>
      <h1 class="page-title mt-4">章节知识讲解提纲</h1>
      <p class="page-subtitle">基于课程知识库生成课堂讲解结构、重点难点、时间分配与基础实训任务。</p>
    </div>

    <div class="outline-layout">
      <div class="outline-main card">
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

          <div class="form-grid">
            <el-form-item label="章节名称">
              <el-input v-model="chapterTitle" placeholder="例如：第 3 章 检索增强生成 RAG" />
            </el-form-item>
            <el-form-item label="课时长度">
              <el-input-number
                v-model="durationMinutes"
                :min="10"
                :max="240"
                :step="5"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="学生基础">
              <el-select v-model="audienceLevel" style="width: 100%">
                <el-option label="基础" value="基础" />
                <el-option label="进阶" value="进阶" />
                <el-option label="复习巩固" value="复习巩固" />
              </el-select>
            </el-form-item>
          </div>

          <el-form-item label="知识点范围">
            <el-select
              v-model="knowledgeScope"
              multiple
              filterable
              allow-create
              placeholder="输入或选择知识点；留空时自动从知识库提取"
              style="width: 100%"
            >
              <el-option
                v-for="kp in savedKnowledgePoints"
                :key="kp.id"
                :label="kp.point"
                :value="kp.point"
              />
            </el-select>
            <div class="helper-text">
              <span v-if="savedKnowledgePoints.length">
                已加载 {{ savedKnowledgePoints.length }} 个课程知识点，可按章节选择重点范围。
              </span>
              <span v-else>该课程暂无保存知识点，可手动输入或直接根据章节名称检索生成。</span>
            </div>
          </el-form-item>

          <el-form-item>
            <el-checkbox v-model="includePractice">包含基础实训任务建议</el-checkbox>
          </el-form-item>
        </el-form>

        <div class="form-actions">
          <el-button @click="resetForm">重置条件</el-button>
          <el-button type="primary" :loading="generating" @click="handleGenerate">
            生成讲解提纲
          </el-button>
        </div>

        <div v-if="outline" class="outline-result">
          <div class="result-toolbar">
            <div>
              <div class="section-kicker">生成结果</div>
              <h2>{{ outline.title }}</h2>
            </div>
            <el-button plain @click="copyOutline">复制提纲</el-button>
          </div>

          <div class="summary-grid">
            <div class="summary-card">
              <span>章节</span>
              <strong>{{ outline.chapter_title }}</strong>
            </div>
            <div class="summary-card">
              <span>建议课时</span>
              <strong>{{ outline.duration_minutes }} 分钟</strong>
            </div>
            <div class="summary-card">
              <span>引用片段</span>
              <strong>{{ outline.source_chunks.length }} 条</strong>
            </div>
          </div>

          <div class="outline-section">
            <h3>教学目标</h3>
            <ul class="clean-list">
              <li v-for="item in outline.objectives" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div class="two-column">
            <div class="outline-section">
              <h3>重点知识</h3>
              <div class="point-list">
                <div v-for="item in outline.key_points" :key="item" class="point-item">
                  {{ item }}
                </div>
              </div>
            </div>
            <div class="outline-section">
              <h3>难点提示</h3>
              <div class="point-list warning">
                <div v-for="item in outline.difficult_points" :key="item" class="point-item">
                  {{ item }}
                </div>
              </div>
            </div>
          </div>

          <div class="outline-section">
            <div class="section-title-row">
              <h3>课堂流程与时间分配</h3>
              <el-tag :type="flowTotalMinutes === outline.duration_minutes ? 'success' : 'warning'" effect="plain">
                已分配 {{ flowTotalMinutes }} / {{ outline.duration_minutes }} 分钟
              </el-tag>
            </div>
            <div class="flow-list">
              <div v-for="(item, index) in outline.teaching_flow" :key="`${item.stage}-${index}`" class="flow-item">
                <div class="flow-time">{{ item.minutes }} min</div>
                <div class="flow-content">
                  <div class="flow-title">{{ item.stage }}</div>
                  <p><strong>教师活动：</strong>{{ item.teacher_activity }}</p>
                  <p><strong>学生活动：</strong>{{ item.student_activity }}</p>
                  <p><strong>内容重点：</strong>{{ item.content_focus }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="two-column">
            <div class="outline-section">
              <h3>基础实训任务</h3>
              <ul class="clean-list">
                <li v-for="item in outline.practice_tasks" :key="formatListItem(item)">
                  {{ formatListItem(item) }}
                </li>
              </ul>
              <el-empty v-if="!outline.practice_tasks.length" description="未生成实训任务" :image-size="72" />
            </div>
            <div class="outline-section">
              <h3>考核与巩固建议</h3>
              <ul class="clean-list">
                <li v-for="item in outline.assessment_suggestions" :key="formatListItem(item)">
                  {{ formatListItem(item) }}
                </li>
              </ul>
            </div>
          </div>

          <div class="outline-section">
            <h3>知识来源</h3>
            <el-collapse>
              <el-collapse-item
                v-for="citation in outline.citations"
                :key="citation.chunk_id"
                :title="formatCitationTitle(citation)"
              >
                <div class="citation-meta">{{ citation.source_doc_name }} · {{ citation.chunk_id }}</div>
                <p class="citation-excerpt">{{ citation.excerpt }}</p>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>

        <div v-else class="empty-result">
          <BookOpenText :size="34" />
          <h3>等待生成章节提纲</h3>
          <p>选择课程并输入章节名称后，系统会检索本地知识库并生成适合教师备课的讲解结构。</p>
        </div>

        <div class="history-section">
          <div class="section-header">
            <div>
              <div class="section-kicker">历史记录</div>
              <div class="section-title">已保存讲解提纲</div>
            </div>
            <el-button size="small" plain :loading="loadingHistory" @click="loadHistory">刷新列表</el-button>
          </div>
          <el-table :data="history" class="custom-table" style="width: 100%" v-loading="loadingHistory">
            <el-table-column prop="title" label="提纲名称" min-width="220">
              <template #default="scope">
                <div class="history-title">
                  <span>{{ scope.row.title }}</span>
                  <el-tag v-if="scope.row.outline_id === currentOutlineId" size="small" type="success" effect="plain">
                    当前
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="chapter_title" label="章节" min-width="160" />
            <el-table-column label="课时" width="90">
              <template #default="scope">{{ scope.row.duration_minutes }} 分钟</template>
            </el-table-column>
            <el-table-column label="生成时间" width="180">
              <template #default="scope">{{ formatDate(scope.row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="190" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="viewOutline(scope.row)">查看</el-button>
                <el-button size="small" type="danger" plain @click="deleteOutline(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="outline-sidebar">
        <div class="info-card">
          <div class="info-icon">
            <BookMarked :size="18" />
          </div>
          <h3 class="info-title">备课生成建议</h3>
          <ul class="info-list">
            <li>
              <strong>先上传资料</strong>
              <p>建议先上传课程大纲、讲义或实训指导书，提纲会更贴近课程内容。</p>
            </li>
            <li>
              <strong>自动保存历史</strong>
              <p>每次生成完成后都会保存到历史记录，后续可直接查看和复用。</p>
            </li>
            <li>
              <strong>选择知识点</strong>
              <p>可手动限定重点知识点，用于生成面向某一节课的讲解提纲。</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { BookMarked, BookOpenText } from "lucide-vue-next";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiRequest } from "../services/api";

const courses = ref([]);
const loadingCourses = ref(false);
const selectedCourse = ref("");
const savedKnowledgePoints = ref([]);
const chapterTitle = ref("");
const durationMinutes = ref(45);
const audienceLevel = ref("基础");
const knowledgeScope = ref([]);
const includePractice = ref(true);
const generating = ref(false);
const outline = ref(null);
const currentOutlineId = ref(null);
const history = ref([]);
const loadingHistory = ref(false);

const flowTotalMinutes = computed(() => {
  return (outline.value?.teaching_flow || []).reduce((total, item) => {
    return total + Number(item.minutes || 0);
  }, 0);
});

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

const loadKnowledgePoints = async () => {
  if (!selectedCourse.value) {
    savedKnowledgePoints.value = [];
    return;
  }
  try {
    savedKnowledgePoints.value = await apiRequest(`/courses/${selectedCourse.value}/knowledge-points`);
  } catch (error) {
    ElMessage.error(error.message || "加载知识点失败");
  }
};

const loadHistory = async () => {
  if (!selectedCourse.value) {
    history.value = [];
    return;
  }
  loadingHistory.value = true;
  try {
    history.value = await apiRequest(`/courses/${selectedCourse.value}/lesson-outlines`);
  } catch (error) {
    ElMessage.error(error.message || "加载讲解提纲历史失败");
  } finally {
    loadingHistory.value = false;
  }
};

const handleGenerate = async () => {
  if (!selectedCourse.value) {
    ElMessage.warning("请先选择课程");
    return;
  }
  if (!chapterTitle.value.trim()) {
    ElMessage.warning("请输入章节名称");
    return;
  }
  generating.value = true;
  try {
    outline.value = await apiRequest(`/courses/${selectedCourse.value}/lesson-outlines/generate`, {
      method: "POST",
      body: JSON.stringify({
        course_id: selectedCourse.value,
        chapter_title: chapterTitle.value.trim(),
        duration_minutes: durationMinutes.value,
        knowledge_scope: knowledgeScope.value.length ? knowledgeScope.value : null,
        audience_level: audienceLevel.value,
        include_practice: includePractice.value,
      }),
    });
    currentOutlineId.value = outline.value?.outline_id || null;
    await loadHistory();
    ElMessage.success("讲解提纲生成完成，已保存到历史记录");
  } catch (error) {
    ElMessage.error(error.message || "讲解提纲生成失败");
  } finally {
    generating.value = false;
  }
};

const resetForm = () => {
  chapterTitle.value = "";
  durationMinutes.value = 45;
  audienceLevel.value = "基础";
  knowledgeScope.value = [];
  includePractice.value = true;
  outline.value = null;
  currentOutlineId.value = null;
};

const formatCitationTitle = (citation) => {
  const rawTitle = citation.title_path || "";
  const sourceName = citation.source_doc_name || "未知文档";
  const meaningfulTitle = rawTitle
    .split(">")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(-2)
    .join(" > ");
  const title = meaningfulTitle || sourceName || `知识片段 ${citation.chunk_id}`;
  return title.length > 56 ? `${title.slice(0, 56)}...` : title;
};

const formatListItem = (item) => {
  if (typeof item === "string") return item;
  if (item && typeof item === "object") {
    const parts = [];
    if (item.name || item.title || item.task) {
      parts.push(item.name || item.title || item.task);
    }
    if (item.description || item.content) {
      parts.push(item.description || item.content);
    }
    if (item.duration_minutes || item.minutes) {
      parts.push(`建议用时 ${item.duration_minutes || item.minutes} 分钟`);
    }
    if (item.output_format || item.output) {
      parts.push(`产出形式：${item.output_format || item.output}`);
    }
    return parts.join("；") || JSON.stringify(item);
  }
  return String(item || "");
};

const copyOutline = async () => {
  if (!outline.value) return;
  const text = [
    outline.value.title,
    `章节：${outline.value.chapter_title}`,
    `课时：${outline.value.duration_minutes} 分钟`,
    "",
    "教学目标：",
    ...outline.value.objectives.map((item) => `- ${item}`),
    "",
    "重点知识：",
    ...outline.value.key_points.map((item) => `- ${item}`),
    "",
    "难点提示：",
    ...outline.value.difficult_points.map((item) => `- ${item}`),
    "",
    "课堂流程：",
    ...outline.value.teaching_flow.map(
      (item) => `- ${item.stage}（${item.minutes} 分钟）：${item.content_focus}`
    ),
    "",
    "基础实训任务：",
    ...outline.value.practice_tasks.map((item) => `- ${formatListItem(item)}`),
  ].join("\n");
  await navigator.clipboard.writeText(text);
  ElMessage.success("已复制提纲内容");
};

const viewOutline = async (item) => {
  try {
    outline.value = await apiRequest(`/courses/${selectedCourse.value}/lesson-outlines/${item.outline_id}`);
    currentOutlineId.value = item.outline_id;
    chapterTitle.value = outline.value.chapter_title || "";
    durationMinutes.value = outline.value.duration_minutes || 45;
    knowledgeScope.value = outline.value.key_points || [];
    ElMessage.info(`已加载提纲：${item.title}`);
    window.scrollTo({ top: 260, behavior: "smooth" });
  } catch (error) {
    ElMessage.error(error.message || "加载讲解提纲失败");
  }
};

const deleteOutline = async (item) => {
  try {
    await ElMessageBox.confirm(`确定删除提纲「${item.title}」吗？`, "确认删除", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
    await apiRequest(`/courses/${selectedCourse.value}/lesson-outlines/${item.outline_id}`, {
      method: "DELETE",
    });
    ElMessage.success("删除成功");
    if (currentOutlineId.value === item.outline_id) {
      outline.value = null;
      currentOutlineId.value = null;
    }
    await loadHistory();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error.message || "删除失败");
    }
  }
};

const formatDate = (value) => {
  if (!value) return "-";
  return new Date(value).toLocaleString();
};

watch(selectedCourse, () => {
  outline.value = null;
  currentOutlineId.value = null;
  knowledgeScope.value = [];
  loadKnowledgePoints();
  loadHistory();
});

onMounted(loadCourses);
</script>

<style scoped>
.outline-page {
  max-width: 1120px;
  margin: 0 auto;
}

.mt-4 {
  margin-top: 16px;
}

.outline-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 24px;
  align-items: start;
}

.outline-main {
  padding: 32px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr 0.8fr;
  gap: 16px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-soft);
}

.outline-result {
  margin-top: 32px;
  padding-top: 28px;
  border-top: 1px solid var(--color-border-soft);
}

.result-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 20px;
}

.result-toolbar h2 {
  margin: 4px 0 0;
  font-size: 24px;
  color: var(--color-text-main);
}

.section-kicker {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-muted);
  letter-spacing: 0.08em;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.summary-card {
  padding: 16px;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-sm);
  background: #f8fafc;
}

.summary-card span {
  display: block;
  font-size: 12px;
  color: var(--color-text-muted);
  margin-bottom: 6px;
}

.summary-card strong {
  color: var(--color-text-main);
}

.outline-section {
  padding: 20px;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-md);
  background: white;
  margin-bottom: 16px;
}

.outline-section h3 {
  margin: 0 0 14px;
  font-size: 16px;
  color: var(--color-text-main);
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-title-row h3 {
  margin: 0;
}

.two-column {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.clean-list {
  margin: 0;
  padding-left: 18px;
  color: var(--color-text-secondary);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.point-list {
  display: grid;
  gap: 8px;
}

.point-item {
  padding: 9px 12px;
  border-radius: 8px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  color: #0369a1;
  font-size: 13px;
  line-height: 1.55;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.point-list.warning .point-item {
  background: #fffbeb;
  border-color: #fde68a;
  color: #92400e;
}

.flow-list {
  display: grid;
  gap: 12px;
}

.flow-item {
  display: grid;
  grid-template-columns: 76px 1fr;
  gap: 14px;
  padding: 14px;
  border-radius: 12px;
  background: #f8fafc;
}

.flow-time {
  height: 34px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #111827;
  color: white;
  font-size: 12px;
  font-weight: 700;
}

.flow-title {
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 8px;
}

.flow-content p {
  margin: 4px 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.citation-meta {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

.citation-excerpt {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.empty-result {
  margin-top: 32px;
  padding: 56px 20px;
  text-align: center;
  border-radius: var(--radius-md);
  background: var(--color-bg-alt);
  color: var(--color-text-muted);
}

.empty-result h3 {
  color: var(--color-text-main);
  margin: 14px 0 8px;
}

.empty-result p {
  margin: 0 auto;
  max-width: 460px;
  line-height: 1.6;
}

.history-section {
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-soft);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.section-title {
  margin-top: 4px;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-main);
}

.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.history-title span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.info-list p {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

@media (max-width: 1000px) {
  .outline-layout,
  .two-column,
  .summary-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
