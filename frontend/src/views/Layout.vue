<template>
  <el-container>
    <el-aside width="200px" style="background-color: #304156">
      <div class="logo">员工考勤管理系统</div>
      <el-menu
        :default-active="activeMenu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
      >
        <el-menu-item index="/employees">
          <el-icon><User /></el-icon>
          <span>员工管理</span>
        </el-menu-item>
        <el-menu-item index="/attendance">
          <el-icon><Clock /></el-icon>
          <span>员工打卡</span>
        </el-menu-item>
        <el-menu-item index="/records">
          <el-icon><Document /></el-icon>
          <span>考勤记录</span>
        </el-menu-item>
        <el-menu-item index="/statistics">
          <el-icon><DataLine /></el-icon>
          <span>考勤统计</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="background-color: #fff; border-bottom: 1px solid #eee">
        <div class="header-right">
          <span class="user-info">当前用户: {{ admin?.username }}</span>
          <el-button type="text" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main style="background-color: #f5f7fa">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { User, Clock, Document, DataLine } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const admin = computed(() => {
  const adminStr = localStorage.getItem('admin')
  return adminStr ? JSON.parse(adminStr) : null
})

const activeMenu = computed(() => route.path)

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('admin')
  router.push('/login')
}
</script>

<style scoped>
.el-container {
  min-height: 100vh;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  border-bottom: 1px solid #1f2d3d;
}

.el-menu {
  border-right: none;
}

.header-right {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  height: 100%;
}

.user-info {
  margin-right: 20px;
  color: #606266;
}
</style>
