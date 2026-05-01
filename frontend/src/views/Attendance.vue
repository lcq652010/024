<template>
  <div class="attendance-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>员工打卡</span>
        </div>
      </template>

      <div class="attendance-content">
        <el-form label-width="100px" style="max-width: 400px; margin: 0 auto;">
          <el-form-item label="选择员工">
            <el-select v-model="selectedEmployee" placeholder="请选择员工" style="width: 100%">
              <el-option
                v-for="emp in employees"
                :key="emp.id"
                :label="`${emp.name} - ${emp.department}`"
                :value="emp.id"
              />
            </el-select>
          </el-form-item>
        </el-form>

        <div class="clock-section">
          <div class="current-time">
            <div class="date">{{ currentDate }}</div>
            <div class="time">{{ currentTime }}</div>
          </div>

          <div class="check-buttons">
            <el-button
              type="success"
              size="large"
              :disabled="!selectedEmployee"
              :loading="checkInLoading"
              @click="handleCheckIn"
            >
              <el-icon><Plus /></el-icon>
              签到
            </el-button>
            <el-button
              type="primary"
              size="large"
              :disabled="!selectedEmployee"
              :loading="checkOutLoading"
              @click="handleCheckOut"
            >
              <el-icon><Minus /></el-icon>
              签退
            </el-button>
          </div>

          <div v-if="todayRecord" class="today-status">
            <el-divider>今日打卡状态</el-divider>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="签到时间">
                <span :class="todayRecord.check_in ? 'status-ok' : 'status-wait'">
                  {{ todayRecord.check_in || '未签到' }}
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="签退时间">
                <span :class="todayRecord.check_out ? 'status-ok' : 'status-wait'">
                  {{ todayRecord.check_out || '未签退' }}
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="状态" :span="2">
                <el-tag :type="getStatusType()">{{ getStatusText() }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Minus } from '@element-plus/icons-vue'
import request from '../utils/request'

const employees = ref([])
const selectedEmployee = ref(null)
const currentDate = ref('')
const currentTime = ref('')
const checkInLoading = ref(false)
const checkOutLoading = ref(false)
const todayRecord = ref(null)

let timer = null

const updateTime = () => {
  const now = new Date()
  currentDate.value = now.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
  currentTime.value = now.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const getEmployees = async () => {
  try {
    const res = await request.get('/employees')
    employees.value = res.data
  } catch (error) {
    ElMessage.error('获取员工列表失败')
  }
}

const getTodayRecord = async () => {
  if (!selectedEmployee.value) {
    todayRecord.value = null
    return
  }
  try {
    const today = new Date().toISOString().split('T')[0]
    const res = await request.get('/attendance/records', {
      params: {
        employee_id: selectedEmployee.value,
        start_date: today,
        end_date: today
      }
    })
    todayRecord.value = res.data[0] || null
  } catch (error) {
    ElMessage.error('获取今日打卡记录失败')
  }
}

const handleCheckIn = async () => {
  checkInLoading.value = true
  try {
    const res = await request.post('/attendance/checkin', {
      employee_id: selectedEmployee.value
    })
    if (res.data.success) {
      ElMessage.success(res.data.message)
      getTodayRecord()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '签到失败')
  } finally {
    checkInLoading.value = false
  }
}

const handleCheckOut = async () => {
  checkOutLoading.value = true
  try {
    const res = await request.post('/attendance/checkout', {
      employee_id: selectedEmployee.value
    })
    if (res.data.success) {
      ElMessage.success(res.data.message)
      getTodayRecord()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '签退失败')
  } finally {
    checkOutLoading.value = false
  }
}

const getStatusType = () => {
  if (!todayRecord.value) return 'info'
  if (todayRecord.value.check_in && todayRecord.value.check_out) return 'success'
  if (todayRecord.value.check_in) return 'warning'
  return 'info'
}

const getStatusText = () => {
  if (!todayRecord.value) return '未打卡'
  if (todayRecord.value.check_in && todayRecord.value.check_out) return '已完成'
  if (todayRecord.value.check_in) return '已签到，待签退'
  return '未打卡'
}

watch(selectedEmployee, () => {
  getTodayRecord()
})

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  getEmployees()
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.attendance-content {
  padding: 20px;
}

.clock-section {
  text-align: center;
  margin-top: 40px;
}

.current-time {
  margin-bottom: 40px;
}

.date {
  font-size: 18px;
  color: #606266;
  margin-bottom: 10px;
}

.time {
  font-size: 48px;
  font-weight: bold;
  color: #303133;
}

.check-buttons {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-bottom: 40px;
}

.check-buttons .el-button {
  min-width: 120px;
  height: 50px;
  font-size: 18px;
}

.today-status {
  max-width: 500px;
  margin: 0 auto;
}

.status-ok {
  color: #67c23a;
  font-weight: bold;
}

.status-wait {
  color: #909399;
}
</style>
