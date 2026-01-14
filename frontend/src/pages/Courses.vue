<template>
  <div class="courses-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">我的工作区</h1>
        <p class="page-subtitle">管理您的实训课程、知识库与 AI 智能体</p>
      </div>
      <div class="header-actions">
        <el-button
          v-if="isTeacher"
          type="primary"
          @click="$router.push('/courses/new')"
        >
          <Plus :size="16" style="margin-right: 8px" />
          创建课程
        </el-button>
      </div>
    </div>

    <div class="workspace-filters">
      <div class="search-bar">
        <Search :size="18" class="search-icon" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索课程、文档或知识点..."
          class="minimal-input"
        />
      </div>
      <div class="filter-tabs">
        <button 
          class="filter-tab" 
          :class="{ active: filterType === 'all' }"
          @click="filterType = 'all'"
        >
          全部课程
        </button>
        <button 
          v-if="session.user"
          class="filter-tab" 
          :class="{ active: filterType === 'my' }"
          @click="filterType = 'my'"
        >
          我创建的
        </button>
      </div>
    </div>

    <div v-loading="loading" class="bento-grid">
      <div v-if="filteredCourses.length === 0 && !loading" class="empty-state">
        <div class="empty-icon-box">
          <BookOpen :size="32" />
        </div>
        <h3>暂无课程</h3>
        <p>开始创建您的第一个实训课程，构建专属知识库。</p>
        <el-button v-if="isTeacher" type="primary" plain @click="$router.push('/courses/new')">
          立即创建
        </el-button>
      </div>
      
      <div
        v-for="course in filteredCourses"
        :key="course.id"
        class="bento-card"
        @click="viewDetails(course)"
      >
        <div class="card-top">
          <div class="course-icon-wrapper">
            <BookOpen :size="20" />
          </div>
          <div class="course-id-tag">{{ course.id.split('_')[1] || course.id }}</div>
        </div>
        
        <div class="card-body">
          <h3 class="course-title">{{ course.title }}</h3>
          <p class="course-desc">{{ course.description || '点击添加课程描述，完善您的教学计划' }}</p>
        </div>
        
        <div class="card-footer">
          <div class="meta-group">
            <div class="meta-avatar">{{ course.creator_id.charAt(0).toUpperCase() }}</div>
            <span class="meta-text">{{ course.creator_id }}</span>
          </div>
          <div class="meta-divider"></div>
          <span class="meta-date">{{ formatDate(course.created_at) }}</span>
        </div>
        
        <div class="card-action">
          <span>进入课程</span>
          <ArrowRight :size="14" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from "vue";
import { useRouter } from "vue-router";
import { apiRequest } from "../services/api";
import { sessionState } from "../stores/session";
import { 
  Plus, 
  Search, 
  BookOpen, 
  ArrowRight
} from "lucide-vue-next";
import { ElMessage } from "element-plus";

const router = useRouter();
const session = computed(() => sessionState.value);
const isTeacher = computed(() => session.value.user?.role === 'teacher');

const courses = ref([]);
const loading = ref(true);
const searchQuery = ref("");
const filterType = ref("all");

const loadCourses = async () => {
  loading.value = true;
  try {
    const data = await apiRequest("/courses");
    courses.value = data;
  } catch (err) {
    ElMessage.error(err.message || "加载课程失败");
  } finally {
    loading.value = false;
  }
};

const filteredCourses = computed(() => {
  let result = courses.value;
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(c => 
      c.title.toLowerCase().includes(query) || 
      (c.description && c.description.toLowerCase().includes(query))
    );
  }
  
  if (filterType.value === 'my' && session.value.user) {
    result = result.filter(c => c.creator_id === session.value.user.id);
  }
  
  return result;
});

const formatDate = (dateStr) => {
  if (!dateStr) return '未知时间';
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
};

const viewDetails = (course) => {
  ElMessage.info(`正在进入: ${course.title}`);
};

onMounted(loadCourses);
</script>

<style scoped>
.courses-page {
  max-width: 1100px;
  margin: 0 auto;
}

.workspace-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  gap: 24px;
}

.search-bar {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  background: white;
  border: 1px solid var(--color-border);
  padding: 0 16px;
  border-radius: 10px;
  height: 42px;
  transition: all 0.2s;
}

.search-bar:focus-within {
  border-color: var(--color-text-main);
  box-shadow: var(--shadow-sm);
}

.search-icon {
  color: var(--color-text-muted);
}

.minimal-input {
  border: none;
  background: transparent;
  width: 100%;
  font-size: 14px;
  color: var(--color-text-main);
  outline: none;
}

.filter-tabs {
  display: flex;
  background: var(--color-border-soft);
  padding: 4px;
  border-radius: 8px;
}

.filter-tab {
  border: none;
  background: transparent;
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.filter-tab.active {
  background: white;
  color: var(--color-text-main);
  box-shadow: var(--shadow-sm);
}

.bento-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  min-height: 300px;
}

.bento-card {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.bento-card:hover {
  border-color: var(--color-text-main);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.course-icon-wrapper {
  width: 40px;
  height: 40px;
  background-color: var(--color-border-soft);
  color: var(--color-text-main);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.course-id-tag {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
  background: var(--color-border-soft);
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
}

.card-body {
  flex: 1;
}

.course-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-main);
  margin: 0 0 10px 0;
  letter-spacing: -0.02em;
}

.course-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0 0 24px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-soft);
}

.meta-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-avatar {
  width: 20px;
  height: 20px;
  background-color: var(--color-primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
}

.meta-text {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.meta-divider {
  width: 4px;
  height: 4px;
  background-color: var(--color-border);
  border-radius: 50%;
  margin: 0 10px;
}

.meta-date {
  font-size: 12px;
  color: var(--color-text-muted);
}

.card-action {
  position: absolute;
  right: 24px;
  bottom: 24px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-main);
  opacity: 0;
  transform: translateX(10px);
  transition: all 0.2s;
}

.bento-card:hover .card-action {
  opacity: 1;
  transform: translateX(0);
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 20px;
}

.empty-icon-box {
  width: 64px;
  height: 64px;
  background-color: var(--color-border-soft);
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  margin: 0 auto 24px;
}

.empty-state h3 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--color-text-secondary);
  margin-bottom: 24px;
}
</style>
