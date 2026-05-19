import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../views/Layout.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/requirement',
    children: [
      {
        path: 'requirement',
        name: 'RequirementSummary',
        component: () => import('../views/RequirementSummary.vue'),
        meta: { title: '需求汇总表' }
      },
      {
        path: 'project',
        name: 'ProjectList',
        component: () => import('../views/ProjectList.vue'),
        meta: { title: '项目配置表' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
