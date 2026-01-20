<template>
  <div v-if="!isLoginPage" class="layout-container">
    <!-- Sidebar -->
    <aside class="sidebar">
      <!-- Workspace Switcher (The Attio Way) -->
      <div class="workspace-section">
        <el-popover
          placement="bottom-start"
          :width="240"
          trigger="click"
          popper-class="workspace-popover"
        >
          <template #reference>
            <div class="workspace-switcher" :class="{ loading: switching }">
              <div class="workspace-icon">
                <component :is="activeWorkspace.icon" :size="18" />
              </div>
              <div class="workspace-info">
                <div class="workspace-name">{{ activeWorkspace.name }}</div>
                <div class="workspace-type">点击切换工作区</div>
              </div>
              <ChevronsUpDown :size="14" class="up-down-icon" />
            </div>
          </template>
          
          <div class="workspace-list">
            <div class="popover-label">可用视角 (同步后端身份)</div>
            <div 
              v-for="ws in workspaces" 
              :key="ws.id"
              class="workspace-item"
              :class="{ active: session.user?.role === ws.id }"
              @click="syncAndSwitchRole(ws.id)"
            >
              <div class="ws-item-icon" :class="ws.id">
                <component :is="ws.icon" :size="16" />
              </div>
              <div class="ws-item-text">
                <div class="ws-item-name">{{ ws.name }}</div>
                <div class="ws-item-desc">{{ ws.desc }}</div>
              </div>
              <Check v-if="session.user?.role === ws.id" :size="14" class="check-icon" />
            </div>
          </div>
        </el-popover>
      </div>
      
      <!-- Navigation Sections -->
      <div class="sidebar-scrollable">
        <div class="nav-section">
          <div class="nav-label">概览</div>
          <nav class="sidebar-nav">
            <RouterLink 
              v-if="session.user?.role === 'admin'" 
              to="/admin" 
              class="nav-item" 
              :class="{ active: currentPath === '/admin' }"
            >
              <ShieldCheck :size="18" />
              <span>全站仪表盘</span>
            </RouterLink>
            <RouterLink 
              to="/courses" 
              class="nav-item" 
              :class="{ active: currentPath === '/courses' && currentPath !== '/courses/new' }"
            >
              <LayoutGrid :size="18" />
              <span>{{ session.user?.role === 'student' ? '我的学习' : '实训课程' }}</span>
            </RouterLink>
            <RouterLink
              to="/qa"
              class="nav-item"
              :class="{ active: currentPath === '/qa' }"
            >
              <MessageSquare :size="18" />
              <span>RAG 问答</span>
            </RouterLink>
            <RouterLink
              to="/exercises/grade"
              class="nav-item"
              :class="{ active: currentPath === '/exercises/grade' }"
            >
              <CheckSquare :size="18" />
              <span>练习评测</span>
            </RouterLink>
          </nav>
        </div>

        <div v-if="session.user?.role === 'teacher' || session.user?.role === 'admin'" class="nav-section">
          <div class="nav-label">教学管理</div>
          <nav class="sidebar-nav">
            <RouterLink to="/courses/new" class="nav-item" :class="{ active: currentPath === '/courses/new' }">
              <PlusCircle :size="18" />
              <span>新建实训</span>
            </RouterLink>
            <RouterLink to="/knowledge-base" class="nav-item" :class="{ active: currentPath === '/knowledge-base' }">
              <UploadCloud :size="18" />
              <span>知识库上传</span>
            </RouterLink>
            <RouterLink to="/knowledge-base/search" class="nav-item" :class="{ active: currentPath === '/knowledge-base/search' }">
              <Search :size="18" />
              <span>知识库检索</span>
            </RouterLink>
            <RouterLink to="/exercises" class="nav-item" :class="{ active: currentPath === '/exercises' }">
              <ClipboardList :size="18" />
              <span>练习生成</span>
            </RouterLink>
          </nav>
        </div>
      </div>

      <div class="sidebar-spacer"></div>

      <div class="sidebar-footer">
        <el-popover
          placement="right-end"
          :width="220"
          trigger="click"
          popper-class="user-popover"
        >
          <template #reference>
            <div class="user-pill">
              <div class="user-avatar">{{ userInitial }}</div>
              <div class="user-info-text">
                <div class="user-name">{{ session.user?.name }}</div>
                <div class="user-email">{{ session.user?.email }}</div>
              </div>
              <MoreHorizontal :size="14" class="more-icon" />
            </div>
          </template>
          
          <div class="popover-content">
            <div class="popover-header">
              <div class="popover-user-name">{{ session.user?.name }}</div>
              <div class="popover-user-role">{{ roleName }}</div>
            </div>
            <div class="popover-divider"></div>
            <button class="popover-item logout" @click="handleLogout">
              <LogOut :size="16" />
              <span>退出登录</span>
            </button>
          </div>
        </el-popover>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="main-wrapper">
      <header class="global-header">
        <div class="header-left">
          <div class="breadcrumb-nav">
            <span class="bc-item">智能实训平台</span>
            <span class="bc-sep">/</span>
            <span class="bc-item active">{{ activeWorkspace.name }}</span>
          </div>
        </div>
        <div class="header-right">
          <div class="status-indicator">
            <div class="status-dot"></div>
            <span>系统在线</span>
          </div>
        </div>
      </header>

      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>

  <!-- Login Layout -->
  <div v-else class="login-layout">
    <router-view />
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRoute, useRouter, RouterLink, RouterView } from "vue-router";
import { sessionState, clearSession, setSession } from "./stores/session";
import { apiRequest } from "./services/api";
import { 
  BookOpen, 
  LayoutGrid, 
  PlusCircle, 
  LogOut,
  ShieldCheck,
  ChevronsUpDown,
  Check,
  MoreHorizontal,
  Plus, 
  UploadCloud,
  Search,
  MessageSquare,
  ClipboardList,
  CheckSquare
} from "lucide-vue-next";
import { ElMessage } from "element-plus";

