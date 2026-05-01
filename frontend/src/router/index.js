import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Layout from '../views/Layout.vue'
import Employees from '../views/Employees.vue'
import Attendance from '../views/Attendance.vue'
import Records from '../views/Records.vue'
import Statistics from '../views/Statistics.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    component: Layout,
    redirect: '/employees',
    children: [
      {
        path: 'employees',
        name: 'Employees',
        component: Employees,
        meta: { title: '员工管理' }
      },
      {
        path: 'attendance',
        name: 'Attendance',
        component: Attendance,
        meta: { title: '员工打卡' }
      },
      {
        path: 'records',
        name: 'Records',
        component: Records,
        meta: { title: '考勤记录' }
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: Statistics,
        meta: { title: '考勤统计' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const admin = localStorage.getItem('admin')
  const isLoggedIn = token && admin
  
  if (to.path !== '/login' && !isLoggedIn) {
    localStorage.removeItem('token')
    localStorage.removeItem('admin')
    next('/login')
  } else if (to.path === '/login' && isLoggedIn) {
    next('/employees')
  } else {
    next()
  }
})

export default router
