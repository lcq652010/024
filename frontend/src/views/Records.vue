<template>
  <div class="records-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>考勤记录</span>
          <el-button type="primary" @click="searchRecords">查询</el-button>
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

      <el-table :data="records" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="employee_name" label="员工姓名" width="120" />
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="check_in" label="签到时间" width="120">
          <template #default="scope">
            <span :class="scope.row.check_in ? 'text-success' : 'text-warning'">
              {{ scope.row.check_in || '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="check_out" label="签退时间" width="120">
          <template #default="scope">
            <span :class="scope.row.check_out ? 'text-success' : 'text-warning'">
              {{ scope.row.check_out || '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row)">{{ getStatusText(scope.row) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-section" v-if="records.length > 0">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="records.length"
          :page-size="10"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const employees = ref([])
const records = ref([])
const loading = ref(false)

const searchForm = reactive({
  employee_id: null,
  start_date: '',
  end_date: ''
})

const getEmployees = async () => {
  try {
    const res = await axios.get('/api/employees')
    employees.value = res.data
  } catch (error) {
    ElMessage.error('获取员工列表失败')
  }
}

const searchRecords = async () => {
  loading.value = true
  try {
    const params = {}
    if (searchForm.employee_id) {
      params.employee_id = searchForm.employee_id
    }
    if (searchForm.start_date) {
      params.start_date = searchForm.start_date
    }
    if (searchForm.end_date) {
      params.end_date = searchForm.end_date
    }

    const res = await axios.get('/api/attendance/records', { params })
    records.value = res.data
  } catch (error) {
    ElMessage.error('获取考勤记录失败')
  } finally {
    loading.value = false
  }
}

const getStatusType = (row) => {
  if (row.check_in && row.check_out) return 'success'
  if (row.check_in) return 'warning'
  return 'danger'
}

const getStatusText = (row) => {
  if (row.check_in && row.check_out) return '已完成'
  if (row.check_in) return '已签到'
  return '异常'
}

onMounted(() => {
  getEmployees()
  searchRecords()
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

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.text-success {
  color: #67c23a;
}

.text-warning {
  color: #e6a23c;
}
</style>
