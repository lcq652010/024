<template>
  <div class="statistics-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>考勤统计</span>
          <el-button type="primary" @click="getStatistics">查询</el-button>
        </div>
      </template>

      <div class="search-section">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="员工">
            <el-select v-model="searchForm.employee_id" placeholder="全部员工" clearable style="width: 200px">
              <el-option
                v-for="emp in employees"
                :key="emp.id"
                :label="`${emp.name} - ${emp.department}`"
                :value="emp.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="年份">
            <el-select v-model="searchForm.year" style="width: 120px">
              <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="y" />
            </el-select>
          </el-form-item>
          <el-form-item label="月份">
            <el-select v-model="searchForm.month" style="width: 120px">
              <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <div v-if="searchForm.employee_id && individualStats" class="individual-stats">
        <el-descriptions title="个人考勤统计" :column="3" border>
          <el-descriptions-item label="员工姓名">{{ individualStats.employee_name }}</el-descriptions-item>
          <el-descriptions-item label="统计月份">{{ `${individualStats.year}年${individualStats.month}月` }}</el-descriptions-item>
          <el-descriptions-item label="月总天数">{{ individualStats.total_days }} 天</el-descriptions-item>
          <el-descriptions-item label="出勤天数">
            <span class="attendance-count">{{ individualStats.attendance_days }} 天</span>
          </el-descriptions-item>
          <el-descriptions-item label="出勤率">
            <span class="attendance-rate">{{ ((individualStats.attendance_days / individualStats.total_days) * 100).toFixed(1) }}%</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <h4>当月考勤明细</h4>
        <el-table :data="individualStats.records" border stripe style="margin-top: 15px">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="check_in" label="签到时间" width="120">
            <template #default="scope">
              <span :class="scope.row.check_in ? 'text-success' : 'text-danger'">
                {{ scope.row.check_in || '未签到' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="check_out" label="签退时间" width="120">
            <template #default="scope">
              <span :class="scope.row.check_out ? 'text-success' : 'text-danger'">
                {{ scope.row.check_out || '未签退' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row)">{{ getStatusText(scope.row) }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else-if="!searchForm.employee_id && overallStats" class="overall-stats">
        <el-descriptions title="全体员工考勤统计" :column="2" border>
          <el-descriptions-item label="统计月份">{{ `${overallStats.year}年${overallStats.month}月` }}</el-descriptions-item>
          <el-descriptions-item label="月总天数">{{ overallStats.total_days }} 天</el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <h4>各员工出勤情况</h4>
        <el-table :data="overallStats.stats" border stripe style="margin-top: 15px">
          <el-table-column prop="employee_id" label="员工ID" width="100" />
          <el-table-column prop="employee_name" label="员工姓名" width="150" />
          <el-table-column prop="attendance_days" label="出勤天数" width="120">
            <template #default="scope">
              <span class="attendance-count">{{ scope.row.attendance_days }} 天</span>
            </template>
          </el-table-column>
          <el-table-column label="出勤率" width="120">
            <template #default="scope">
              <span class="attendance-rate">{{ ((scope.row.attendance_days / overallStats.total_days) * 100).toFixed(1) }}%</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getOverallStatusType(scope.row.attendance_days, overallStats.total_days)">
                {{ getOverallStatusText(scope.row.attendance_days, overallStats.total_days) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-empty v-else description="暂无统计数据" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const employees = ref([])
const individualStats = ref(null)
const overallStats = ref(null)

const currentYear = new Date().getFullYear()
const yearOptions = computed(() => [currentYear, currentYear - 1, currentYear - 2])

const searchForm = reactive({
  employee_id: null,
  year: currentYear,
  month: new Date().getMonth() + 1
})

const getEmployees = async () => {
  try {
    const res = await axios.get('/api/employees')
    employees.value = res.data
  } catch (error) {
    ElMessage.error('获取员工列表失败')
  }
}

const getStatistics = async () => {
  try {
    const params = {
      year: searchForm.year,
      month: searchForm.month
    }
    if (searchForm.employee_id) {
      params.employee_id = searchForm.employee_id
    }

    const res = await axios.get('/api/attendance/monthly-stats', { params })
    
    if (searchForm.employee_id) {
      individualStats.value = res.data
      overallStats.value = null
    } else {
      overallStats.value = res.data
      individualStats.value = null
    }
  } catch (error) {
    ElMessage.error('获取统计数据失败')
  }
}

const getStatusType = (row) => {
  if (row.check_in && row.check_out) return 'success'
  if (row.check_in) return 'warning'
  return 'danger'
}

const getStatusText = (row) => {
  if (row.check_in && row.check_out) return '正常'
  if (row.check_in) return '已签到'
  return '异常'
}

const getOverallStatusType = (attendanceDays, totalDays) => {
  const rate = attendanceDays / totalDays
  if (rate >= 0.8) return 'success'
  if (rate >= 0.5) return 'warning'
  return 'danger'
}

const getOverallStatusText = (attendanceDays, totalDays) => {
  const rate = attendanceDays / totalDays
  if (rate >= 0.8) return '良好'
  if (rate >= 0.5) return '一般'
  return '需关注'
}

onMounted(() => {
  getEmployees()
  getStatistics()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-section {
  margin-bottom: 20px;
}

.attendance-count {
  font-size: 18px;
  font-weight: bold;
  color: #67c23a;
}

.attendance-rate {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}

h4 {
  margin-bottom: 10px;
  color: #303133;
}
</style>
