<template>
  <div class="admin-dashboard">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">系统管理后台</h1>
        <p class="page-subtitle">监控全站运行状态，管理用户权限与教学资源</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" plain>
          <RefreshCw :size="16" style="margin-right: 8px" />
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- Stats Overview -->
    <div class="stats-grid">
      <div class="stat-card card">
        <div class="stat-icon-box users">
          <UsersIcon :size="24" />
        </div>
        <div class="stat-info">
          <div class="stat-label">总用户数</div>
          <div class="stat-value">{{ stats.totalUsers }}</div>
          <div class="stat-trend positive">+12% Since last month</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon-box courses">
          <BookOpen :size="24" />
        </div>
        <div class="stat-info">
          <div class="stat-label">开设课程</div>
          <div class="stat-value">{{ stats.totalCourses }}</div>
          <div class="stat-trend positive">+5% Since last week</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon-box questions">
          <MessageSquare :size="24" />
        </div>
        <div class="stat-info">
          <div class="stat-label">AI 问答次数</div>
          <div class="stat-value">{{ stats.totalQuestions }}</div>
          <div class="stat-trend positive">+28% Since yesterday</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon-box exercises">
          <Layout :size="24" />
        </div>
        <div class="stat-info">
          <div class="stat-label">已生成练习</div>
          <div class="stat-value">{{ stats.totalExercises }}</div>
          <div class="stat-trend neutral">Stable</div>
        </div>
      </div>
    </div>

    <!-- Management Sections -->
    <div class="management-layout">
      <div class="main-panel card">
        <div class="panel-header">
          <h3 class="panel-title">用户管理</h3>
          <el-input 
            v-model="userSearch" 
            placeholder="搜索姓名或邮箱..." 
            style="width: 240px"
          >
            <template #prefix><Search :size="14" /></template>
          </el-input>
        </div>
        <el-table :data="users" style="width: 100%" class="custom-table">
          <el-table-column prop="name" label="姓名" width="180" />
          <el-table-column prop="email" label="邮箱" width="220" />
          <el-table-column prop="role" label="角色">
            <template #default="scope">
              <span class="badge" :class="scope.row.role === 'admin' ? 'badge-primary' : 'badge-success'">
                {{ scope.row.role === 'admin' ? '管理员' : scope.row.role === 'teacher' ? '教师' : '学生' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="注册时间" />
          <el-table-column label="操作" width="120">
            <template #default>
              <el-button link type="primary">编辑</el-button>
              <el-button link type="danger">禁用</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="side-panel">
        <div class="card log-panel">
          <h3 class="panel-title">系统日志</h3>
          <div class="log-list">
            <div v-for="(log, i) in logs" :key="i" class="log-item">
              <div class="log-dot" :class="log.type"></div>
              <div class="log-content">
                <div class="log-msg">{{ log.msg }}</div>
                <div class="log-time">{{ log.time }}</div>
              </div>
            </div>
          </div>
          <el-button link class="view-all-btn">查看全部日志</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from "vue";
import { 
  Users as UsersIcon, 
  BookOpen, 
  MessageSquare, 
  Layout, 
  RefreshCw,
  Search
} from "lucide-vue-next";
import { apiRequest } from "../services/api";
import { ElMessage } from "element-plus";

const stats = reactive({
  totalUsers: 42,
  totalCourses: 15,
  totalQuestions: 1240,
  totalExercises: 850
});

const userSearch = ref("");
const users = ref([
  { name: '张三', email: 'admin@edu.ai', role: 'admin', created_at: '2026-01-01' },
  { name: '李教授', email: 'pro_li@edu.ai', role: 'teacher', created_at: '2026-01-05' },
  { name: '王同学', email: 'stu_wang@edu.ai', role: 'student', created_at: '2026-01-10' },
]);

const logs = ref([
  { type: 'info', msg: 'System backup completed', time: '10 mins ago' },
  { type: 'success', msg: 'AI Model Qwen2.5 re-deployed', time: '1 hr ago' },
  { type: 'warning', msg: 'Database connection delay', time: '3 hrs ago' },
  { type: 'info', msg: 'User login: admin@edu.ai', time: '5 hrs ago' },
]);

const loadStats = async () => {
  // Real stats loading logic would go here
  // For now we use the reactive mock data
};

onMounted(loadStats);
</script>

<style scoped>
.admin-dashboard {
  max-width: 1300px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
}

.stat-icon-box {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon-box.users { background: #eff6ff; color: #3b82f6; }
.stat-icon-box.courses { background: #f0fdf4; color: #22c55e; }
.stat-icon-box.questions { background: #fdf2f8; color: #db2777; }
.stat-icon-box.exercises { background: #fff7ed; color: #f97316; }

.stat-label {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
}

.stat-trend {
  font-size: 11px;
  font-weight: 500;
  margin-top: 4px;
}

.stat-trend.positive { color: #10b981; }
.stat-trend.neutral { color: #94a3b8; }

.management-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.panel-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 20px;
}

.log-item {
  display: flex;
  gap: 12px;
}

.log-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.log-dot.info { background: #3b82f6; }
.log-dot.success { background: #10b981; }
.log-dot.warning { background: #f59e0b; }

.log-msg {
  font-size: 13px;
  color: #1e293b;
  font-weight: 500;
}

.log-time {
  font-size: 11px;
  color: #94a3b8;
}

.view-all-btn {
  margin-top: 24px;
  width: 100%;
}

.custom-table {
  --el-table-header-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
}

@media (max-width: 1200px) {
  .management-layout {
    grid-template-columns: 1fr;
  }
}
</style>