const route = useRoute();
const router = useRouter();
const session = computed(() => sessionState.value);
const currentPath = computed(() => route.path);
const switching = ref(false);

const workspaces = [
  { id: 'admin', name: '全站控制台', desc: '管理员权限', icon: ShieldCheck },
  { id: 'teacher', name: '实训工作室', desc: '教师权限', icon: LayoutGrid },
  { id: 'student', name: '学习中心', desc: '学生权限', icon: BookOpen },
];

const activeWorkspace = computed(() => {
  return workspaces.find(w => w.id === session.value.user?.role) || workspaces[1];
});

const userInitial = computed(() => session.value.user?.name?.charAt(0) || 'U');

const roleName = computed(() => {
  const roles = { admin: '系统管理员', teacher: '实训教师', student: '学生用户' };
  return roles[session.value.user?.role] || '用户';
});

// Real Switch: Sync with Backend
const syncAndSwitchRole = async (role) => {
  if (session.value.user?.role === role) return;
  
  switching.value = true;
  try {
    const updatedUser = await apiRequest("/auth/me/role", {
      method: "PATCH",
      body: JSON.stringify({ role }),
    });
    
    // Update local state
    setSession(session.value.token, updatedUser);
    ElMessage.success(`视角已切换至: ${roleName.value}`);
    
    // Redirect
    if (role === 'admin') router.push('/admin');
    else router.push('/courses');
  } catch (error) {
    ElMessage.error("身份同步失败: " + error.message);
  } finally {
    switching.value = false;
  }
};

const handleLogout = () => {
  clearSession();
  router.push("/login");
};
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  background: white;
}

.workspace-section {
  padding: 24px 16px 16px;
}

.workspace-switcher {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: #f8fafc;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.workspace-switcher.loading {
  opacity: 0.6;
  pointer-events: none;
}

.workspace-switcher:hover {
  border-color: var(--color-text-main);
  background: white;
}

.workspace-icon {
  width: 32px;
  height: 32px;
  background: var(--color-text-main);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.workspace-info {
  flex: 1;
  min-width: 0;
}

.workspace-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-main);
  letter-spacing: -0.02em;
}

.workspace-type {
  font-size: 11px;
  color: var(--color-text-muted);
}

.sidebar-scrollable {
  flex: 1;
  padding: 12px 0;
}

.nav-section {
  padding: 0 16px;
  margin-bottom: 28px;
}

.nav-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-text-muted);
  letter-spacing: 0.1em;
  padding: 0 12px 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  color: var(--color-text-secondary);
  text-decoration: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.nav-item:hover {
  color: var(--color-text-main);
  background: var(--color-border-soft);
}

.nav-item.active {
  color: var(--color-text-main);
  background: var(--color-border-soft);
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--color-border-soft);
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 10px;
  cursor: pointer;
}

.user-pill:hover { background: var(--color-bg-alt); }

.user-avatar {
  width: 32px;
  height: 32px;
  background: #e2e8f0;
  color: var(--color-text-main);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.user-name { font-size: 13px; font-weight: 600; }
.user-email { font-size: 11px; color: var(--color-text-muted); }

/* Workspace Popover */
.workspace-list { padding: 4px; }
.workspace-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
}
.workspace-item:hover { background: var(--color-bg-alt); }
.workspace-item.active { background: var(--color-border-soft); }
.ws-item-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.ws-item-icon.admin { background: #fee2e2; color: #ef4444; }
.ws-item-icon.teacher { background: #dcfce7; color: #22c55e; }
.ws-item-icon.student { background: #dbeafe; color: #3b82f6; }
.ws-item-name { font-size: 13px; font-weight: 600; }
.ws-item-desc { font-size: 11px; color: var(--color-text-muted); }

/* Main Wrapper & Global Header */
.main-wrapper {
  flex: 1;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
}

.global-header {
  height: 64px;
  padding: 0 40px;
  background: white;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.breadcrumb-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.bc-item { color: var(--color-text-muted); }
.bc-item.active { color: var(--color-text-main); font-weight: 600; }
.bc-sep { color: var(--color-border); }

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.status-dot {
  width: 6px;
  height: 6px;
  background: #22c55e;
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.1);
}

.main-content {
  flex: 1;
  padding: 40px;
}
</style>
