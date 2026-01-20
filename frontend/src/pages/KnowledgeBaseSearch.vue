<template>
  <div class="knowledge-base-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/courses' }">工作区</el-breadcrumb-item>
        <el-breadcrumb-item>知识库检索</el-breadcrumb-item>
      </el-breadcrumb>
      <h1 class="page-title mt-4">知识库检索</h1>
      <p class="page-subtitle">在课程知识库中快速查找相关知识片段、来源文档与详细内容。</p>
    </div>

    <div class="search-layout">
      <div class="search-main card">
        <el-form label-position="top">
          <el-form-item label="选择课程范围">
            <el-select
              v-model="selectedCourse"
              placeholder="请选择课程进行检索"
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
          <el-form-item label="Top-K 结果数量">
            <el-select v-model="topK" placeholder="请选择返回结果数" style="width: 100%">
              <el-option v-for="option in topKOptions" :key="option" :label="option" :value="option" />
            </el-select>
          </el-form-item>

          <div class="search-row-container">
            <el-input
              v-model="searchQuery"
              placeholder="输入关键词、概念或问题进行检索..."
              @keyup.enter="searchKnowledgeBase"
              size="large"
            >
              <template #prefix>
                <Search :size="18" class="search-icon-prefix" />
              </template>
            </el-input>
            <el-button 
              type="primary" 
              :loading="searching" 
              @click="searchKnowledgeBase"
              size="large"
            >
              开始检索
            </el-button>
          </div>
        </el-form>

        <div v-if="searchResults.length" class="results-section">
          <div class="section-title">检索结果 ({{ searchResults.length }})</div>
          <el-table
            :data="searchResults"
            class="custom-table"
            style="width: 100%"
          >
            <el-table-column prop="title_path" label="片段位置" min-width="240" />
            <el-table-column prop="source_doc_name" label="来源文档" min-width="180" />
            <el-table-column label="评分" width="160">
              <template #default="scope">
                <div class="score-tags">
                  <el-tooltip content="向量相似度 (1-距离)" placement="top">
                    <el-tag size="small" type="info">
                      V: {{ ((1 - scope.row.score) * 100).toFixed(0) }}%
                    </el-tag>
                  </el-tooltip>
                  <el-tooltip
                    v-if="scope.row.bm25_score !== undefined && scope.row.bm25_score !== null"
                    content="BM25 相关性得分"
                    placement="top"
                  >
                    <el-tag size="small" type="warning">
                      B: {{ (scope.row.bm25_score * 100).toFixed(0) }}%
                    </el-tag>
                  </el-tooltip>
                  <el-tooltip
                    v-if="scope.row.hybrid_score !== undefined && scope.row.hybrid_score !== null"
                    content="混合排序综合得分"
                    placement="top"
                  >
                    <el-tag size="small" type="primary">
                      H: {{ (scope.row.hybrid_score * 100).toFixed(0) }}%
                    </el-tag>
                  </el-tooltip>
                  <el-tooltip v-if="scope.row.rerank_score !== undefined && scope.row.rerank_score !== null" content="Rerank 相关性得分" placement="top">
                    <el-tag
                      size="small"
                      :type="scope.row.rerank_score > 0.7 ? 'success' : 'warning'"
                    >
                      R: {{ (scope.row.rerank_score * 100).toFixed(0) }}%
                    </el-tag>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="content" label="内容摘要" min-width="300">
              <template #default="scope">
                <div class="result-content-preview">{{ scope.row.content }}</div>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <div v-else class="empty-results">
          <div class="empty-icon-box">
            <SearchIcon :size="32" />
          </div>
          <h3>{{ searchQuery ? "未找到匹配结果" : "开启知识检索" }}</h3>
          <p>{{ searchQuery ? "请尝试更换关键词或检查所选课程范围。" : "选择课程并输入关键词，系统将从向量库中为您匹配最相关的知识片段。" }}</p>
        </div>
      </div>

      <div class="search-sidebar">
        <div class="info-card">
          <div class="info-icon">
            <Layers :size="18" />
          </div>
          <h3 class="info-title">检索技巧</h3>
          <ul class="info-list">
            <li>
              <strong>关键词匹配</strong>
              <p>输入核心术语（如“主键”）可获得最直接的定义。</p>
            </li>
            <li>
              <strong>语义检索</strong>
              <p>支持自然语言提问，系统会根据语义寻找相关片段。</p>
            </li>
            <li>
              <strong>范围缩小</strong>
              <p>确保选择了正确的课程，以便在特定知识领域内查找。</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import { Search, Search as SearchIcon, Layers } from "lucide-vue-next";
import { apiRequest } from "../services/api";
import { ElMessage } from "element-plus";

const courses = ref([]);
const loadingCourses = ref(false);
const selectedCourse = ref("");
const searchQuery = ref("");
const topK = ref(8);
const topKOptions = [3, 5, 8, 10, 15];
const searchResults = ref([]);
const searching = ref(false);

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

const searchKnowledgeBase = async () => {
  if (!selectedCourse.value) {
    ElMessage.warning("请先选择课程范围");
    return;
  }
  if (!searchQuery.value.trim()) {
    ElMessage.warning("请输入检索关键词");
    return;
  }
  searching.value = true;
  try {
    const payload = await apiRequest(`/courses/${selectedCourse.value}/documents/search`, {
      method: "POST",
      body: JSON.stringify({ query: searchQuery.value, top_k: topK.value }),
    });
    searchResults.value = payload.results || [];
    if (searchResults.value.length === 0) {
      ElMessage.info("未找到相关知识片段");
    }
  } catch (error) {
    ElMessage.error(error.message || "检索失败");
  } finally {
    searching.value = false;
  }
};

onMounted(loadCourses);

watch(selectedCourse, () => {
  searchResults.value = [];
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

.search-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 24px;
  align-items: start;
}

.search-main {
  padding: 32px;
}

.search-row-container {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.search-icon-prefix {
  color: var(--color-text-muted);
}

.results-section {
  margin-top: 32px;
  padding-top: 32px;
  border-top: 1px solid var(--color-border-soft);
}

.section-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 20px;
}

.result-content-preview {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.score-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.empty-results {
  text-align: center;
  padding: 60px 20px;
  background: var(--color-bg-alt);
  border-radius: var(--radius-md);
  margin-top: 32px;
}

.empty-icon-box {
  width: 64px;
  height: 64px;
  background-color: white;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  margin: 0 auto 24px;
  border: 1px solid var(--color-border);
}

.empty-results h3 {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 8px;
}

.empty-results p {
  color: var(--color-text-secondary);
  font-size: 14px;
  max-width: 400px;
  margin: 0 auto;
}

.search-sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
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
  .search-layout {
    grid-template-columns: 1fr;
  }
}
</style>
