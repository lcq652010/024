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
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-value attendance">{{ individualStats.attendance_days }}</div>
              <div class="stat-label">出勤天数</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-value normal">{{ individualStats.normal_count }}</div>
              <div class="stat-label">正常天数</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-value late">{{ individualStats.late_count }}</div>
              <div class="stat-label">迟到天数</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-value early">{{ individualStats.early_count + individualStats.late_early_count }}</div>
              <div class="stat-label">早退天数</div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="20" style="margin-top: 20px">
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>考勤状态分布</span>
              </template>
              <div class="chart-container">
                <Pie :data="pieChartData" :options="pieChartOptions" />
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>统计详情</span>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="员工姓名">{{ individualStats.employee_name }}</el-descriptions-item>
                <el-descriptions-item label="统计月份">{{ `${individualStats.year}年${individualStats.month}月` }}</el-descriptions-item>
                <el-descriptions-item label="月总天数">{{ individualStats.total_days }} 天</el-descriptions-item>
                <el-descriptions-item label="出勤率">
                  <span class="rate">{{ ((individualStats.attendance_days / individualStats.total_days) * 100).toFixed(1) }}%</span>
                </el-descriptions-item>
                <el-descriptions-item label="迟到早退天数">{{ individualStats.late_early_count }} 天</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>当月考勤明细</span>
          </template>
          <el-table :data="individualStats.records" border stripe>
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
            <el-table-column prop="status" label="状态" width="120">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <div v-else-if="!searchForm.employee_id && overallStats" class="overall-stats">
        <el-card>
          <template #header>
            <span>全体员工考勤统计 - {{ `${overallStats.year}年${overallStats.month}月` }}</span>
          </template>
          <el-table :data="overallStats.stats" border stripe>
            <el-table-column prop="employee_id" label="员工ID" width="100" />
            <el-table-column prop="employee_name" label="员工姓名" width="120" />
            <el-table-column prop="department" label="部门" width="120" />
            <el-table-column prop="attendance_days" label="出勤天数" width="120">
              <template #default="scope">
                <span class="attendance-count">{{ scope.row.attendance_days }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="normal_count" label="正常" width="100">
              <template #default="scope">
                <el-tag type="success">{{ scope.row.normal_count }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="late_count" label="迟到" width="100">
              <template #default="scope">
                <el-tag type="warning">{{ scope.row.late_count }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="早退" width="100">
              <template #default="scope">
                <el-tag type="warning">{{ scope.row.early_count + scope.row.late_early_count }}</el-tag>
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
        </el-card>

        <el-row :gutter="20" style="margin-top: 20px">
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>出勤率分布</span>
              </template>
              <div class="chart-container">
                <Bar :data="barChartData" :options="barChartOptions" />
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>异常统计</span>
              </template>
              <div class="chart-container">
                <Doughnut :data="abnormalChartData" :options="doughnutChartOptions" />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <el-empty v-else description="暂无统计数据" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement
} from 'chart.js'
import { Pie, Bar, Doughnut } from 'vue-chartjs'
import request from '../utils/request'

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement
)

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

const pieChartData = computed(() => {
  if (!individualStats.value) return { labels: [], datasets: [] }
  return {
    labels: ['正常', '迟到', '早退', '迟到早退'],
    datasets: [{
      data: [
        individualStats.value.normal_count,
        individualStats.value.late_count,
        individualStats.value.early_count,
        individualStats.value.late_early_count
      ],
      backgroundColor: [
        '#67C23A',
        '#E6A23C',
        '#F56C6C',
        '#909399'
      ]
    }]
  }
})

const pieChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom'
    }
  }
}

const barChartData = computed(() => {
  if (!overallStats.value) return { labels: [], datasets: [] }
  return {
    labels: overallStats.value.stats.map(s => s.employee_name),
    datasets: [{
      label: '出勤天数',
      data: overallStats.value.stats.map(s => s.attendance_days),
      backgroundColor: '#409EFF'
    }]
  }
})

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true
    }
  }
}

const abnormalChartData = computed(() => {
  if (!overallStats.value) return { labels: [], datasets: [] }
  const totalLate = overallStats.value.stats.reduce((sum, s) => sum + s.late_count, 0)
  const totalEarly = overallStats.value.stats.reduce((sum, s) => sum + s.early_count, 0)
  const totalLateEarly = overallStats.value.stats.reduce((sum, s) => sum + s.late_early_count, 0)
  
  return {
    labels: ['迟到', '早退', '迟到早退'],
    datasets: [{
      data: [totalLate, totalEarly, totalLateEarly],
      backgroundColor: [
        '#E6A23C',
        '#F56C6C',
        '#909399'
      ]
    }]
  }
})

const doughnutChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom'
    }
  }
}

const getEmployees = async () => {
  try {
    const res = await request.get('/employees')
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

    const res = await request.get('/attendance/monthly-stats', { params })
    
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

const getStatusType = (status) => {
  switch (status) {
    case '正常':
      return 'success'
    case '迟到':
      return 'warning'
    case '早退':
      return 'warning'
    case '迟到早退':
      return 'danger'
    default:
      return 'info'
  }
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

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-value.attendance {
  color: #409EFF;
}

.stat-value.normal {
  color: #67C23A;
}

.stat-value.late {
  color: #E6A23C;
}

.stat-value.early {
  color: #F56C6C;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.chart-container {
  height: 300px;
}

.attendance-count {
  font-size: 16px;
  font-weight: bold;
  color: #409EFF;
}

.attendance-rate {
  font-size: 16px;
  font-weight: bold;
  color: #67C23A;
}

.rate {
  font-size: 18px;
  font-weight: bold;
  color: #67C23A;
}

.text-success {
  color: #67C23A;
}

.text-danger {
  color: #F56C6C;
}
</style>
