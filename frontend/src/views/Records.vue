<template>
  <div class="records-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>考勤记录</span>
          <el-button type="primary" @click="searchRecords">查询</el-button>
        </div>
      </template>

      <div class="quick-filters">
        <el-radio-group v-model="quickFilter" @change="handleQuickFilter">
          <el-radio-button label="today">今天</el-radio-button>
          <el-radio-button label="week">本周</el-radio-button>
          <el-radio-button label="month">本月</el-radio-button>
          <el-radio-button label="custom">自定义</el-radio-button>
        </el-radio-group>
      </div>

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
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 150px">
              <el-option label="正常" value="正常" />
              <el-option label="迟到" value="迟到" />
              <el-option label="早退" value="早退" />
              <el-option label="迟到早退" value="迟到早退" />
            </el-select>
          </el-form-item>
          <el-form-item label="开始日期">
            <el-date-picker
              v-model="searchForm.start_date"
              type="date"
              placeholder="选择开始日期"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          <el-form-item label="结束日期">
            <el-date-picker
              v-model="searchForm.end_date"
              type="date"
              placeholder="选择结束日期"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="employee_name" label="员工姓名" width="120" />
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="check_in" label="签到时间" width="120">
          <template #default="scope">
            <span :class="scope.row.check_in ? 'text-success' : 'text-danger'">
              {{ scope.row.check_in || '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="check_out" label="签退时间" width="120">
          <template #default="scope">
            <span :class="scope.row.check_out ? 'text-success' : 'text-danger'">
              {{ scope.row.check_out || '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-section" v-if="pagination.total > 0">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          :page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :current-page="pagination.page"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const employees = ref([])
const tableData = ref([])
const loading = ref(false)
const quickFilter = ref('month')

const pagination = reactive({
  total: 0,
  page: 1,
  page_size: 10,
  total_pages: 0
})

const searchForm = reactive({
  employee_id: null,
  start_date: '',
  end_date: '',
  status: ''
})

const getEmployees = async () => {
  try {
    const res = await request.get('/employees')
    employees.value = res.data
  } catch (error) {
    ElMessage.error('获取员工列表失败')
  }
}

const handleQuickFilter = (val) => {
  const today = new Date()
  
  switch (val) {
    case 'today':
      searchForm.start_date = formatDate(today)
      searchForm.end_date = formatDate(today)
      break
    case 'week':
      const weekStart = new Date(today)
      weekStart.setDate(today.getDate() - today.getDay() + 1)
      searchForm.start_date = formatDate(weekStart)
      searchForm.end_date = formatDate(today)
      break
    case 'month':
      const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
      searchForm.start_date = formatDate(monthStart)
      searchForm.end_date = formatDate(today)
      break
    case 'custom':
      break
  }
  pagination.page = 1
  searchRecords()
}

const formatDate = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const searchRecords = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (searchForm.employee_id) {
      params.employee_id = searchForm.employee_id
    }
    if (searchForm.start_date) {
      params.start_date = searchForm.start_date
    }
    if (searchForm.end_date) {
      params.end_date = searchForm.end_date
    }
    if (searchForm.status) {
      params.status = searchForm.status
    }

    const res = await request.get('/attendance/records', { params })
    tableData.value = res.data.data
    pagination.total = res.data.total
    pagination.page = res.data.page
    pagination.page_size = res.data.page_size
    pagination.total_pages = res.data.total_pages
  } catch (error) {
    ElMessage.error('获取考勤记录失败')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (val) => {
  pagination.page_size = val
  pagination.page = 1
  searchRecords()
}

const handleCurrentChange = (val) => {
  pagination.page = val
  searchRecords()
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

onMounted(() => {
  getEmployees()
  handleQuickFilter('month')
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quick-filters {
  margin-bottom: 15px;
}

.search-section {
  margin-bottom: 20px;
}

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}
</style>
